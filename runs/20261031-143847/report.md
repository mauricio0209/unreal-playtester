# Session report

2 confirmed bugs, 1 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T14:38:47.368758 |
| Actions | 126 |
| Duration | 420.1 s |
| Cost | $0.2295 |

## Confirmed bugs

### Side door stayed closed after interact

Invariant `side_door_opens_when_used`: The side door is never locked: standing next to it and interacting opens it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at 156,\-686 within 50cm of SideDoor at 200,\-700 interacted but ActorStates\.SideDoor remained closed violating never\-locked requirement

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Press Interact
5. Let the game run for 1.0 s

![Before](shots/t000.png)

![After](shots/t002.png)

### Gold coin gave \+1 instead of \+5

Invariant `gold_coin_worth_five`: The gold coin is worth 5 when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Inventory went from 2 to 3 after collecting GoldCoin \(present\-\>missing\) delta\=1 not 5, so gold\_coin\_worth\_five is actually violated despite automatic check saying holds\.

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (1500, 0)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s

![Before](shots/t002_reset.png)

![After](shots/t005.png)

## Rejected hypotheses

### Exit door opened without gold coin

Invariant `exit_door_needs_gold_coin`: The exit door opens only for a player carrying the gold coin.

Verdict: Rejected (0/3 runs reproduced)

Runs: False, False, False

Reason: bug reproduced in 0 of 3 runs

Hypothesis: Walked to ExitDoor \(3500,0\) and interacted with InventoryCount\=1 and GoldCoin missing, yet ExitDoor state became open\. Invariant requires GoldCoin carried \(state null after collection\) to open\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Press Interact
9. Let the game run for 1.0 s

![Before](shots/t013_reset.png)

![After](shots/t015.png)
