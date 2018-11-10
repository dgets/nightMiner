"""
history.py

Started 5nov18

This is going to replace what was going on in state_save.py in d4m0Turtle
previously
"""

from . import myglobals


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

    @staticmethod
    def prune_current_assignments(me):
        """
        Runs through the current assignments; picks out which ships are in the
        history, but not in the valid ships list (ie dead ones), and returns
        the list to the caller

        :param me:
        :return:
        """
        # see if we've got any dead ships still recorded

        shids = []

        for ship_history_key in myglobals.Variables.current_assignments.keys():
            myglobals.Misc.loggit('pruning', 'info', " - pruning current_assignments, if necessary (ship: " +
                                  str(ship_history_key) + ")")

            #if not myglobals.Variables.current_assignments[ship_history_key].is_alive(me):
            try:
                if me.get_ship(ship_history_key) is None:
                    # wipe entry
                    myglobals.Misc.loggit('pruning', 'info', " -* wiping ship.id: " + str(ship_history_key) +
                                          " from current_assignments due to its demise")
                    shids.append(ship_history_key)
            except:
                # wipe entry
                myglobals.Misc.loggit('pruning', 'info', " -* wiping ship.id: " + str(ship_history_key) +
                                      " from current_assignments due to its demise")
                shids.append(ship_history_key)
                
            return shids