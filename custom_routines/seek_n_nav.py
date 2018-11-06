"""
seek_n_nav.py

Started on: 6nov18 (or well that's when I remembered at add this note,
anyway)

routines for general seeking out of halite ore resources w/basic resource
location determination and navigation to it
"""

from random import randint

from hlt import Position

from . import myglobals


class Nav:
    @staticmethod
    def generate_random_offset(current_position):
        """
        Generates a random position w/in myglobals.Const.Initial_Scoot_Distance
        of current_location, and returns it for navigation to a new location
        w/in that distance

        :param current_position: Position
        :return: new Position destination
        """

        x_offset = randint(-myglobals.Const.Initial_Scoot_Distance, myglobals.Const.Initial_Scoot_Distance)
        y_offset = randint(-myglobals.Const.Initial_Scoot_Distance, myglobals.Const.Initial_Scoot_Distance)

        return Position(current_position.x + x_offset, current_position.y + y_offset)
