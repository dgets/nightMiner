"""
seek_n_nav.py

Started on: 6nov18 (or well that's when I remembered at add this note,
anyway)

routines for general seeking out of halite ore resources w/basic resource
location determination and navigation to it
"""

from hlt import Position

from . import history, analytics
from . import myglobals as glo


class Nav:
    @staticmethod
    def generate_random_offset(ship, game_map):
        """
        Generates a random Direction

        :rtype: object
        :return: Direction
        """

        tmp_dir = glo.Misc.r_dir_choice()
        while game_map[ship.position.directional_offset(tmp_dir)].is_occupied:
            tmp_dir = glo.Misc.r_dir_choice()

        return tmp_dir

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
        else:
            new_dir = Nav.generate_random_offset(ship, game_map)
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

        if (ship.position in glo.Variables.current_assignments[ship.id].destination.get_surrounding_cardinals()) and \
           game_map[glo.Variables.current_assignments[ship.id].destination].is_occupied and \
           not analytics.NavAssist.are_we_blocking_our_shipyard(me):

            # we should collide over the shipyard, as it's an opponent
            # blocking our final hop
            new_direction = Misc.is_direction_normalized(game_map, ship)
            if new_direction is None:
                return ship.stay_still()

            glo.Misc.log_w_shid('mining', 'debug', ship.id, " moving to destination " +
                                str(glo.Variables.current_assignments[ship.id].destination))

            return ship.move(new_direction)

        target_dir = Misc.is_direction_normalized(game_map, ship)
        if target_dir is None:
            # again, not sure why I'm here, but let's process for it
            return ship.stay_still()

        if game_map[ship.position.directional_offset(target_dir)].is_occupied or \
                Nav.check_for_potential_collision(ship.position.directional_offset(target_dir)):
            return ship.move(Nav.generate_profitable_offset(ship, game_map))

        return ship.move(game_map.naive_navigate(ship, glo.Variables.current_assignments[ship.id].destination))

    @staticmethod
    def less_dumb_move(ship, direction, game_map):
        """
        Moves into the cell in the direction given, if not occupied, or else
        waits for a turn in order to avoid collision

        TODO: see if this is ready for complete deprecation and then remove

        :param ship:
        :param direction:
        :param game_map:
        :return:
        """

        next_dir = analytics.NavAssist.avoid_collision_by_random_scoot(direction, ship)
        if next_dir is not None and \
                Nav.check_for_potential_collision(game_map[ship.position.directional_offset(direction)].position):
            return Nav.generate_profitable_offset(ship, game_map)
        elif next_dir is not None:
            return ship.move(game_map.naive_navigate(ship,
                                                     game_map[ship.position.directional_offset(direction)].position))
        else:
            # I guess we'll just wait for now
            glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " avoiding collision at " +
                            str(ship.position))
            # no, we're gonna try to not use stay_still() any more
            # return ship.stay_still()

            return ship.move(Nav.generate_profitable_offset(ship, game_map))

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

        glo.Misc.loggit('core', 'debug', " -* ship's current position: " + str(ship.position))
        # glo.Misc.loggit('core', 'debug', " -* destination: " +    # this is covered above in the 'scoot' log stmt
        #                str(glo.Variables.current_assignments[ship.id].destination))

        target_dir = Misc.is_direction_normalized(game_map, ship)
        if target_dir is None:
            glo.Misc.loggit('core', 'debug', " -** staying still")
            return ship.stay_still()

        glo.Misc.loggit('core', 'debug', " -** processed results from _get_target_direction() to " + str(target_dir))

        if game_map[ship.position.directional_offset(target_dir)].is_occupied:
            glo.Misc.loggit('core', 'debug', " -** changing course due to occupied cell")
            return ship.move(Nav.generate_random_offset(ship, game_map))

        return ship.move(target_dir)

    @staticmethod
    def check_for_potential_collision(considered_position):
        """
        Method will check glo.Variables.considered_destinations to see if the
        considered_position in question already lives there; if it does, it
        will return True for collision detection, else False.

        :param considered_position:
        :return: Boolean
        """

        if considered_position in glo.Variables.considered_destinations:
            return True
        else:
            return False


class Offense:
    @staticmethod
    def blockade_enemy_drops(ship, game_map, me):
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

        # TODO: determine whether we need to implement random moving collision avoidance
        if target_syard_pos is not None and \
                Nav.check_for_potential_collision(ship.position.directional_offset(
                    game_map.naive_navigate(ship, target_syard_pos))):
            return ship.move(Nav.generate_random_offset(ship, game_map))
        elif target_syard_pos is not None:
            return ship.move(game_map.naive_navigate(ship, target_syard_pos))
        else:
            glo.Misc.log_w_shid('blockade', 'info', ship.id, " -* did not find enemy shipyard(s)")

            # TODO: remove this when we work on the pringles
            # NOTE: not going to bother adding collision detection code here,
            # being as this shouldn't even get utilized any more at this
            # point, or only at the very end of game when the ship won't be
            # changing the outcome at all, anyway
            return ship.move(game_map.naive_navigate(ship, Position(1, 1)))

    @staticmethod
    def early_blockade(me, ship, game, game_map, turn):
        """
        If we've got the ships to blockade at this point, we'll return the
        navigation command for this ship to take its rightful place.

        :param me:
        :param ship:
        :param game:
        :param game_map:
        :param turn:
        :return: None or cqueue_addition
        """

        if not glo.Variables.early_blockade_initialized:
            # analytics.Offense.init_early_blockade(me, game, turn)
            raise RuntimeError("early_blockade() not properly set up")

        tmp_msg = " assigned early_blockade "

        if ship.position is not glo.Variables.current_assignments[ship.id].destination:
            tmp_msg += "(en route to " + str(glo.Variables.current_assignments[ship.id].destination) + ")"
            glo.Misc.log_w_shid('early_blockade', 'info', ship.id, tmp_msg)

            return Nav.scoot(ship, game_map)
        else:
            tmp_msg += "(chillin' at " + ship.position + ")"
            glo.Misc.log_w_shid('early_blockade', ship.id, 'info', tmp_msg)

            return ship.stay_still()


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

    @staticmethod
    def is_direction_normalized(game_map, ship):
        """
        Takes the results of game_map._get_target_direction() and cleans the
        Nones out of it.  Assumes that the valid destination is packed into
        current_assignments[ship.id].destination.

        :param game_map:
        :param ship:
        :return: sanitized direction or None to flag for stay_still()
        """

        tmp_direction = game_map._get_target_direction(ship.position,
                                                       glo.Variables.current_assignments[ship.id].destination)

        glo.Misc.loggit('core', 'debug', " -* target's direction: " + str(tmp_direction))

        glo.Misc.loggit('core', 'debug', " -** trying bogus tuple fix")
        (trash1, trash2) = tmp_direction

        if trash1 is None and trash2 is None:
            # not sure why we're here, but we definitely want to stay
            return None
        elif trash1 is None:
            return trash2
        else:
            return trash1
