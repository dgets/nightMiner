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

from hlt import Direction

from . import myglobals, seek_n_nav


class Core:
    """
    Here lies the Core that is not within the 'core'.
    """

    @staticmethod
    def original_preprocessing():
        """
        Computationally expensive and/or other preprocessing that nees to be
        taken care of before the primary per-turn loop.

        :return: game (a local version of hlt.Game()'s return)
        """

        # really good place to do computationally expensive preprocessing *cough*
        game = hlt.Game()
        game.ready("nightMiner")

        myglobals.Misc.loggit('any', 'info', "Hatched and swimming! Player ID is {}.".format(game.my_id))

        return game

    @staticmethod
    def per_turn_preprocessing(game, me):
        """
        Computationally expensive and/or other preprocessing taken care of at
        the start of each turn in the primary game loop.

        :param game:
        :return:
        """

        myglobals.Misc.loggit('core', 'info', " - updating frame")
        game.update_frame()

        myglobals.Misc.loggit('core', 'debug', " -* me.get_ships() dump: " + str(me.get_ships()))

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

        # we've mined all of the halite, or someone else got to it
        # before we did here, bounce a random square
        if ship.halite_amount < 900 and game_map[ship.position].halite_amount == 0:
            myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **randomly wandering**")
            rnd_dir = random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
            myglobals.Variables.current_assignments[ship.id].destination = \
                ship.position.directional_offset(rnd_dir)
            myglobals.Variables.current_assignments[ship.id].secondary_mission = myglobals.Missions.in_transit
            myglobals.Variables.current_assignments[ship.id].turnstamp = turn

            return seek_n_nav.Nav.less_dumb_move(ship, myglobals.Misc.r_dir_choice(), game_map)

        # continuing transit for this ship to its final destination
        elif myglobals.Variables.current_assignments[ship.id].secondary_mission == \
                myglobals.Missions.in_transit \
                and game_map.normalize(myglobals.Variables.current_assignments[ship.id].destination) != \
                ship.position:
            myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **scooting** to " +
                                  str(myglobals.Variables.current_assignments[ship.id].destination))

            return ship.move(game_map.naive_navigate(ship,
                                                     myglobals.Variables.current_assignments[ship.id].destination))

        # we've fully transited and are in the spot where we wanted to mine
        elif myglobals.Variables.current_assignments[ship.id].secondary_mission == \
                myglobals.Missions.in_transit:
            myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **mining** at " +
                                  str(ship.position))
            myglobals.Variables.current_assignments[ship.id].secondary_mission = myglobals.Missions.busy
            myglobals.Variables.current_assignments[ship.id].turnstamp = turn

            return ship.stay_still()

        # transit back to the shipyard
        elif (ship.is_full or (ship.halite_amount >= 900 and game_map[ship.position].halite_amount == 0)) and \
                ship.position != me.shipyard.position:
            # ship.position != myglobals.Variables.current_assignments[ship.id].destination:
            # head to drop off the halite
            myglobals.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " in **transit to dropo**")

            return seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map, turn)

        elif (ship.is_full or (ship.halite_amount >= 900 and game_map[ship.position].halite_amount == 0)) and \
                ship.position == myglobals.Variables.current_assignments[ship.id].destination:
            # not sure why we're still in this loop, but drop off the goddamned halite
            myglobals.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **making drop** " +
                                  "from within the **mining** loop for some reason")

            return None     # we'll test for it to see if shid needs to die

        # not sure what happened just yet
        else:
            myglobals.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **WTF**")

            return ship.stay_still()
