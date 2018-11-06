"""
seek_n_nav.py

Started on: 6nov18 (or well that's when I remembered at add this note,
anyway)

routines for general seeking out of halite ore resources w/basic resource
location determination and navigation to it
"""


import random

from hlt import Position, Direction

from . import myglobals, history, seek_n_nav


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

        x_offset = random.randint(-myglobals.Const.Initial_Scoot_Distance, myglobals.Const.Initial_Scoot_Distance)
        y_offset = random.randint(-myglobals.Const.Initial_Scoot_Distance, myglobals.Const.Initial_Scoot_Distance)

        return Position(current_position.x + x_offset, current_position.y + y_offset)

    @staticmethod
    def return_halite_to_shipyard(ship, me, game_map):
        myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) +
                              " **returning to shipyard** at " + str(me.shipyard.position))
        if myglobals.Variables.current_assignments[ship.id].primary_mission != myglobals.Missions.dropoff:
            myglobals.Variables.current_assignments[ship.id].primary_mission = myglobals.Missions.dropoff
            myglobals.Variables.current_assignments[ship.id].secondary_mission = None
            myglobals.Variables.current_assignments[ship.id].destination = me.shipyard.position

        return ship.move(game_map.naive_navigate(ship, me.shipyard.position))


class StartUp:
    @staticmethod
    def get_initial_minimum_distance(ship, turn, key_exception):
        """
        Returns the command_queue data for the ship obtaining initial minimum
        distance in order to avoid clogging the shipyard access.

        :param ship:
        :param turn:
        :param key_exception:
        :return:
        """

        myglobals.Misc.loggit('core', 'debug', " - fell into except; **setting new ship id: " + str(ship.id) +
                                  " to mining**")
        myglobals.Misc.loggit('core', 'debug', " -* ke: " + str(key_exception))

        myglobals.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                               seek_n_nav.Nav.
                                                                               generate_random_offset(
                                                                                   ship.position
                                                                               ), turn,
                                                                               myglobals.Missions.mining,
                                                                               myglobals.Missions.in_transit)

        return ship.move(random.choice([Direction.North, Direction.South, Direction.East, Direction.West]))
