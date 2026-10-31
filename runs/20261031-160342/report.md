# Session report

3 confirmed bugs, 1 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T16:03:42.492040 |
| Actions | 164 |
| Duration | 372.8 s |
| Cost | $0.0827 |

## Confirmed bugs

### Fell out of world outside intentional pit

Invariant `no_fall_out_of_world`: The player pawn must never fall out of the world: die, drop below KillZ, or end up more than 2 m below the floor (Z < -200), except through a region the design marks as intentional. A fall anywhere else is a level geometry bug.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Sweep lane y\=\-500 fell at X\=2179 Y\=\-489 Z\=6 PawnAlive false outside decoy\_pit region, Z below floor threshold, indicates hole in floor geometry

Repro:

Start from a fresh level load.

1. Walk to (-400, -500)
2. Let the game run for 2.0 s
3. Walk to (4900, -500)
4. Let the game run for 2.0 s
5. Walk to (4900, -500)
6. Let the game run for 2.0 s
7. Walk to (4900, -500)
8. Let the game run for 2.0 s

![Before](shots/t001_lane7.png)

![After](shots/t001.png)

### Door1 does not open after interact within range

Invariant `door_opens`: Interacting with Door1 while standing within 150 cm of it must open the door. If the door is still not open after a later step, the interaction is broken.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: At \(3455,0\) 45cm from Door1 \(3500,0\) performed interact and stepped, but Objects\.Door1 remains 'closed' and view shows wall, violating door\_opens requirement

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t010_reset.png)

![After](shots/t012.png)

### Pickup1 disappears without increasing InventoryCount

Invariant `pickup_counts`: Collecting Pickup1 (it disappears from the world) must increase InventoryCount. If it is gone but the count is unchanged since it was last present, the pickup was lost.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player moved to Pickup1 location \(1000,500\) \- state shows Objects\.Pickup1\=missing but InventoryCount\=0 same as before collection\. Expected count to increase by 1 when pickup disappears\.

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s

![Before](shots/t014_reset.png)

![After](shots/t016.png)

## Rejected hypotheses

### Door2 stays closed after in\-range interact

Invariant `door2_opens`: Interacting with Door2 while standing within 150 cm of it must open the door. If the door is still not open after a later step, the interaction is broken.

Verdict: Flaky, not confirmed (2/3 runs reproduced)

Runs: True, False, True

Reason: bug reproduced in 2 of 3 runs

Hypothesis: At \(156,\-686\) distance \~46cm to Door2 at \(200,\-700\) well within 150cm, after walk\_to \+ interact \+ step Door2 state is still closed, violating must\-open rule\. Auto\-check incorrectly reported holds\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Press Interact
6. Let the game run for 1.0 s

![Before](shots/t012_reset.png)

![After](shots/t014.png)
