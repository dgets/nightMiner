"""
analytics.py

started 8nov18

Class will hold different (dumb) analytic routines.
"""

from hlt import Position, Direction

from . import seek_n_nav
from . import myglobals as glo


class MapChunk:
    """
    Class will hold 5x5 grids comprising the primary map's data, with specific
    routines available to help plot courses through without wasting halite,
    determination on whether or not there is a shipyard or drop site available
    locally, etc.
    """

    Width = glo.Const.Max_Chunk_Width
    Height = glo.Const.Max_Chunk_Height

    x_start = -1
    y_start = -1

    # gotta use the list comprehension for arrays here I guess
    cell_data = [[0 for x in range(glo.Const.Max_Chunk_Width)] for y in range(glo.Const.Max_Chunk_Height)]

    # NOTE: we're not going to be using arrays to hold multiple shipyards or
    # dropoff points at this point, so if there's more than one we'll just
    # not bother with anything beyond the first
    has_shipyard = None
    has_dropoff = None

    def __init__(self, me, map, init_x, init_y):
        # NOTE: init will need to be run again after a shipyard or dropoff is
        # built within this chunk

        self.x_start = init_x
        self.y_start = init_y

        dropoffs = me.get_dropoffs()

        for x in range(0, self.Width - 1):
            for y in range(0, self.Height - 1):
                # determine halite amount
                self.cell_data[x][y] = map[Position(x + self.x_start, y + self.y_start)].halite_amount

                # structures?
                if Position(x + self.x_start, y + self.y_start).has_structure and not (self.has_shipyard and
                        self.has_dropoff):
                    # is it mine?
                    try:
                        for drop in dropoffs:
                            if drop.owner == me.id and (drop.position.x >= self.x_start and
                                  drop.position.x < (self.x_start + self.Width) and (drop.position.y >= self.y_start
                                  and drop.position.y < self.y_start + self.Height)):
                                # we have a drop
                                self.has_dropoff = True
                                break
                    except:
                        self.has_dropoff = False

                    if me.shipyard.position.x >= self.x_start and me.shipyard.position.x < (self.x_start + self.Width) \
                            and me.shipyard.position.y >= self.y_start and \
                            me.shipyard.position.y < (self.y_start + self.Height):
                        self.has_shipyard = True
                    else:
                        self.has_shipyard = False

                    if self.has_dropoff is None:
                        self.has_dropoff = False

    def mark_devoid_cells(self, ship, map):
        """
        Method goes through the cells in this particular chunk and, for this
        ship, marks them as 'unsafe' when they have no halite, in order to
        make naive_navigate() keep us in halite laden squares.

        NOTE: There will have to be a backup when no halite is present to give
        a path to percolate through.

        :param ship:
        :param map:
        :return:
        """
        for x in range(self.x_start, self.x_start + self.Width - 1):
            for y in range(self.y_start, self.y_start - self.Height):
                if map[Position(x, y)].halite_amount == 0:
                    map[Position(x, y)].mark_unsafe(ship)

    @staticmethod
    def create_centered_chunk(me, ship, map):
        return MapChunk(me, map, ship.position.x - (MapChunk.Width % 2), ship.position.y - (MapChunk.Height % 2))


class HaliteAnalysis:
    """
    Different static methods for analyzing the halite content of the map in
    general and in other non-MapChunk situations.
    """

    @staticmethod
    def find_best_dir(ship, game_map):
        """
        Method will use the ship's position to scan the 4 cardinal directions
        for the most profitable halite move.  Will return the direction.  Note
        that this will be taking into account whether or not that cell is
        currently occupied.

        :param ship:
        :param game_map:
        :return: Direction
        """
        halite_best = 0
        best_dir = seek_n_nav.Nav.generate_random_offset()

        glo.Misc.log_w_shid('seek', 'info', ship.id, "Entered analytics.HaliteAnalysis.find_best_dir()")

        for da_way in Direction.get_all_cardinals():
            glo.Misc.log_w_shid('seek', 'debug', ship.id, " - considering " +
                                str(ship.position.directional_offset(da_way)))

            if game_map[ship.position.directional_offset(da_way)].halite_amount > halite_best and \
                    game_map[ship.position.directional_offset(da_way)].is_empty:
                glo.Misc.log_w_shid('seek', 'debug', ship.id, " - * currently found " +
                                    str(ship.position.directional_offset(da_way)) + " to be best w/" +
                                    str(game_map[ship.position.directional_offset(da_way)].halite_amount) +
                                    " halite & empty")

                halite_best = game_map[ship.position.directional_offset(da_way)].halite_amount
                best_dir = da_way

        return best_dir


class NavAssist:
    """
    Originally created as a place to house a routine created to 'globally'
    avoid collisions between our own ships, this will house any sort of
    analytic routines meant to assist in navigation.
    """

    @staticmethod
    def avoid_collision_by_wait(dest_dir, ship):
        """
        Method will determine whether or not the directional move being
        considered has already been taken by a ship during this turn; if so,
        it will go with staying still instead of making a move this turn (ie
        allow the other ship to pass by and then go on its way.

        TODO: Add verification of whether or not the other ship is marked 'in_transit'

        :param dest_dir:
        :param ship:
        :return: Direction or None
        """
        if ship.position.directional_offset(dest_dir) in glo.Variables.considered_destinations:
            return None
        else:
            glo.Misc.add_barred_destination(dest_dir, ship)
            return dest_dir

    @staticmethod
    def avoid_collision_by_random_scoot(dest_dir, ship):
        """
        Method will, again, determine whether or not the directional move being
        considered has already been taken; if so, it will attempt the other
        cardinal directions.  The first without any occupants will be selected;
        if all have occupants, None will be returned.

        :param dest_dir:
        :param ship:
        :return: Direction or None
        """
        if ship.position.directional_offset(dest_dir) in glo.Variables.considered_destinations:
            # position is already taken

            for tmp_dir in [Direction.North, Direction.South, Direction.East, Direction.West]:
                if ship.position.directional_offset(tmp_dir) not in glo.Variables.considered_destinations:
                    # we can return our pseudo-random direction

                    glo.Misc.add_barred_destination(tmp_dir, ship)
                    return tmp_dir

            # we're just going to have to stay still if we're here
            return None

        else:
            # position was not taken
            return dest_dir

    @staticmethod
    def are_we_blocking_our_shipyard(me):
        """
        Boolean return for whether or not we're over our own shipyard.

        :param me:
        :return: Boolean
        """

        for test_ship in me.get_ships():
            if test_ship.position is me.shipyard.position:
                return True

        return False

class Offense:
    """
    Offensive analytics.
    """

    @staticmethod
    def scan_for_enemy_shipyards(game):
        # identify map data for Const storage and later retrieval
        glo.Misc.loggit('preprocessing', 'info', "Scanning for enemy shipyards")

        # this is a whole lot easier
        for player in game.players.values():
            if player is not game.me:
                glo.Misc.loggit('preprocessing', 'debug', " - found shipyard @ " +
                                str(player.shipyard) + " belonging to player: " + str(player.id))

                glo.Const.Enemy_Drops.append(player.shipyard.position)

        return

    @staticmethod
    def can_we_early_blockade(game):
        """
        Method returns true if we can spare enough ships to continue mining
        while blockading the enemy shipyards, false if otherwise.

        :param game:
        :return: Boolean
        """

        glo.Misc.loggit('early_blockade', 'debug', "testing whether to enable early_blockade(): " +
                        str(len(game.me.get_ships())) + " (?>) " + str((((len(game.players.values()) - 1) * 4) +
                                                                        glo.Const.Early_Blockade_Remainder_Ships)))

        if len(game.me.get_ships()) > (((len(game.players.values()) - 1) * 4) +
                                       glo.Const.Early_Blockade_Remainder_Ships):
            glo.Misc.loggit('early_blockade', 'info', "enabling early blockade")
            return True
        else:
            return False

    @staticmethod
    def init_early_blockade(me, game, turn):
        """
        Method assigns ships with the least amount of halite to individual
        key routes into the enemy shipyards.

        :param me:
        :param game:
        :param turn:
        :return:
        """

        glo.Misc.loggit('early_blockade', 'debug', "initializing early_blockade() data")

        sorted_ships = Offense.sort_ships_by_halite(me, True)
        ship_cntr = 0

        for playa in game.players:
            for drop_route in playa.shipyard.position.get_surrounding_cardinals():
                # assign a ship to each
                # for now I think we'll just do this starting with the ships
                # with the least halite
                glo.Variables.drop_assignments[drop_route] = sorted_ships[ship_cntr]
                ship_cntr += 1

                glo.Variables.current_assignments[sorted_ships[ship_cntr].id].destination = drop_route
                glo.Variables.current_assignments[sorted_ships[ship_cntr].id].primary_mission = \
                    glo.Missions.early_blockade
                glo.Variables.current_assignments[sorted_ships[ship_cntr].id].secondary_mission = \
                    glo.Missions.in_transit
                glo.Variables.current_assignments[sorted_ships[ship_cntr].id].turnstamp = turn

        glo.Variables.early_blockade_initialized = True

        return


    @staticmethod
    def sort_ships_by_halite(me, least_to_highest):
        """
        This one will sort the ships we've got by the amount of halite that
        they have on board, and return the list in that order.

        :param me:
        :param least_to_highest: Boolean
        :return: sorted list
        """

        tmp_msg = " - sorting ships by halite "
        if least_to_highest:
            tmp_msg += "(descending)"
        else:
            tmp_msg += "(ascending)"
        glo.Misc.loggit('misc_processing', 'info', tmp_msg)

        all_ships = me.get_ships()

        for cntr in range(1, len(all_ships) - 2):   # this may not be the optimal for bubble sort
            for cntr2 in range(1, len(all_ships) - 1):
                if least_to_highest:    # descending
                    if all_ships[cntr2].halite_amount > all_ships[cntr2 - 1].halite_amount:
                        tmp_ship = all_ships[cntr2]
                        all_ships[cntr2] = all_ships[cntr2 - 1]
                        all_ships[cntr2 - 1] = tmp_ship

                else:   # ascending
                    if all_ships[cntr2].halite_amount < all_ships[cntr2 - 1].halite_amount:
                        tmp_ship = all_ships[cntr2]
                        all_ships[cntr2] = all_ships[cntr2 - 1]
                        all_ships[cntr2 - 1] = tmp_ship

        return all_ships

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

        # if not Offense.can_we_early_blockade(game):
        #     return None

        if not glo.Variables.early_blockade_enabled:
            Offense.init_early_blockade(me, game, turn)

        tmp_msg = " assigned early_blockade "

        if ship.position is not glo.Variables.current_assignments[ship.id].destination:
            tmp_msg += "(en route to " + str(glo.Variables.current_assignments[ship.id].destination) + ")"
            glo.Misc.log_w_shid('early_blockade', ship.id, 'info', tmp_msg)

            return seek_n_nav.Nav.scoot(ship, game_map)
        else:
            tmp_msg += "(chillin' at " + ship.position + ")"
            glo.Misc.log_w_shid('early_blockade', ship.id, 'info', tmp_msg)

            return ship.stay_still()

