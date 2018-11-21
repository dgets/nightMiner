"""
mining.py

started 9nov18

Mining algorithm internals.
"""

from . import seek_n_nav, analytics
from . import myglobals as glo


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
        glo.Misc.log_w_shid('seek', 'debug', ship.id, " ShipHistory-->" +
                            str(glo.Variables.current_assignments[ship.id]))

        # new_pos = ship.position.directional_offset(analytics.HaliteAnalysis.find_best_dir(ship, game_map))
        new_dir = analytics.NavAssist.avoid_collision_by_random_scoot(
            seek_n_nav.Nav.generate_profitable_offset(ship, game_map), ship)

        if new_dir is None:
            glo.Misc.loggit('core', 'debug', " -* staying still for collision avoidance")
            return ship.stay_still()

        new_pos = ship.position.directional_offset(new_dir)
        glo.Misc.loggit('core', 'debug', " -* new_pos contents: " + str(new_pos))

        # random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
        glo.Variables.current_assignments[ship.id].destination = new_pos
        glo.Variables.current_assignments[ship.id].secondary_mission = glo.Missions.in_transit
        glo.Variables.current_assignments[ship.id].turnstamp = turn

        glo.Misc.log_w_shid('seek', 'debug', ship.id, " ShipHistory after processing-->" +
                            str(glo.Variables.current_assignments[ship.id]))

        # return seek_n_nav.Nav.less_dumb_move(ship, glo.Misc.r_dir_choice(), game_map)
        return ship.move(new_dir)

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


class CoreSupport:
    """
    Using this class as a home to modularize Core.primary_mission_mining(),
    possibly other stuff afterwards as well.
    """

    @staticmethod
    def wtf_happened(ship, game_map, turn):
        """
        Catch-all loop for Core.primary_mission_mining().

        :param ship:
        :param game_map:
        :param turn:
        :return: c_queue_addition
        """

        glo.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " **WTF**  ship history dump: " +
                        str(glo.Variables.current_assignments[ship.id]) + "; full ship dump: " +
                        str(ship))

        profit_dir = seek_n_nav.Nav.generate_profitable_offset(ship, game_map)
        glo.Variables.current_assignments[ship.id].set_ldps(ship.position,
                                                            ship.position.directional_offset(profit_dir),
                                                            glo.Missions.mining, glo.Missions.in_transit)
        glo.Variables.current_assignments[ship.id].turnstamp = turn

        if game_map[ship.position].halite_amount > 0 and not ship.is_full:
            return ship.stay_still()
        else:
            return ship.move(game_map.naive_navigate(ship, ship.position.directional_offset(profit_dir)))

