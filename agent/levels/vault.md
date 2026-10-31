# The Vault: design notes

The Vault is a single long hall that ends at a heavy door leading to the treasure room. The
player starts at the west end. There are no enemies; the level is about keys and loot.

## Doors and keys

There are three doors, green, red and blue, and one key of each color lying on the floor.
The player picks up a key by walking over it. Keys go on the key ring: they are not loot
and do not change the inventory count.

Every door starts closed and locked. To open a door the player stands next to it and
interacts with it. A door opens only if the player is carrying the key of the same color;
otherwise it stays shut. A key opens only the door of its own color. The blue door is the
heavy door to the treasure room.

Doors play a deep rumble when they open and glow faintly while locked.

## Loot

Loot is collected by walking over it and adds to the inventory count:

- a coin is worth 1,
- a gem bundle is worth 3.

Loot never disappears without being added to the inventory.

## Hazards

There is an open pit in the middle of the hall. Falling into it is intended and simply
ends the attempt.
