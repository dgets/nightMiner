"""
mining.py

started 9nov18

Mining algorithm internals.
"""
import random

from . import seek_n_nav
from . import myglobals as glo

from hlt import Direction


class Mine:
    """
    Mining internals.
    """

    @staticmethod
    def low_cargo_and_no_immediate_halite(ship, game_map, turn):
        """
        We've mined all of the halite, or someone else got to it
        before we did here, bounce a random square.

        :param ship:
        :param game_map:
        :param turn:
        :return: seek_n_nav.Nav.less_dumb_move() command
        """

        glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **randomly wandering**")
        rnd_dir = random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
        glo.Variables.current_assignments[ship.id].destination = \
            ship.position.directional_offset(rnd_dir)
        glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
        glo.Variables.current_assignments[ship.id].turnstamp = turn

        return seek_n_nav.Nav.less_dumb_move(ship, glo.Misc.r_dir_choice(), game_map)

    @staticmethod
    def done_with_transit_now_mine(ship, turn):
        """
        We're there, time to get to work.

        :param ship:
        :param turn:
        :return: stay_still()
        """
        glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **mining** at " +
                              str(ship.position))
        glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.busy
        glo.Variables.current_assignments[ship.id].turnstamp = turn

        return ship.stay_still()
