"""
myglobals.py

Started on: 5nov18 (or well that's when I remembered at add this note,
anyway)

Holds debugging and other constant values
"""

import logging
import random
from enum import Enum

from hlt import Direction


class Const:
    """
    global constants
    """

    DEBUGGING = {
        'preprocessing': True,
        'core': True,
        'seek': False,
        'locate_ore': False,
        'perimeter_search': False,  # this will almost certainly be phased out
        'save_state': False,
        'pruning': False,
        'scuttle': True,
        'blockade': True,
    }

    FEATURES = {
        'mining': True,
        'offense_blockade': True,
    }

    Enough_Ore_To_Spawn = 2000
    Initial_Scoot_Distance = 5
    Max_Chunk_Width = Initial_Scoot_Distance
    Max_Chunk_Height = Initial_Scoot_Distance
    # Max_Scuttle_Time = constants.MAX_TURNS - (Game.game_map.width * 2)
    Enemy_Drops = []


class Variables:
    """
    global variables

    TODO: add barred_destinations consideration in order to prevent pawn forms
    """

    current_assignments = {}    # contains { id: ShipHistory }
    barred_destinations = []    # note that this is not fully implemented yet


class Missions(Enum):
    """
    global mission assignment categories
    """

    in_transit = 1
    mining = 2
    dropoff = 3
    get_distance = 4
    defense = 5
    offense = 6
    busy = 7
    scuttle = 8
    blockade = 9


class Misc:
    @staticmethod
    def loggit(debugging_type, log_level, log_message):
        """
        I've got to say, I'm getting pretty sick of having to type in the
        whole if myglobals.Const.DEBUGGING['blah']: and logging() bits every
        time that I need to throw something into the log.  While this method
        won't be suitable for logging based on multiple Const.DEBUGGING flags,
        most of the ones I'm using are based on a single flag, so this will
        make things a lot easier for adding more, code maintainability, etc.

        :param debugging_type: see Const.DEBUGGING flags ('any' also works)
        :param log_level: debug, info, and any are implemented so far
        :param log_message: message to throw into the log @ log_level
        :return:
        """

        if debugging_type == 'any' or Const.DEBUGGING[debugging_type]:
            if log_level == 'debug' or log_level == 'any':
                logging.debug(log_message)
            elif log_level == 'info' or log_level == 'any':
                logging.info(log_message)
            else:
                raise RuntimeError("Log level specified is not implemented in myglobals.Misc.loggit()")

        return

    @staticmethod
    def log_w_shid(debugging_type, log_level, id, log_message):
        if debugging_type == 'any' or Const.DEBUGGING[debugging_type]:
            if log_level == 'debug' or log_level == 'any':
                logging.debug(" - ship.id: " + str(id) + " " + log_message)
            elif log_level == 'info' or log_level == 'any':
                logging.info(" - ship.id: " + str(id) + " " + log_message)
            else:
                raise RuntimeError("Log level specified is not implemented in myglobals.Misc.log_w_shid()")

    @staticmethod
    def r_dir_choice():
        """
        Just returns one of the 4 cardinal directions at random(-ish); this is
        really just more of a wrapper to save typing than anything

        :return: Direction
        """

        return random.choice([Direction.North, Direction.South, Direction.East, Direction.West])

    @staticmethod
    def add_barred_destination(direction, ship):
        """
        Method adds another destination to the barred_destinations list.

        NOTE: renamed considered_destinations to barred_destinations

        :param direction:
        :param ship:
        :return:
        """

        Variables.barred_destinations.append(ship.position.directional_offset(direction))

        return

    @staticmethod
    def is_already_barred(direction, ship):
        """
        Determines whether or not the destination being considered has been
        decided upon by a previous ship in this turn already.

        :param direction:
        :param ship:
        :return: True if yes, etc
        """

        if ship.position.directional_offset(direction) in Variables.barred_destinations:
            return True
        else:
            return False
