"""
mining.py

started 9nov18

Mining algorithm internals.
"""

from hlt import Direction

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

        final_dir = Direction.Still

        for tmp_dir in Direction.get_all_cardinals():
            if game_map[ship.position.directional_offset(tmp_dir)].is_occupied:
                # we can return our pseudo-random direction
                glo.Misc.log_w_shid('mining', 'core', ship.id,
                                    " -** in questionable clause w/low_cargo_and_no_immediate_halite()")
            else:
                final_dir = tmp_dir

        if final_dir != Direction.Still:
            glo.Misc.add_barred_destination(final_dir, ship)

            return ship.move(game_map.naive_navigate(ship, ship.position.directional_offset(final_dir)))
        else:
            return ship.stay_still()

    @staticmethod
    def done_with_transit_now_mine(ship, turn):
        """
        We're there, time to get to work.

        :param ship:
        :param turn:
        :return: stay_still()
        """

        glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **mining** at " + str(ship.position))
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
            analytics.NavAssist.avoid_if_ship_blocking(game_map, ship)

            return ship.move(game_map.naive_navigate(ship, ship.position.directional_offset(profit_dir)))

