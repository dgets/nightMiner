"""
seek_n_nav.py

Started on: 6nov18 (or well that's when I remembered at add this note,
anyway)

routines for general seeking out of halite ore resources w/basic resource
location determination and navigation to it
"""


import random

from hlt import Direction, Position

from . import history, analytics
from . import myglobals as glo


class Nav:
    # @staticmethod
    # def generate_random_offset(current_position):
    #     """
    #     Generates a random position w/in glo.Const.Initial_Scoot_Distance
    #     of current_location, and returns it for navigation to a new location
    #     w/in that distance
    #
    #     TODO: Get collision detection here
    #
    #     :param current_position: Position
    #     :return: new Position destination
    #     """
    #
    #     x_offset = random.randint(-glo.Const.Initial_Scoot_Distance, glo.Const.Initial_Scoot_Distance)
    #     y_offset = random.randint(-glo.Const.Initial_Scoot_Distance, glo.Const.Initial_Scoot_Distance)
    #
    #     return Position(current_position.x + x_offset, current_position.y + y_offset)
    @staticmethod
    def generate_random_offset():
        """
        Generates a random Direction

        :rtype: object
        :return: Direction
        """

        # return Direction(random.randint(-1, 1), random.randint(-1, 1))
        return random.choice([Direction.North, Direction.South, Direction.East, Direction.West])

    @staticmethod
    def generate_profitable_offset(ship: object, game_map: object) -> object:
        """
        Finds the most profitable direction to move in, or random if none are
        available.

        :param ship:
        :param game_map:
        :return: Direction
        """

        new_dir = analytics.HaliteAnalysis.find_best_dir(ship, game_map)

        if new_dir is not None:
            glo.Misc.loggit('core', 'debug', " -* generate_profitable_offset() returning: " + str(new_dir) +
                            " from: analytics.HaliteAnalysis.find_best_dir()")
            return new_dir
        else:
            new_dir = Nav.generate_random_offset(ship.position)
            glo.Misc.loggit('core', 'debug', " -* generate_profitable_offset() returning: " + str(new_dir) +
                            " from:  Nav.generate_random_offset()")
            return new_dir

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
        next_dir = analytics.NavAssist.avoid_collision_by_random_scoot(direction, ship)
        if next_dir is not None:
            next_dest = game_map[ship.position.directional_offset(direction)]

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

    class ScuttleSupport:
        """
        Holds the navigation routines utilized in Core.scuttle_for_finish()
        """

        @staticmethod
        def scuttle_for_finish(me, game_map, turn):
            """
            Run back home to the shipyard (or later the dropoff) in order to return
            halite ore before the end of the game.

            TODO: add dropoff support

            :param me:
            :param game_map:
            :param turn:
            :return:
            """

            # NOTE: this routine will not work in conjunction with the other
            # normal ship in me.get_ships() game routine
            c_queue = []

            history.Misc.kill_dead_ships(me)

            for ship in me.get_ships():
                if glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.get_distance:
                    glo.Misc.loggit('scuttle', 'info',
                                    " - ship.id: " + str(ship.id) + " getting away from shipyard to " +
                                    glo.Variables.current_assignments[ship.id].destination)

                    c_queue.append(ship.move(game_map.naive_navigate(ship,
                                                                     glo.Variables.current_assignments[ship.id].
                                                                     destination)))

                # head to the blockade
                # elif ship.position == me.shipyard.position and \
                #         ship.halite_amount <= constants.MAX_HALITE - 100:
                elif ship.halite_amount <= 350:
                    glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.blockade
                    glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
                    glo.Variables.current_assignments[ship.id].turnstamp = turn

                    c_queue.append(Offense.blockade_enemy_drops(ship, game_map))

                # head back to the drop, it's scuttle time
                elif glo.Variables.current_assignments[ship.id].primary_mission != glo.Missions.scuttle:
                    glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " heading back to drop")
                    glo.Variables.current_assignments[ship.id].primary_mission = glo.Missions.scuttle
                    glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
                    glo.Variables.current_assignments[ship.id].turnstamp = turn
                    glo.Variables.current_assignments[ship.id].destination = me.shipyard.position

                    c_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))

                # already scuttling, keep it up
                else:
                    glo.Misc.loggit('scuttle', 'info', " - ship.id: " + str(ship.id) + " en route back to drop")
                    c_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))

                    # after we try this with naive_navigate we'll give it a shot with
                    # an implementation using seek_n_nav's less_dumb_move(), as well

            return c_queue


class Offense:
    @staticmethod
    def blockade_enemy_drops(ship, game_map):
        """
        Method will identify the enemy shipyard locations, determine which are
        best for a timely blockade, and send ships that have completed their
        dropoffs to the primary lanes entering such.

        TODO: don't use collision detection (ie naive_navigate)
        TODO: if more than one ship is headed there, block each of the 4 lanes

        :param ship:
        :param game_map:
        :return: command_queue addition
        """

        glo.Misc.log_w_shid('blockade', 'info', ship.id, " - entered blockade_enemy_drops()")

        target_syard_pos = None
        dist = game_map.width * 2 + 1  # ObDistanceBiggerThanGamesMaxDist

        # determine the closest shipyard
        for enemy_syard_pos in glo.Const.Enemy_Drops:
            if game_map.calculate_distance(ship.position, enemy_syard_pos) < dist:
                glo.Misc.log_w_shid('blockade', 'info', ship.id, " -* found close(er) shipyard at: " +
                                    str(enemy_syard_pos))
                dist = game_map.calculate_distance(ship.position, enemy_syard_pos)
                target_syard_pos = enemy_syard_pos

        if target_syard_pos is not None:
            return ship.move(game_map.naive_navigate(ship, target_syard_pos))
        else:
            glo.Misc.log_w_shid('blockade', 'info', ship.id, " -* did not find enemy shipyard(s)")

            return ship.move(game_map.naive_navigate(ship, Position(1, 1)))


class StartUp:
    @staticmethod
    def get_initial_minimum_distance(ship, me, game_map, turn):
        """
        Returns the command_queue data for the ship obtaining initial minimum
        distance in order to avoid clogging the shipyard access.

        :param ship:
        :param me:
        :param game_map:
        :param turn:
        :return:
        """

        glo.Misc.loggit('core', 'debug', " - fell into except; **setting new ship id: " + str(ship.id) +
                        " to mining**")
        # glo.Misc.loggit('core', 'debug', " -* ke: " + str(key_exception))

        tmp_destination_dir = Nav.generate_profitable_offset(ship, game_map)
        glo.Misc.loggit('core', 'debug', " -** tmp_destination_dir contents: " + str(tmp_destination_dir))

        while ship.position.directional_offset(tmp_destination_dir) == me.shipyard.position or \
                game_map[ship.position.directional_offset(tmp_destination_dir)].is_occupied:
            tmp_destination_dir = glo.Misc.r_dir_choice()

        # determine a new destination; for now it's just going to be Initial_Scoot_Distance moves in the most
        # profitable direction (this will need to be changed, obviously)
        cntr = 0
        inc_pos = ship.position
        while cntr < glo.Const.Initial_Scoot_Distance:
            cntr += 1
            inc_pos = inc_pos.directional_offset(tmp_destination_dir)

        glo.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                         # ship.position.directional_offset(
                                                                         #    tmp_destination_dir),
                                                                         inc_pos, turn, glo.Missions.mining,
                                                                         glo.Missions.in_transit)

        # return ship.move(random.choice([Direction.North, Direction.South, Direction.East, Direction.West]))
        # while ship.position.directional_offset(tmp_destination_dir) in glo.Variables.considered_destinations:
        #     tmp_destination_dir = glo.Misc.r_dir_choice()
        tmp_destination_dir = analytics.NavAssist.avoid_collision_by_random_scoot(tmp_destination_dir, ship)
        if tmp_destination_dir is None:
            return ship.stay_still()
        else:
            return Nav.less_dumb_move(ship, tmp_destination_dir, game_map)


class Misc:
    @staticmethod
    def is_position_normalized(pos, game_map):
        """
        Returns t/f whether or not the position is normalized

        :param pos:
        :param game_map:
        :return: boolean
        """

        if pos.x >= game_map.width or pos.y >= game_map.height:
            return False
        else:
            return True
