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

    def __init__(self, me, game_map, init_x, init_y):
        """
        It should be noted at this point that self.cell_data[x][y] =
        halite_amount is not going to be an effective utilization of this
        object.  cell_data[x][y] should point to a dict, of which the
        halite content of the cell will be one of the things stored.

        TODO: Implement effective MapChunk data structure

        :param me:
        :param game_map:
        :param init_x:
        :param init_y:
        """
        # NOTE: init will need to be run again after a shipyard or dropoff is
        # built within this chunk

        self.x_start = init_x
        self.y_start = init_y

        dropoffs = me.get_dropoffs()

        for x in range(0, self.Width - 1):
            for y in range(0, self.Height - 1):
                # determine halite amount
                self.cell_data[x][y] = game_map[Position(x + self.x_start, y + self.y_start)].halite_amount

                # structures?
                if Position(x + self.x_start, y + self.y_start).has_structure and not (self.has_shipyard and
                        self.has_dropoff):
                    # is it mine?
                    try:
                        for drop in dropoffs:
                            if drop.owner == me.id and drop.position.x >= self.x_start and \
                                  drop.position.x < self.x_start + self.Width and drop.position.y >= self.y_start \
                                  and drop.position.y < self.y_start + self.Height:
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

    def mark_devoid_cells(self, ship, game_map):
        """
        Method goes through the cells in this particular chunk and, for this
        ship, marks them as 'unsafe' when they have no halite, in order to
        make naive_navigate() keep us in halite laden squares.

        NOTE: There will have to be a backup when no halite is present to give
        a path to percolate through.

        :param ship:
        :param game_map:
        :return:
        """

        for x in range(self.x_start, self.x_start + self.Width - 1):
            for y in range(self.y_start, self.y_start - self.Height):
                if game_map[Position(x, y)].halite_amount == 0:
                    game_map[Position(x, y)].mark_unsafe(ship)

    def find_most_profitable(self, game_map):
        """
        Method returns the position of the most profitable halite mining
        location in the MapChunk we're working with, or none if everything is
        empty.

        :return:
        """

        max_halite = 0
        max_halite_position = None

        for x in range(self.x_start, self.x_start + self.Width - 1):
            for y in range(self.y_start, self.y_start - self.Height):
                if game_map[Position(x, y)].halite_amount > max_halite:
                    max_halite = game_map[Position(x, y)].halite_amount
                    max_halite_position = Position(x, y)

        return max_halite_position

    @staticmethod
    def create_centered_chunk(me, ship, game_map):
        return MapChunk(me, game_map, ship.position.x - (MapChunk.Width % 2), ship.position.y - (MapChunk.Height % 2))


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

        NOTE: That this should be rendered obsolete by implementation of
        MapChunk properly, as that'll be scanning an arbitrary sized grid for
        the best halite amount.  This will have to do until we can scan for
        local maxima.

        :param ship:
        :param game_map:
        :return: Direction
        """

        halite_best = 0
        best_dir = seek_n_nav.Nav.generate_random_offset(ship, game_map)

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
    def avoid_if_ship_blocking(game_map, ship):
        """
        If there is a ship blocking the way, this routine will mark the cell as
        unsafe, in order to avoid pawn formations in routines that are
        utilizing .naive_navigate() without other fallbacks.

        :param game_map:
        :param ship:
        :return:
        """

        for test_dir in game_map[ship.position].position.get_surrounding_cardinals():
            if game_map[test_dir].is_occupied:
                game_map[test_dir].mark_unsafe(ship)

        return

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
        """
        Method iterates through the enemy shipyards, determining also what ship
        is assigned each shipyard to help blockade

        :param game:
        :return:
        """

        # identify map data for Const storage and later retrieval
        glo.Misc.loggit('preprocessing', 'info', "Scanning for enemy shipyards")

        # this is a whole lot easier
        tot_game_players = 0
        for player in game.players.values():
            if player is not game.me:
                glo.Misc.loggit('preprocessing', 'debug', " - found shipyard @ " +
                                str(player.shipyard) + " belonging to player: " + str(player.id))

                glo.Const.Enemy_Drops.append(player.shipyard.position)
                tot_game_players += 1

        # 4 ships per shipyard; this is an expensive maneuver; probably only
        # viable in 2 player games
        tot_cntr = 0
        for blockade_ship in game.me.get_ships():
            # we're just doing first come first serve right now; later on we'll
            # want to make sure that we're not 'spending' ships that are too
            # far away or too full of halite prior to a drop
            for pathway_dir in Direction.get_all_cardinals():    # four ships per drop
                # glo.Misc.set_n_log_new_dest(blockade_ship,
                #                             glo.Const.Enemy_Drops[tot_cntr].get_directional_offset(pathway_dir))
                glo.Variables.current_assignments[blockade_ship.id].set_ldps(blockade_ship.position,
                                                                             glo.Const.Enemy_drops[tot_cntr].
                                                                                get_directional_offset(pathway_dir),
                                                                             glo.Missions.early_blockade,
                                                                             glo.Missions.in_transit)

            tot_cntr += 1
            if tot_cntr > tot_game_players * 4:
                continue

        glo.Variables.early_blockade_initialized = True

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
        key routes into the enemy shipyards.  This sets each particular
        destination.

        :param me:
        :param game:
        :param turn:
        :return:
        """

        glo.Misc.loggit('early_blockade', 'debug', "initializing early_blockade() data")

        sorted_ships = []
        sorted_ships = Offense.sort_ships_by_halite(me, True)
        ship_cntr = 0

        for playa in game.players:
            if playa == me.id:
                continue

            for drop_route in game.players[playa].shipyard.position.get_surrounding_cardinals():
                # assign a ship to each
                # for now I think we'll just do this starting with the ships
                # with the least halite

                # glo.Variables.drop_assignments[drop_route] = sorted_ships[ship_cntr]

                glo.Misc.log_w_shid('early_blockade', 'debug', sorted_ships[ship_cntr].id,
                                    " - setting destination to :" + str(drop_route))

                glo.Variables.current_assignments[sorted_ships[ship_cntr].id].set_ldps(sorted_ships[ship_cntr].position,
                                                                                       drop_route,
                                                                                       glo.Missions.early_blockade,
                                                                                       glo.Missions.in_transit)
                glo.Variables.current_assignments[sorted_ships[ship_cntr].id].turnstamp = turn

                ship_cntr += 1

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

