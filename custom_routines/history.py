"""
history.py

Started 5nov18

This is going to replace what was going on in state_save.py in d4m0Turtle
previously
"""

from . import myglobals as glo


class ShipHistory:
    """
    This will just save the ship's particular state, at least for a
    certain number of turns, before updating.
    """

    id = -1             # will be rational after init
    location = None
    destination = None
    turnstamp = -1      # see comment above
    primary_mission = "nada"
    secondary_mission = "nada"

    def is_initialized(self):
        """
        Returns the answer to whether or not we're fully initialized...

        NOTE: no check for destination because it might legitimately be None
        at times.

        :return: Boolean
        """

        if (self.id == -1) or (self.location is None) or (self.turnstamp == -1) or (self.primary_mission == 'nada') or \
             (self.secondary_mission == 'nada'):
            return False

        return True

    def is_alive(self, me):
        """
        Are we representing a living ship?

        :param me:
        :return: boolean
        """

        if not self.is_initialized():
            return None     # an exception would be better here

        return me.has_ship(self.id)

    def __init__(self, new_id, new_location, new_destination, new_turnstamp,
                 new_pmission, new_smission):
        self.id = new_id
        self.location = new_location
        self.destination = new_destination
        self.turnstamp = new_turnstamp
        self.primary_mission = new_pmission
        self.secondary_mission = new_smission

    def __str__(self):
        return "ship ID: " + str(self.id) + ", location: " + str(self.location) + ", destination: " \
               + str(self.destination) + ", turnstamp set: " + str(self.turnstamp) + ", secondary_mission: " + \
               str(self.secondary_mission) + ", primary_mission: " + str(self.primary_mission)

    def set_ldps(self, loc, dest, pri, sec):
        """
        Set the current ship's location, destination, primary, and secondary
        missions.

        :param loc: ship's current location
        :param dest: ship's destination
        :param pri: ship's primary mission
        :param sec:   "  secondary mission
        :return:
        """

        self.location = loc

        if dest is not self.destination:
            glo.Misc.loggit('any', 'info', " -* changing destination to " + str(dest))
            self.destination = dest

        if pri is not self.primary_mission:
            glo.Misc.loggit('any', 'info', " -* changing primary mission to " + str(pri))
            self.primary_mission = pri

        if sec is not self.secondary_mission:
            glo.Misc.loggit('any', 'info', " -* changing secondary mission to " + str(sec))
            self.secondary_mission = sec

    def set_loc(self, loc):
        """
        Set the location of the current ship.

        :param loc: ship's current location
        :return:
        """

        self.location = loc

    def set_dest(self, dest):
        """
        Set the destination of the current ship.

        :param dest: ship's new destination
        :return:
        """

        self.destination = dest

    @staticmethod
    def prune_current_assignments(me):
        """
        Runs through the current assignments; picks out which ships are in the
        history, but not in the valid ships list (ie dead ones), and returns
        the list to the caller

        :param me:
        :return:
        """

        shids = []

        for ship_history_key in glo.Variables.current_assignments.keys():
            glo.Misc.loggit('pruning', 'info', " - pruning current_assignments, if necessary (ship: " +
                                  str(ship_history_key) + ")")

            try:
                if me.get_ship(ship_history_key) is None:
                    # wipe entry
                    glo.Misc.loggit('pruning', 'info', " -* wiping ship.id: " + str(ship_history_key) +
                                          " from current_assignments due to its demise")
                    shids.append(ship_history_key)
            except:
                # wipe entry
                glo.Misc.loggit('pruning', 'info', " -* wiping ship.id: " + str(ship_history_key) +
                                      " from current_assignments due to its demise")
                shids.append(ship_history_key)
                
            return shids


class Misc:
    """
    Different support routines related to the ShipHistory object(s).
    """

    @staticmethod
    def kill_dead_ships(me):
        """
        Determines which ships have been deceased, and removes them from the
        current_assignments dict of ShipHistory objects.

        :param me:
        :return:
        """

        new_kill_list_additions = ShipHistory.prune_current_assignments(me)
        glo.Misc.loggit('core', 'debug', "Killing from history due to ship 8-x: " + str(new_kill_list_additions))
        if new_kill_list_additions is not None:
            for shid in new_kill_list_additions:
                # wipe away the dingleberries
                glo.Misc.loggit('core', 'debug', "Killing history of shid: " + str(shid))
                glo.Variables.current_assignments.pop(shid, None)
