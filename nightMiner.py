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

from hlt import constants

from custom_routines import history, seek_n_nav, core_processing, analytics
from custom_routines import myglobals as glo

# --==++** GAME BEGIN **++==--

game = core_processing.Core.original_preprocessing()

# unable to properly set in glo
Max_Scuttle_Time = constants.MAX_TURNS - 25  # TODO: tweak for efficiency

turn: int = 0

# --==++** PRIMARY GAME LOOP **++==--
while True:
    # set local versions of costly lookups
    game_map = game.game_map
    me = game.me  # keeps things speedier

    # costly preprocessing time
    core_processing.Core.per_turn_preprocessing(game, me, turn)

    # initialize per-turn queues
    command_queue = []
    kill_from_history_queue = []
    new_kill_list_additions = []
    glo.Variables.considered_destinations = []

    # clear up other potential crap
    c_queue_addition = None

    if glo.Const.FEATURES['scuttle']:
        glo.Misc.loggit('core', 'debug', " Making sure turn (" + str(turn) + " <= " +
                        str(Max_Scuttle_Time - len(me.get_ships())) + ")")

    # if not turn > (500 - game_map.width - (len(me.get_ships()) * 2)):
    if not glo.Const.FEATURES['scuttle'] or not turn > (Max_Scuttle_Time - len(me.get_ships())):
        # until glo issues are fixed
        # we're not in the scuttle time crunch yet
        for ship in me.get_ships():
            kill_from_history_queue = []

            glo.Misc.loggit('core', 'info', " - processing ship.id: " + str(ship.id))
            glo.Misc.log_w_shid('seek', 'debug', ship.id, "Present cell's halite: " +
                                str(game_map[ship.position].halite_amount))

            try:
                if glo.Const.FEATURES['early_blockade']:
                    # if this is a new ship, we'll be in the except, below
                    if glo.Variables.early_blockade_processing and \
                            glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.early_blockade:
                        glo.Misc.log_w_shid('core', 'info', ship.id, " entering early_blockade()")

                        command_queue.append(seek_n_nav.Offense.early_blockade(me, ship, game, game_map, turn))

                        continue

                if glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.mining:
                    glo.Misc.loggit('core', 'debug', " - ship.id " + str(ship.id) +
                                    " in primary mining conditional")
                    c_queue_addition = core_processing.Core.primary_mission_mining(ship, game_map, me, turn)

                    if c_queue_addition is not None:
                        command_queue.append(c_queue_addition)
                    else:
                        glo.Misc.loggit('core', 'debug', " -* added ship.id: " + str(ship.id) + " to kill list")
                        kill_from_history_queue.append(ship.id)

                    continue

                # we've transited to the shipyard/dropoff
                elif glo.Variables.current_assignments[ship.id].secondary_mission == \
                        glo.Missions.in_transit \
                        and glo.Variables.current_assignments[ship.id].primary_mission == \
                        glo.Missions.dropoff and \
                        glo.Variables.current_assignments[ship.id].destination == ship.position and \
                        ship.halite_amount > 0:
                    # make the drop
                    glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " making drop @ " +
                                    str(ship.position))
                    kill_from_history_queue.append(ship.id)

                    # now we've got to wipe that from the current_assignments
                    # to make sure that it's properly reassigned the next time
                    # around
                    if glo.Variables.current_assignments.pop(ship.id, None) is None:
                        glo.Misc.loggit('core', 'debug', " -* ship.id: " + str(ship.id) + " was found in an " +
                                        "invalid state (no current_assignments entry)!")  # should throw exception

                    continue

                elif game_map.normalize(glo.Variables.current_assignments[ship.id].destination) == ship.position \
                        and glo.Variables.current_assignments[ship.id].primary_mission != \
                        glo.Missions.dropoff and not ship.is_full:
                    # mining time
                    glo.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **mining** @ " +
                                    str(ship.position))
                    glo.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,

                                                                                     None, turn,
                                                                                     glo.Missions.mining,
                                                                                     glo.Missions.busy)
                    command_queue.append(ship.stay_still())
                    continue

                elif glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.dropoff \
                        and ship.position != me.shipyard.position:
                    # head to drop off the halite & drop it off
                    glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " in **transit to drop**")
                    command_queue.append(seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map, turn))
                    continue

                # dropped the halite
                elif glo.Variables.current_assignments[ship.id].primary_mission == glo.Missions.dropoff \
                        and ship.position == me.shipyard.position:
                    glo.Misc.loggit('core', 'info', " -* ship.id: " + str(ship.id) + " DROPPED the BONE")

                    try:
                        command_queue.append(
                            ship.move(seek_n_nav.StartUp.get_initial_minimum_distance(ship, me, game_map, turn)))
                    except:
                        # not so sure this code path is utilized any more
                        command_queue.append(ship.move(glo.Misc.r_dir_choice()))

                    continue

            except KeyError:
                if glo.Const.FEATURES['initial_scoot']:
                    # set everybody to mining (after getting distance), first of all
                    command_queue.append(seek_n_nav.StartUp.get_initial_minimum_distance(ship, me, game_map, turn))
                    tmp_msg = " for initial_scoot"
                else:
                    glo.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                                     ship.position.directional_offset(
                                                                                         analytics.HaliteAnalysis.
                                                                                             find_best_dir(ship,
                                                                                                           game_map)),
                                                                                     turn, glo.Missions.mining,
                                                                                     glo.Missions.in_transit)

                    if not ship.position.directional_offset(analytics.HaliteAnalysis.find_best_dir(ship, game_map)) in \
                           glo.Variables.considered_destinations:
                        glo.Variables.considered_destinations.append(
                            ship.position.directional_offset(analytics.HaliteAnalysis.find_best_dir(ship, game_map)))

                        command_queue.append(seek_n_nav.Nav.scoot(ship, game_map))
                    else:
                        command_queue.append(seek_n_nav.Nav.generate_profitable_offset(ship, game_map))

                    tmp_msg = " for immediate mining"

            glo.Misc.loggit('core', 'debug', " - found and processed ship: " + str(ship.id) + tmp_msg)

        if turn <= 250 and me.halite_amount >= glo.Const.Enough_Ore_To_Spawn  \
                and not game_map[me.shipyard].is_occupied:
            glo.Misc.loggit('core', 'debug', " - spawning ship")
            command_queue.append(me.shipyard.spawn())

        # maintain the current_assignments as best we can here...
        glo.Misc.loggit('core', 'debug', "Killing from history for reassignment: " + str(kill_from_history_queue))

        # we've already got ships in the kill queue that require reassignment,
        # now we just need to add the ones that've been destroyed
        new_kill_list_additions = history.ShipHistory.prune_current_assignments(me)
        glo.Misc.loggit('core', 'debug', "Killing from history due to ship 8-x: " + str(new_kill_list_additions))
        if new_kill_list_additions is not None:
            kill_from_history_queue += new_kill_list_additions

    else:
        glo.Misc.loggit('core', 'debug', "Entered the scuttle race clause")
        # scuttle everybody home and avoid the clusterfsck by blockade or pringles
        command_queue = core_processing.Core.scuttle_for_finish(me, game_map, turn)
        # command_queue = seek_n_nav.Nav.ScuttleSupport.scuttle_for_finish(me, game_map, turn)

    turn += 1
    glo.Variables.considered_destinations = []
    game.end_turn(command_queue)
