"""
analytics.py

started 8nov18

Class will hold different (dumb) analytic routines.
"""

from hlt import Position, Direction, entity

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


class Offense:
    """
    Offensive analytics.
    """

    @staticmethod
    def scan_for_enemy_shipyards(game):
        # identify map data for Const storage and later retrieval
        glo.Misc.loggit('preprocessing', 'info', "Scanning for enemy shipyards")

        # for x in range(0, game.game_map.width):
        #     glo.Misc.loggit('preprocessing', 'debug', " - scanning column: " + str(x))
        #     for y in range(0, game.game_map.height):
        #         # check each map cell
        #         glo.Misc.loggit('preprocessing', 'debug', "  - scanning cell: " + str(Position(x, y)))
        #         if game.game_map[Position(x, y)].has_structure:
        #             glo.Misc.loggit('preprocessing', 'debug', "  -* _HAS_ structure")
        #
        #         # NOTE: this only verifies that it's not our shipyard, as no drops would exist yet
        #         if game.game_map[Position(x, y)].structure_type is not None and \
        #                 game.me.shipyard.position != Position(x, y):
        #             # there is a structure that is not ours
        #             glo.Misc.loggit('preprocessing', 'debug', "Enemy shipyard at: " + str(Position(x, y)))
        #
        #             glo.Const.Enemy_Drops.append(Position(x, y))

        # this is a whole lot easier
        for player in game.players:
            if player is not game.me:
                glo.Misc.loggit('preprocessing', 'debug', " - found shipyard @ " +
                                str(player) + " belonging to player: " +
                                str(player))
                # glo.Const.Enemy_Drops.append(player.shipyard.position)

        return
