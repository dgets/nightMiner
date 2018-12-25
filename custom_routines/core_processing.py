"""
core_processing.py

started 9nov18

This will hold the different bits of nightMiner.py that are going to be better
off pulled out of the main 'core' routine in order to be more modular for
debugging and maintainability purposes.  Try to remember to keep anything that
is specifically for mining or halite dropoff in a mining specific file or,
perhaps, seek_n_nav.py.
"""

import random

import hlt
from hlt import constants, Direction, Position

from . import seek_n_nav, mining, history, analytics
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

        if glo.Const.FEATURES['blockade'] or glo.Const.FEATURES['early_blockade']:
            analytics.Offense.scan_for_enemy_shipyards(game)

        return game

    @staticmethod
    def per_turn_preprocessing(game, me, turn):
        """
        Computationally expensive and/or other preprocessing taken care of at
        the start of each turn in the primary game loop.

        :param game:
        :param me:
        :param ship:
        :param game_map:
        :param turn:
        :return:
        """

        glo.Misc.loggit('core', 'info', " - updating frame")
        game.update_frame()

        glo.Misc.loggit('core', 'debug', " -* me.get_ships() dump: " + str(me.get_ships()))

        if glo.Const.FEATURES['early_blockade'] and not glo.Variables.early_blockade_processing:
            # let's see if we need to be doing an early blockade here
            if analytics.Offense.can_we_early_blockade(game):
                glo.Variables.early_blockade_processing = True
                analytics.Offense.init_early_blockade(me, game, turn)

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

        # we've mined all of the halite, bounce a random square
        if ship.halite_amount < constants.MAX_HALITE and \
                glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.mining and \
                glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.busy and \
                game_map[ship.position].halite_amount == 0:

            return mining.Mine.low_cargo_and_no_immediate_halite(ship, game_map, turn)

        # we've fully transited and are in the spot where we wanted to mine
        elif (glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.in_transit or
                glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.busy) and \
                glo.Variables.current_assignments[ship.id].destination == ship.position and \
                game_map[ship.position].halite_amount > 0 and ship.halite_amount < constants.MAX_HALITE:

            return mining.Mine.done_with_transit_now_mine(ship, turn)

        # transit back to the shipyard
        elif ship.halite_amount >= 900 and ship.position != me.shipyard.position:
            # ship.position != glo.Variables.current_assignments[ship.id].destination:
            # head to drop off the halite
            glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " in **transit to drop**")
            glo.Variables.current_assignments[ship.id].set_ldps(ship.position, me.shipyard.position,
                                                                glo.Missions.dropoff, glo.Missions.in_transit)

            return seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map, turn)

        elif (ship.is_full or ship.halite_amount >= 900) and game_map[ship.position].halite_amount == 0:
            # not sure why we're still in this loop, but drop off the goddamned halite
            glo.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **making drop** " +
                            "from within the **mining** loop for some reason")
            # now, obviously, we need to obtain minimum distance again and go back about our rounds

            return ship.move(seek_n_nav.StartUp.get_initial_minimum_distance(ship, me, game_map, turn))
            # return ship.stay_still()

        # continuing transit for this ship to its final destination
        elif glo.Variables.current_assignments[ship.id].secondary_mission == glo.Missions.in_transit and \
                glo.Variables.current_assignments[ship.id].turnstamp <= (turn + glo.Const.Initial_Scoot_Distance * 2) \
                and glo.Variables.current_assignments[ship.id].destination != ship.position:
            return seek_n_nav.Nav.scoot(ship, game_map)

        # get off the pot when you're done shitting, por dios
        elif ship.position == me.shipyard.position and ship.halite_amount == 0:
            c_queue_addition = ship.move(seek_n_nav.StartUp.get_initial_minimum_distance(ship, me, game_map, turn))
            glo.Misc.log_w_shid('core', 'debug', ship.id, " - get_initial_minimum_distance() returning: " +
                                str(c_queue_addition))

            return c_queue_addition

        # not sure what happened just yet
        else:
            profit_dir = seek_n_nav.Nav.generate_profitable_offset(ship, game_map)
            glo.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **WTF**  ship history dump: " +
                            str(glo.Variables.current_assignments[ship.id]) + "; full ship dump: " +
                            str(ship))
            glo.Variables.current_assignments[ship.id].set_ldps(ship.position,
                                                                ship.position.directional_offset(profit_dir),
                                                                glo.Missions.mining, glo.Missions.in_transit)
            glo.Variables.current_assignments[ship.id].turnstamp = turn

            # return ship.stay_still()
            if ship.halite_amount < constants.MAX_HALITE and game_map[ship.position].halite_amount > 0:
                return ship.stay_still()
            else:
                return ship.move(profit_dir)

    @staticmethod
    def scuttle_for_finish(me, game_map, turn):
        # NOTE: this routine will not work in conjunction with the other
        # normal ship in me.get_ships() game routine; command_queue will
        # get double orders for each ship if this happens.  It must be
        # one or the other
        c_queue = []

        new_kill_list_additions = history.ShipHistory.prune_current_assignments(me)
        glo.Misc.loggit('core', 'debug', "Killing from history due to ship 8-x: " + str(new_kill_list_additions))
        if new_kill_list_additions is not None:
            for shid in new_kill_list_additions:
                # wipe away the dingleberries
                glo.Misc.loggit('core', 'debug', "Killing history of shid: " + str(shid))
                glo.Variables.current_assignments.pop(shid, None)

        for ship in me.get_ships():
            if glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.get_distance:
                glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " getting away from shipyard to " +
                                glo.Variables.current_assignments[ship.id].destination)

                c_queue.append(ship.move(game_map.naive_navigate(ship,
                                                                 glo.Variables.current_assignments[ship.id].
                                                                 destination)))

            # elif ship.position == me.shipyard.position and \
            #         ship.halite_amount <= constants.MAX_HALITE - 100:
            elif ship.halite_amount <= 350:
                # glo.Variables.current_assignments[ship.id].primary_mission != glo.Missions.get_distance:

                # get away from the drop
                # glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " setting get_distance from " +
                #                       "shipyard")
                # glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.get_distance

                # go blockade
                c_queue.append(seek_n_nav.Offense.blockade_enemy_drops(ship, game_map))

                glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.blockade
                glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
                glo.Variables.current_assignments[ship.id].turnstamp = turn

                # tmp_destination = seek_n_nav.Nav.generate_profitable_offset(ship, game_map)
                # while ship.position.directional_offset(tmp_destination) == me.shipyard.position:
                #     tmp_destination = seek_n_nav.Nav.profitable_profitable_offset(ship.position, game_map)
                # glo.Variables.current_assignments[ship.id].destination = \
                #     ship.position.directional_offset(tmp_destination)

                # c_queue.append(ship.move(game_map.naive_navigate(ship,
                #                                                  glo.Variables.current_assignments[ship.id].
                #                                                  destination)))

                # c_queue.append(ship.move(game_map.naive_navigate(ship, Position(0, 0))))

                # if (turn % 2) == 1:
                #     c_queue.append(ship.move(Direction.North))
                # else:
                #     c_queue.append(ship.move(Direction.East))

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
