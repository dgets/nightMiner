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

import hlt
from hlt import Direction
from custom_routines import myglobals, history, seek_n_nav

# --==++** GAME BEGIN **++==--

game = hlt.Game()

# really good place to do computationally expensive preprocessing *cough*

game.ready("nightMiner")

myglobals.Misc.loggit('any', 'info', "Hatched and swimming! Player ID is {}.".format(game.my_id))

# for turnstamps
turn = 0

# --==++** PRIMARY GAME LOOP **++==--
while True:
    myglobals.Misc.loggit('core', 'info', " - updating frame")
    game.update_frame()

    myglobals.Misc.loggit('core', 'info', " - updating 'me'")
    # keeps things speedier
    me = game.me
    myglobals.Misc.loggit('core', 'info', " - updating 'game_map'")
    game_map = game.game_map

    myglobals.Misc.loggit('core', 'info', " - initializing 'command_queue'")
    command_queue = []

    myglobals.Misc.loggit('core', 'debug', " -* me.get_ships() dump: " + str(me.get_ships()))

    for ship in me.get_ships():
        myglobals.Misc.loggit('core', 'debug', " - processing ship.id: " + str(ship.id))
        try:
            if myglobals.Variables.current_assignments[ship.id].primary_mission == myglobals.Missions.mining:
                # if this is a new ship, we'll be in except, below
                #if turn < (myglobals.Variables.current_assignments[ship.id].turnstamp + 2):  # wander moar
                if myglobals.Variables.current_assignments[ship.id].secondary_mission == myglobals.Missions.in_transit \
                        and myglobals.Variables.current_assignments[ship.id].destination != ship.position:
                    myglobals.Misc.loggit('core', 'debug', " - ship.id: " + str(ship.id) + " **scooting**")
                    #command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                    #                                              Direction.West])))
                    command_queue.append(ship.move(game_map.naive_navigate(ship,
                                                                           myglobals.Variables.
                                                                           current_assignments[ship.id].destination)))
                    continue
                #elif game_map(ship.position).halite_amount > 0 and not ship.is_full:
                elif game_map.normalize(myglobals.Variables.current_assignments[ship.id].destination) == ship.position:
                    # mine
                    myglobals.Misc.loggit('core', 'debug', " - ship.id: " + str(ship.id) + " **mining** @ " +
                                          str(ship.position))
                    myglobals.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                                           None, turn,
                                                                                           myglobals.Missions.mining,
                                                                                           None)
                    command_queue.append(ship.stay_still())
                    continue
                elif game_map(ship.position).halite_amount == 0 and not ship.is_full:
                    myglobals.Misc.loggit('core', 'debug', " - ship.id: " + str(ship.id) + " **wandering** a step to " +
                                          "find more halite")
                    command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                                                                  Direction.West])))
                    continue
                else:
                    # drop off the halite
                    myglobals.Misc.loggit('core', 'debug', " - ship.id: " + str(ship.id) +
                                          " **returning to shipyard** at " + str(me.shipyard.position))
                    command_queue.append(ship.move(game_map.naive_navigate(ship, me.shipyard.position)))
                    #command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                    #                                              Direction.West])))
                    continue

        except:
            # set everybody to mining, first of all
            myglobals.Misc.loggit('core', 'debug', " - fell into except; **setting new ship id: " + str(ship.id) +
                                  " to mining**")
            myglobals.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                                   seek_n_nav.Nav.
                                                                                   generate_random_offset(
                                                                                       ship.position
                                                                                   ), turn,
                                                                                   myglobals.Missions.mining,
                                                                                   myglobals.Missions.in_transit)
            command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                                                          Direction.West])))

        myglobals.Misc.loggit('core', 'debug', " - found and processed ship: " + str(ship.id))

    if game.turn_number <= 200 and me.halite_amount > myglobals.Const.Enough_Ore_To_Spawn and \
            not game_map[me.shipyard].is_occupied:
        myglobals.Misc.loggit('core', 'debug', " - spawning ship")
        command_queue.append(me.shipyard.spawn())

    turn += 1
    game.end_turn(command_queue)
