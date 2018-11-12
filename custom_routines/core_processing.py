"""
core_processing.py

started 9nov18

This will hold the different bits of nightMiner.py that are going to be better
off pulled out of the main 'core' routine in order to be more modular for
debugging and maintainability purposes.  Try to remember to keep anything that
is specifically for mining or halite dropoff in a mining specific file or,
perhaps, seek_n_nav.py.
"""

import hlt

from . import seek_n_nav, mining
from . import myglobals as glo

class Core:
    """
    Here lies the Core that is not within the 'core'.
    """

    @staticmethod
    def original_preprocessing():
        """
        Computationally expensive and/or other preprocessing that needs to be
        taken care of before the primary per-turn loop.

        :return: game (a local version of hlt.Game()'s return)
        """

        # really good place to do computationally expensive preprocessing *cough*
        game = hlt.Game()
        game.ready("nightMiner")

        glo.Misc.loggit('any', 'info', "Hatched and swimming! Player ID is {}.".format(game.my_id))

        return game

    @staticmethod
    def per_turn_preprocessing(game, me):
        """
        Computationally expensive and/or other preprocessing taken care of at
        the start of each turn in the primary game loop.

        :param game:
        :param me:
        :return:
        """

        glo.Misc.loggit('core', 'info', " - updating frame")
        game.update_frame()

        glo.Misc.loggit('core', 'debug', " -* me.get_ships() dump: " + str(me.get_ships()))

    @staticmethod
    def primary_mission_mining(ship, game_map, me, turn):
        """
        If the primary mission is mining, the algorithm is in here; it will have
        to be further subdivided from here, however.  This is just the top level
        of the core conditional.

        :param ship:
        :param game_map:
        :param me:
        :param turn:
        :return: command_queue addition
        """

        # maybe if things end up taking too long for processing at some point
        # we can add a conditional here to see if it's out of bounds before
        # invoking game_map.normalize() here; not sure how much of a diff it'd
        # really make
        glo.Variables.current_assignments[ship.id].destination = game_map.normalize(
            glo.Variables.current_assignments[ship.id].destination
        )

        # we've mined all of the halite, or someone else got to it
        # before we did here, bounce a random square
        if ship.halite_amount < 900 and \
                glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.mining and \
                game_map[ship.position].halite_amount == 0:
            return mining.Mine.low_cargo_and_no_immediate_halite(ship, game_map, turn)

        # continuing transit for this ship to its final destination
        elif glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.in_transit \
                and glo.Variables.current_assignments[ship.id].destination != ship.position:
            return seek_n_nav.Nav.scoot(ship, game_map)

        # we've fully transited and are in the spot where we wanted to mine
        elif glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.in_transit or \
                glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.busy:
            return mining.Mine.done_with_transit_now_mine(ship, turn)

        # transit back to the shipyard
        elif (ship.is_full or ship.halite_amount >= 900) and game_map[ship.position].halite_amount == 0 and \
                ship.position != me.shipyard.position:
            # ship.position != glo.Variables.current_assignments[ship.id].destination:
            # head to drop off the halite
            glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " in **transit to drop**")
            return seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map, turn)

        elif (ship.is_full or ship.halite_amount >= 900) and game_map[ship.position].halite_amount == 0:
            # not sure why we're still in this loop, but drop off the goddamned halite
            glo.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **making drop** " +
                            "from within the **mining** loop for some reason")
            return ship.stay_still()

        # not sure what happened just yet
        else:
            glo.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **WTF**  ship history dump: " +
                                  str(glo.Variables.current_assignments[ship.id]) + "; full ship dump: " +
                                  str(ship))
            glo.Variables.current_assignments[ship.id].set_ldps(ship.position,
                                                                seek_n_nav.Nav.
                                                                generate_profitable_offset(ship, game_map),
                                                                glo.Missions.mining, glo.Missions.in_transit)
            glo.Variables.current_assignments[ship.id].turnstamp = turn
            return ship.stay_still()

    @staticmethod
    def scuttle_for_finish(me, game_map, turn):
        # NOTE: this routine will not work in conjunction with the other
        # normal ship in me.get_ships() game routine; command_queue will
        # get double orders for each ship if this happens.  It must be
        # one or the other
        c_queue = []

        for ship in me.get_ships():
            if glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.get_distance:
                glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " getting away from shipyard")
                c_queue.append(ship.move(game_map.naive_navigate(ship,
                                                                 glo.Variables.current_assignments[ship.id].
                                                                 destination)))

            elif ship.position == me.shipyard.position and \
                    glo.Variables.current_assignments[ship.id].primary_mission != glo.Missions.get_distance:
                # get away from the drop
                glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " setting get_distance from " +
                                      "shipyard")
                glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.get_distance
                glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
                glo.Variables.current_assignments[ship.id].turnstamp = turn

                tmp_destination = seek_n_nav.Nav.generate_profitable_offset(ship, game_map)
                while tmp_destination == me.shipyard.position:
                    tmp_destination = seek_n_nav.Nav.profitable_profitable_offset(ship.position, game_map)
                glo.Variables.current_assignments[ship.id].destination = tmp_destination

                c_queue.append(ship.move(game_map.naive_navigate(ship,
                                                                 glo.Variables.current_assignments[ship.id].
                                                                 destination)))
            elif glo.Variables.current_assignments[ship.id].primary_mission != glo.Missions.scuttle:
                glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " heading back to drop")
                # head back to the drop, it's scuttle time
                glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.scuttle
                glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
                glo.Variables.current_assignments[ship.id].turnstamp = turn
                glo.Variables.current_assignments[ship.id].destination = me.shipyard.position

                c_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))
            else:
                # already scuttling, keep it up
                glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " en route back to drop")
                c_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))

            # after we try this with naive_navigate we'll give it a shot with
            # an implementation using seek_n_nav's less_dumb_move(), as well

        return c_queue
