# Session report

2 confirmed bugs, 0 rejected hypotheses.

## Session

| Field | Value |
| --- | --- |
| Model |  |
| Started | 2026-10-31T11:22:29.601523 |
| Actions | 40 |
| Duration | 187.1 s |
| Cost | $0.0 |

## Confirmed bugs

### door\_needs\_own\_key broken \(scripted check\)

Invariant `door_needs_own_key`: A door opens only if the player is carrying the key of the same color.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object BlueDoor episode broke door\_needs\_own\_key\.

Repro:

Start from a fresh level load.

1. Walk to (3500, 0)
2. Let the game run for 6.833333333333333 s
3. Press Interact

![Replay](videos/bug1.gif)

[Replay video (MP4)](videos/bug1.mp4)

![Before](shots/baseline_000_before.png)

![After](shots/baseline_000_after.png)

### gem\_worth\_three broken \(scripted check\)

Invariant `gem_worth_three`: A gem bundle adds 3 to the inventory.

Verdict: Confirmed (3/3 runs reproduced)

Runs: True, True, True

Reason: bug reproduced in all 3 runs

Hypothesis: Scripted object GemBundle episode broke gem\_worth\_three\.

Repro:

Start from a fresh level load.

1. Walk to (2000, 300)
2. Let the game run for 4.370624736026114 s

![Replay](videos/bug2.gif)

[Replay video (MP4)](videos/bug2.mp4)

![Before](shots/baseline_003_before.png)

![After](shots/baseline_003_after.png)

## Rejected hypotheses

None.
