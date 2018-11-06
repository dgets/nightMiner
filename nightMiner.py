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
from custom_routines import myglobals, history

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
    # speed, again (see if there are any places to implement anything like
    # this with my own structs)
    game_map = game.game_map

    myglobals.Misc.loggit('core', 'info', " - initializing 'command_queue'")
    command_queue = []

    myglobals.Misc.loggit('core', 'debug', " -* me.get_ships() dump: " + str(me.get_ships()))

    for ship in me.get_ships():
        try:
            if myglobals.Variables.current_assignments[ship.id].primary_mission == 'mining':
                # if this is a new ship, we'll be in except, below
                if turn <= (myglobals.Variables.current_assignments[ship.id].turnstamp + 5):  # wander moar
                    command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                                                                  Direction.West])))
                    continue
                elif game_map(ship.position).halite_amount > 0:
                    # mine
                    command_queue.append(ship.stay_still())
                else:
                    command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                                                                  Direction.West])))
                    continue

        except:
            # set everybody to mining, first of all
            myglobals.Variables.current_assignments[ship.id] = history.ShipHistory(ship.id, ship.position, None, turn,
                                                                                   myglobals.Missions.mining,
                                                                                   myglobals.Missions.in_transit)
            command_queue.append(ship.move(random.choice([Direction.North, Direction.South, Direction.East,
                                                          Direction.West])))

        if (game.turn_number <= 200) and (me.halite_amount > myglobals.Const.Enough_Ore_To_Spawn) and \
                (not game_map[me.shipyard].is_occupied):
            command_queue.append(me.shipyard.spawn())

        turn += 1

        game.end_turn(command_queue)
