"""
seek_n_nav.py

Started on: 6nov18 (or well that's when I remembered at add this note,
anyway)

routines for general seeking out of halite ore resources w/basic resource
location determination and navigation to it
"""


import random

from hlt import Position, Direction

from . import history, seek_n_nav
from . import myglobals as glo


class Nav:
    @staticmethod
    def generate_random_offset(current_position):
        """
        Generates a random position w/in glo.Const.Initial_Scoot_Distance
        of current_location, and returns it for navigation to a new location
        w/in that distance

        :param current_position: Position
        :return: new Position destination
        """

        x_offset = random.randint(-glo.Const.Initial_Scoot_Distance, glo.Const.Initial_Scoot_Distance)
        y_offset = random.randint(-glo.Const.Initial_Scoot_Distance, glo.Const.Initial_Scoot_Distance)

        return Position(current_position.x + x_offset, current_position.y + y_offset)

    @staticmethod
    def return_halite_to_shipyard(ship, me, game_map, turn):
        """
        Returns naive_navigate()'s instructions on how best to return to the
        initial shipyard

        :param ship:
        :param me:
        :param game_map:
        :param turn:
        :return:
        """
        glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) +
                              " **returning to shipyard** at " + str(me.shipyard.position))

        glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.dropoff
        glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
        glo.Variables.current_assignments[ship.id].destination = me.shipyard.position
        glo.Variables.current_assignments[ship.id].turnstamp = turn

        return ship.move(game_map.naive_navigate(ship, glo.Variables.current_assignments[ship.id].destination))

    @staticmethod
    def less_dumb_move(ship, direction, game_map):
        """
        Moves into the cell in the direction given, if not occupied, or else
        waits for a turn in order to avoid collision

        :param ship:
        :param direction:
        :param game_map:
        :return:
        """
        next_dest = game_map[ship.position.directional_offset(direction)]
        if next_dest.is_empty:
            glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " one step at a time...")
            #return ship.move(direction)
            return ship.move(game_map.naive_navigate(ship, next_dest.position))
        else:
            # I guess we'll just wait for now
            glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " avoiding collision at " +
                                  str(ship.position))
            return ship.stay_still()

    @staticmethod
    def scoot(ship, game_map):
        """
        In transit to a destination; just another step on the way.

        :param ship:
        :param game_map:
        :return:
        """
        glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **scooting** to " +
                              str(glo.Variables.current_assignments[ship.id].destination))

        return ship.move(game_map.naive_navigate(ship,
                                                 glo.Variables.current_assignments[ship.id].destination))


class StartUp:
    @staticmethod
    def get_initial_minimum_distance(ship, me, turn, key_exception):
        """
        Returns the command_queue data for the ship obtaining initial minimum
        distance in order to avoid clogging the shipyard access.

        :param ship:
        :param me:
        :param turn:
        :param key_exception:
        :return:
        """

        glo.Misc.loggit('core', 'debug', " - fell into except; **setting new ship id: " + str(ship.id) +
                                  " to mining**")
        glo.Misc.loggit('core', 'debug', " -* ke: " + str(key_exception))

        tmp_destination = seek_n_nav.Nav.generate_random_offset(ship.position)
        while tmp_destination == me.shipyard.position:
            tmp_destination = seek_n_nav.Nav.generate_random_offset(ship.position)

        glo.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                               tmp_destination, turn,
                                                                               glo.Missions.mining,
                                                                               glo.Missions.in_transit)

        return ship.move(random.choice([Direction.North, Direction.South, Direction.East, Direction.West]))
