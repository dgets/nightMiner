# nightMiner

**nightMiner** is a Halite III bot that is basically just a rewrite of the
previous incarnation, [d4m0Turtle](https://github.com/dgets/d4m0Turtle).
Rewrite was started with the objective of utilizing more modular OOP, along
with proper OO development (at least where I'm able to model it properly, with
my current level of familiarity-- hopefully pushing the bounds on this a
little bit).  There was also a bit of an issue with trying to incorporate too
many features at once, so I'm trying to stick to a more linear development
pattern, implementing each piece at a time here.

The basic idea is to get a bot functional with basic mining, as well as any
offensive and defensive capabilities that we might be able to implement.  Not
really sure on how those are going to compare to the previous _Halite II_
capabilities, I haven't really looked that far yet.  After basic (dumb)
decision making is done on these, and things are looking good, we can look
into incorporating some deep learning in order to better determine when these
options are going to be best implemented.  We've got a way to go before
anything like this is possible, though.

God, it'd sure be nice to be using unit tests, wouldn't it?

## Halite III

For more information on the contest, see the 
[Halite III coding contest web site](http://Halite.io).

For an overview from the level of the ISS, Halite is an artificial
intelligence coding challenge, built around coding bots in a virtual
environment to 'mine' _halite ore_ for usage for movement, creating more
ships/turtles, and determining which player has won in any particular
simulation.

