# Session report

3 confirmed bugs, 1 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T15:58:33.489478 |
| Actions | 146 |
| Duration | 308.8 s |
| Cost | $0.0438 |

## Confirmed bugs

### Fell out of world at middle hall floor hole

Invariant `no_fall_out_of_world`: The player pawn must never fall out of the world: die, drop below KillZ, or end up more than 2 m below the floor (Z < -200), except through a region the design marks as intentional. A fall anywhere else is a level geometry bug.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player died at X\=2179 Y\=\-489 Z\=6 outside intentional decoy pit, indicating missing collision/hole in walkable area

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

### Pickup1 collected but inventory not incremented

Invariant `pickup_counts`: Collecting Pickup1 (it disappears from the world) must increase InventoryCount. If it is gone but the count is unchanged since it was last present, the pickup was lost.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to Pickup1 at \(1000,500\) \- state shows Pickup1 missing and InventoryCount remains 0, violating pickup\_counts invariant

Repro:

Start from a fresh level load.

1. Walk to (1000, 500)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s

![Before](shots/t004_reset.png)

![After](shots/t006.png)

### Door1 did not open after interact within 150 cm

Invariant `door_opens`: Interacting with Door1 while standing within 150 cm of it must open the door. If the door is still not open after a later step, the interaction is broken.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Player at 3455,0 is 45cm from Door1 at 3500,0, interacted and stepped, but Objects state remains closed and view shows wall unchanged, so predicate door\_stays\_closed\_after\_interact violated

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

![Before](shots/t008_reset.png)

![After](shots/t010.png)

## Rejected hypotheses

### Door2 did not open after interact within 150 cm

Invariant `door2_opens`: Interacting with Door2 while standing within 150 cm of it must open the door. If the door is still not open after a later step, the interaction is broken.

Verdict: Flaky, not confirmed (2/3 runs reproduced)

Runs: True, False, True

Reason: bug reproduced in 2 of 3 runs

Hypothesis: Player at 156,\-686 within 46 cm of Door2 at 200,\-700 interacted but state remains closed after step, so interaction is broken despite automatic check claiming holds

Repro:

Start from a fresh level load.

1. Walk to (200, -700)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Press Interact
6. Let the game run for 1.0 s

![Before](shots/t006_reset.png)

![After](shots/t008.png)
