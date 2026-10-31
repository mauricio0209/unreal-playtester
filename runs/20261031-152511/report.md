# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:25:11.574567 |
| Actions | 150 |
| Duration | 445.3 s |
| Cost | $0.2008 |

## Confirmed bugs

### Death outside pit on sweep lane y\=\-365

Invariant `no_death_outside_pit`: The player must never die outside the pit (x 2350-2650, y 350-650).

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Sweep at X\=2166 Y\=\-357 Z\=11 PawnAlive\=false\. This is outside pit x2350\-2650 y350\-650 yet player died, breaking no\_death\_outside\_pit invariant\. Screenshot shows floor/void view consistent with falling through geometry\.

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

Invariant `side_door_opens_with_interact`: The side door opens when the player stands next to it and interacts, with or without inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to SideDoor at 200,\-700 and interacted within 150cm; ActorStates\.SideDoor remained 'closed' and screenshot shows wall, violating should\-open invariant\.

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t004_swept.png)

![After](shots/t005.png)

### Gold coin only gives 1 instead of 5

Invariant `gold_coin_worth_five`: The gold coin adds 5 to the inventory count.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Picked up GoldCoin at \~1500,0 and inventory went from 0 to 1, not 5; state shows GoldCoin missing and InventoryCount\=1 confirming delta \!\=5

Repro:

Start from a fresh level load.

1. Walk to (2000, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 3.0 s

![Before](shots/t013_reset.png)

![After](shots/t015.png)

## Rejected hypotheses

None.
