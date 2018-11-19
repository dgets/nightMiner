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
        'core': True,
        'seek': True,
        'locate_ore': True,
        'perimeter_search': False,  # this will almost certainly be phased out
        'save_state': True,
        'pruning': False,
        'scuttle': True,
    }

    Enough_Ore_To_Spawn = 2000
    Initial_Scoot_Distance = 5
    Max_Chunk_Width = Initial_Scoot_Distance
    Max_Chunk_Height = Initial_Scoot_Distance
    # Max_Scuttle_Time = constants.MAX_TURNS - (Game.game_map.width * 2)
    # Max_Scuttle_Time = constants.MAX_TURNS - (40 * 2)  # until above works
    # NOTE: the above will need to have the # of living ships * 2 added to it,
    # so that they can all get in to dropoff and get out of each others way,
    # so long as we're only dealing with the one shipyard & no dropoffs


class Variables:
    """
    global variables
    """

    current_assignments = {}   # contains { id: ShipHistory }
    considered_destinations = []


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