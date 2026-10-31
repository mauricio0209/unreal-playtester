# The Armory: design notes

The Armory is three halls in a row along +X. The player starts in the west hall at (0, 0).
The east end of the middle hall is closed by the exit door, which leads to the third hall.
Coordinates are in centimeters.

## Doors

- The side door, in the west hall, is a plain service door. It is never locked: anyone who
  stands next to it and interacts with it opens it, with or without anything in their pockets.
- The exit door, at the east end of the middle hall, is the armory's checkpoint. It opens only
  for a player carrying the gold coin, which doubles as the exit pass; without the gold coin,
  interacting with it does nothing.

Doors swing open with a metallic clang.

## Coins

Coins are collected by walking over them and add to the inventory count:

- the silver coin is worth 2,
- the gold coin is worth 5.

Picking up the gold coin also grants the exit pass; it still counts toward the inventory.

## Floor and hazards

The middle hall has an open pit, from x 2350 to 2650 and y 350 to 650. Falling into the pit
is intended and ends the attempt.

Everywhere else the floor is solid: the player must never fall through the floor, die, or end
up below the floor outside the pit.

Torches line the walls for atmosphere.
