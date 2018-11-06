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
        myglobals.Misc.loggit('core', 'info', " - processing ship.id: " + str(ship.id))
        try:
            if myglobals.Variables.current_assignments[ship.id].primary_mission == myglobals.Missions.mining:
                # if this is a new ship, we'll be in except, below
                if myglobals.Variables.current_assignments[ship.id].secondary_mission == myglobals.Missions.busy and \
                   game_map[ship.position].halite_amount == 0:
                    # we've mined all of the halite, or someone else got to it
                    # before we did here, bounce a random square
                    myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **randomly wandering**")
                    rnd_dir = random.choice([Direction.North, Direction.South, Direction.East, Direction.West])
                    myglobals.Variables.current_assignments[ship.id].destination = \
                        ship.position.directional_offset(rnd_dir)
                    
                    command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                                                                  Direction.West])))
                    continue

                elif myglobals.Variables.current_assignments[ship.id].secondary_mission == \
                        myglobals.Missions.in_transit \
                        and myglobals.Variables.current_assignments[ship.id].destination != ship.position:
                    # continuing transit for this ship to its final destination
                    myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **scooting**")

                    command_queue.append(ship.move(game_map.naive_navigate(ship,
                                                                           myglobals.Variables.
                                                                           current_assignments[ship.id].destination)))
                    continue

                elif not ship.is_full and \
                        myglobals.Variables.current_assignments[ship.id].secondary_mission == myglobals.Missions.busy \
                        and game_map[ship.position].halite_amount > 0:
                    # continuing mining here
                    myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **continuing mining** @ " +
                                          str(ship.position))
                    command_queue.append(ship.stay_still())
                    continue

                elif game_map.normalize(myglobals.Variables.current_assignments[ship.id].destination) == ship.position \
                        and not ship.is_full:
                    # mine
                    myglobals.Misc.loggit('core', 'info', " - ship.id: " + str(ship.id) + " **mining** @ " +
                                          str(ship.position))
                    myglobals.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position,
                                                                                           None, turn,
                                                                                           myglobals.Missions.mining,
                                                                                           myglobals.Missions.busy)
                    command_queue.append(ship.stay_still())
                    continue

                else:
                    # drop off the halite
                    command_queue.append(seek_n_nav.Nav.return_halite_to_shipyard(ship, me, game_map))
                    continue

        except KeyError as ke:
            # set everybody to mining, first of all
            command_queue.append(seek_n_nav.StartUp.get_initial_minimum_distance(ship, turn, ke))

        myglobals.Misc.loggit('core', 'debug', " - found and processed ship: " + str(ship.id))

    if game.turn_number <= 200 and me.halite_amount > myglobals.Const.Enough_Ore_To_Spawn and \
            not game_map[me.shipyard].is_occupied:
        myglobals.Misc.loggit('core', 'debug', " - spawning ship")
        command_queue.append(me.shipyard.spawn())

    turn += 1
    game.end_turn(command_queue)
