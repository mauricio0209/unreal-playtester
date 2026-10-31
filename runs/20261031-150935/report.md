# Session report

3 confirmed bugs, 1 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:09:35.157767 |
| Actions | 151 |
| Duration | 452.5 s |
| Cost | $0.1855 |

## Confirmed bugs

### Death outside pit region at \(2166, \-357\)

Invariant `floor_solid_no_death_outside_pit`: Outside the pit region the player must never die.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player died at X\=2166 Y\=\-357 Z\=11 which is outside pit \(2350\-2650,350\-650\) but PawnAlive became false\. Outside pit player must never die\.

Repro:

Start from a fresh level load.

1. Walk to (-466, -365)
2. Let the game run for 2.0 s
3. Walk to (3456, -365)
4. Let the game run for 2.0 s
5. Walk to (3456, -365)
6. Let the game run for 2.0 s
7. Walk to (3456, -365)
8. Let the game run for 2.0 s

![Before](shots/t001_lane4.png)

![After](shots/t001.png)

### Side door fails to open on interact

Invariant `side_door_opens_on_interact`: Interacting with the side door from up close opens it regardless of inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: After walk\_to \(156,\-686\) within 46cm of SideDoor \(200,\-700\) and interact, ActorStates\.SideDoor still 'closed' despite spec requiring open regardless of inventory\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t003_swept.png)

![After](shots/t004.png)

### Gold coin only gives 1 instead of 5

Invariant `gold_coin_worth_five`: Picking up the gold coin adds exactly 5 to inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to gold coin at 1500,0: GoldCoin went from present to missing but InventoryCount is 1 not 5, delta \!\=5 breaks gold\_coin\_worth\_five despite auto\-check saying holds

Repro:

Start from a fresh level load.

1. Walk to (1500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s

![Before](shots/t006_reset.png)

![After](shots/t008.png)

## Rejected hypotheses

### Pit fall does not kill player

Invariant `pit_ends_attempt`: Falling into the pit region and below the floor must end the attempt.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Player at \(2579,533,\-417\) inside pit X2350\-2650 Y350\-650 below floor Z<0 with PawnAlive true and bIsFalling true\. Should have ended attempt but still alive\.

Repro:

Start from a fresh level load.

1. Walk to (-466, 535)
2. Let the game run for 2.0 s
3. Walk to (3456, 535)
4. Let the game run for 2.0 s
5. Walk to (3456, 535)
6. Let the game run for 2.0 s
7. Walk to (3456, 535)
8. Let the game run for 2.0 s

![Before](shots/t002_lane1.png)

![After](shots/t002.png)
