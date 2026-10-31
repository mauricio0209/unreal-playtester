# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | muse-spark-1.3-contributor |
| Started | 2026-10-31T13:58:35.062236 |
| Actions | 124 |
| Duration | 487.7 s |
| Cost | $0.3656 |

## Confirmed bugs

### Red door stays closed with red key

Invariant `red_door_opens_with_key`: Interacting next to the red door while carrying the red key opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up RedKey \(missing, inventory 0\) then walked to RedDoor within \~44cm and interacted, but RedDoor remained closed, so carrying key did not open it\.

Repro:

Start from a fresh level load.

1. Walk to (1500, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 3.0 s
6. Walk to (2200, -700)
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Let the game run for 3.0 s
10. Press Interact
11. Let the game run for 1.0 s

![Before](shots/t015_reset.png)

![After](shots/t019.png)

### Gem bundle only gave 1 inventory

Invariant `gem_worth_three`: A gem bundle is worth 3 and never disappears without being added to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked over GemBundle at \~2000,300 and it disappeared but InventoryCount is 1 instead of 3, violating worth\-3 rule

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 2.0 s

![Before](shots/t024_reset.png)

![After](shots/t026.png)

### Red door opened without red key

Invariant `door_opens_without_own_key`: A door opens only if the player is carrying the key of the same color.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up green key then interacted at red door and it opened while RedKey state is still present, so door opened without its own key

Repro:

Start from a fresh level load.

1. Walk to (300, 700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 2.0 s
5. Walk to (1000, 500)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 2.0 s
9. Walk to (2200, -700)
10. Let the game run for 1.0 s
11. Let the game run for 1.0 s
12. Let the game run for 1.0 s
13. Press Interact
14. Let the game run for 1.0 s

![Before](shots/t026_reset.png)

![After](shots/t030.png)

## Rejected hypotheses

None.
