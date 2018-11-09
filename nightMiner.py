"""
nightMiner.py

Started 5 Nov 18

Just going with a rewrite of d4m0Turtle right now because of the amount of
issues I've had due to poor design strategy in the beginning of this project.
Going to try to keep a better focus on OO this time, and there may be one or
two other people actually collaborating on me with this project, so I figure
that the name doesn't have to have anything to do with my name in it, this
time around.  ;)
"""

import random

#import hlt
#from hlt import Direction
from hlt import constants
from custom_routines import myglobals, history, seek_n_nav, core_processing

# --==++** GAME BEGIN **++==--

game = core_processing.Core.original_preprocessing()

# for turnstamps
turn = 0

# --==++** PRIMARY GAME LOOP **++==--
while True:
    # set local versions of costly lookups
    game_map = game.game_map
    me = game.me  # keeps things speedier

    # costly preprocessing time
    core_processing.Core.per_turn_preprocessing(game, me)

    # initialize per-turn queues
    command_queue = []
    kill_from_history_queue = []
    new_kill_list_additions = []

    # clear up other potential crap
    c_queue_addition = None

    for ship in me.get_ships():
        kill_from_history_queue = []

        myglobals.Misc.loggit('core', 'info', " - processing ship.id: " + str(ship.id))
        try:
            # if this is a new ship, we'll be in the except, below
            if myglobals.Variables.current_assignments[ship.id].primary_mission == myglobals.Missions.mining:
                myglobals.Misc.loggit('core', 'debug', " - ship.id " + str(ship.id) + " in primary mining conditional")
                c_queue_addition = core_processing.Core.primary_mission_mining(ship, game_map, me, turn)

                if c_queue_addition is not None:
                    command_queue.append(c_queue_addition)
                else:
                    myglobals.Misc.loggit('core', 'debug', " -* added ship.id: " + str(ship.id) + " to kill list")
                    kill_from_history_queue.append(ship.id)

                continue

            # we've transited to the shipyard/dropoff
            elif myglobals.Variables.current_assignments[ship.id].secondary_mission == \
                    myglobals.Missions.in_transit \
                    and myglobals.Variables.current_assignments[ship.id].primary_mission == \
                    myglobals.Missions.dropoff and \
                    myglobals.Variables.current_assignments[ship.id].destination == ship.position and \
                    ship.halite_amount > 0:
                # make the drop
                myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " making drop @ " +
                                      str(ship.position))
                kill_from_history_queue.append(ship.id)

                # now we've got to wipe that from the current_assignments
                # to make sure that it's properly reassigned the next time
                # around
                if myglobals.Variables.current_assignments.pop(ship.id, None) is None:
                    myglobals.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " was found in an " +
                                          "invalid state (no current_assignments entry)!")  # should throw exception

                continue

            elif game_map.normalize(myglobals.Variables.current_assignments[ship.id].destination) == ship.position \
                    and myglobals.Variables.current_assignments[ship.id].primary_mission != \
                    myglobals.Missions.dropoff and not ship.is_full:
                # mine
                myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **mining** @ " +
                                      str(ship.position))
                myglobals.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                                       None, turn,
                                                                                       myglobals.Missions.mining,
                                                                                       myglobals.Missions.busy)
                command_queue.append(ship.stay_still())
                continue

            elif myglobals.Variables.current_assignments[ship.id].primary_mission == myglobals.Missions.dropoff and \
                    ship.position != me.shipyard.position:
                # head to drop off the halite
                myglobals.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " in **transit to drop**")
                command_queue.append(seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map, turn))
                continue

            elif myglobals.Variables.current_assignments[ship.id].primary_mission == myglobals.Missions.dropoff and \
                    ship.position == me.shipyard.position:
                # drop off the fucking halite HERE then, if nothing else
                myglobals.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " DROP the BONE")
                kill_from_history_queue.append(ship.id)

                continue

        except KeyError as ke:
            # set everybody to mining, first of all
            command_queue.append(seek_n_nav.StartUp.get_initial_minimum_distance(ship, turn, ke))

        myglobals.Misc.loggit('core', 'debug', " - found and processed ship: " + str(ship.id))

    # TODO: change hardcoded 200 below into a percentage of game turns
    #if game.turn_number <= 200 and me.halite_amount > myglobals.Const.Enough_Ore_To_Spawn and \
    if game.turn_number <= (constants.MAX_TURNS / 2) and me.halite_amount > myglobals.Const.Enough_Ore_To_Spawn and \
            not game_map[me.shipyard].is_occupied:
        myglobals.Misc.loggit('core', 'debug', " - spawning ship")
        command_queue.append(me.shipyard.spawn())

    # maintain the current_assignments as best we can here...
    myglobals.Misc.loggit('core', 'debug', "Killing from history for reassignment: " + str(kill_from_history_queue))

    # we've already got ships in the kill queue that require reassignment,
    # now we just need to add the ones that've been destroyed
    new_kill_list_additions = history.ShipHistory.prune_current_assignments(me)
    myglobals.Misc.loggit('core', 'debug', "Killing from history due to ship 8-x: " + str(new_kill_list_additions))
    if new_kill_list_additions is not None:
        kill_from_history_queue += new_kill_list_additions

    for shid in kill_from_history_queue:
        # wipe away the dingleberries
        myglobals.Misc.loggit('core', 'debug', "Killing history of shid: " + str(shid))
        myglobals.Variables.current_assignments.pop(shid, None)

    turn += 1
    game.end_turn(command_queue)
