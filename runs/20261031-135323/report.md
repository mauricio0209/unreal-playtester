# Session report

3 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model | meta-models/muse-spark-open-1026 |
| Started | 2026-10-31T13:53:23.205135 |
| Actions | 131 |
| Duration | 437.6 s |
| Cost | $0.2726 |

## Confirmed bugs

### RedDoor did not open with RedKey

Invariant `red_door_opens_with_own_key`: Interacting with RedDoor up close while carrying RedKey must open it.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Collected RedKey \(state missing/carried\) and interacted within 44cm of RedDoor at 2200,\-700, but RedDoor state stayed closed and view shows blocked wall, violating must\-open invariant\.

Repro:

Start from a fresh level load.

1. Walk to (1500, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Walk to (2200, -700)
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Press Interact
9. Let the game run for 1.0 s

![Before](shots/t004_reset.png)

![After](shots/t006.png)

### GemBundle gave 1 instead of 3

Invariant `gem_bundle_worth_three`: GemBundle adds exactly 3 to inventory when collected.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Walked to GemBundle at 2000,300; it disappeared and inventory went from 0 to 1, not 3 as required\.

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 1.0 s
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s

![Before](shots/t010_reset.png)

![After](shots/t012.png)

### BlueDoor opened without collecting BlueKey

Invariant `blue_door_needs_own_key`: BlueDoor must not open while BlueKey is still present.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Interacted at BlueDoor \(3455,0\) with inventory 0; state shows BlueDoor open while BlueKey still present at 3000,\-500, so door opened without its key\.

Repro:

Start from a fresh level load.

1. Let the game run for 0.5 s
2. Walk to (3500, 0)
3. Let the game run for 1.0 s
4. Let the game run for 1.0 s
5. Let the game run for 1.0 s
6. Let the game run for 1.0 s
7. Let the game run for 1.0 s
8. Let the game run for 1.0 s
9. Press Interact
10. Let the game run for 1.0 s

![Before](shots/t014_reset.png)

![After](shots/t017.png)

## Rejected hypotheses

None.
