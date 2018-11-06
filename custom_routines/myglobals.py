"""
myglobals.py

Started on: 5nov18 (or well that's when I remembered at add this note,
anyway)

Holds debugging and other constant values
"""

import logging
from enum import Enum


class Const:
    DEBUGGING = {
        'core': True,
        'seek': True,
        'locate_ore': True,
        'perimeter_search': True,
        'save_state': True,
    }

    Enough_Ore_To_Spawn = 2000


class Variables:
    current_assignments = { }


class Missions(Enum):
    in_transit = 1
    mining = 2
    dropoff = 3
    get_distance = 4
    defense = 5
    offense = 6


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