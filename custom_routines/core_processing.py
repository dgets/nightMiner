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

from . import seek_n_nav, mining, analytics
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

        analytics.Offense.scan_for_enemy_shipyards(game)

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
                game_map[ship.position].halite_amount > 0 and not ship.is_full:
                # game_map[ship.position].halite_amount > 0 and ship.halite_amount < constants.MAX_HALITE:
            return mining.Mine.done_with_transit_now_mine(ship, turn)

        # transit back to the shipyard
        elif ship.halite_amount >= 900 and ship.position != me.shipyard.position:
            # ship.position != glo.Variables.current_assignments[ship.id].destination:
            # head to drop off the halite
            glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " in **transit to drop**")
            glo.Variables.current_assignments[ship.id].set_ldps(ship.position, me.shipyard.position,
                                                                glo.Missions.dropoff, glo.Missions.in_transit)
            return seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map, turn)

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

        # not sure what happened just yet; enter the WTF clause
        else:
            return mining.CoreSupport.wtf_happened(ship, game_map, turn)
