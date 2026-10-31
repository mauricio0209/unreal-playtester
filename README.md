# Unreal AI Playtester

An autonomous playtesting agent for Unreal Engine 5.8, powered by Meta's Muse models.
The model **proposes** bugs. An independent, deterministic verifier **confirms** each one
by replaying it from a clean level load and checking engine state. No LLM is involved
in verification.

> Status: planning. Built for the Meta Global AI Developer Hackathon 2026.

## Built during the hackathon

Everything in this repository was created during the hackathon, starting 2026-10-30.
See the git history for the full timeline.

## How it works

```
[Python agent] --HTTP--> [UE 5.8 PIE + Remote Control API]
   |                        BP_TestHarness: GetState, MoveTo, Interact, Jump,
   |                        LookAt, Step(seconds), Screenshot, ResetLevel
   |- Explorer: Muse Spark (Meta Model API), sees screenshot + state + spec,
   |            picks the next action or files a bug hypothesis
   |- Verifier: resets the level, replays the repro steps 3 times and evaluates
   |            deterministic predicates on GetState()
   '- Report:   repro steps, before/after screenshots, verdict
```

The game runs turn-based: it stays paused while the model thinks and advances a fixed
number of seconds per action, so model latency never affects the results.

## MVP scope

- One greybox level with 3 seeded bugs and 1 decoy:
  1. Floor without collision. Predicate: `!PawnAlive || LastZ < KillZ` (the engine destroys
     the pawn below `KillZ`, so `GetState` reports its last known Z).
  2. Door with a misaligned trigger. Predicate: door stays closed after `Interact` within 150 cm.
  3. Pickup that doesn't increment the counter. Predicate: inventory unchanged although the pickup was destroyed.
  4. Decoy: a pit that `spec.json` declares intentional. It must be rejected.
- `spec.json`: the game's invariants in natural language, each paired with a predicate.
- Muse Spark Open on Baseten as an interchangeable cheap explorer (same chat-completions interface,
  model `meta-models/muse-spark-open-1026`).

## Success criteria

1. One command runs a full session in under 10 minutes for under US$5.
2. At least 2 of the 3 seeded bugs are found and confirmed by the verifier 3 out of 3 times.
3. No non-reproducible bug is ever marked as confirmed, and the decoy is rejected.
4. Every report can be reproduced by a human from its steps alone.

## Roadmap

Submission deadline: **Wednesday, November 4, 9:00 PM ET**.

| Day | Work | Checkpoint |
|---|---|---|
| Fri, Oct 30 | Setup: repo, UE, Remote Control, MCP, Muse Code authenticated. | Done. |
| Sat, Oct 31 (2–3 h) | Greybox map + `BP_TestHarness` with `GetState`, `Step`, `MoveTo`, `Screenshot` and `ResetLevel`, driven from Python. | Done Fri night: the pawn moves over HTTP and replays are bit-identical across PIE sessions. |
| Sun, Nov 1 (2–3 h) | 3 seeded bugs + 1 decoy, `spec.json`, replay verifier (no LLM). | The verifier confirms the bugs from hand-written repro steps. |
| Mon, Nov 2 (full day) | Agent loop with Muse Spark + report. | Success criteria 1–3. |
| Tue, Nov 3 (full day) | Muse Spark Open on Baseten as alternate explorer, polish, README, record footage. | Feature freeze at 18:00. |
| Wed, Nov 4 | Edit the 3-minute video, submit before noon, post on X. | No new code. |

## Muse Code usage

Well-scoped tasks with a clear contract (for example the verifier's predicate functions) are
delegated to Muse Code headlessly, up to three lanes in parallel, then reviewed before commit:

```bash
scripts/muse-lane.sh <lane> tasks/<task>.md                     # muse-spark-1.3-contributor
scripts/muse-lane.sh <lane> tasks/<task>.md muse-wonder-1.0     # harder multi-file tasks
```

Each lane runs in its own git worktree under bubblewrap with `/mnt/c` hidden, so Muse never
sees `.env` (Muse's own sandbox does not restrict reads). That is what makes the cheaper
contributor tier safe here: the repository is public anyway.

Each delegated task's prompt lives in `tasks/`, and its commit message says
`Delegated to Muse Code`. Design, the harness and the verifier's replay logic stay hand-reviewed.

## Setup

```bash
cp .env.example .env   # then fill in your keys
```

## Repository layout

- `agent/`: Python agent, verifier and report (coming next).
- `unreal/PlaytestArena/`: UE 5.8 project with the greybox level, seeded bugs and `BP_TestHarness`.
