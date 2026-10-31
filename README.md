# Unreal AI Playtester

An autonomous playtesting agent for Unreal Engine 5.8, powered by Meta's Muse models.
The model **proposes** bugs. An independent, deterministic verifier **confirms** each one
by replaying it from a clean level load and checking engine state. No LLM is involved
in verification.

> Status: working end to end. Built for the Meta Global AI Developer Hackathon 2026.

## Built during the hackathon

Everything in this repository was created during the hackathon, starting 2026-10-30.
The git history has every step; early commit messages are in Spanish, so here is the short
version in English.

### Build log

- **Oct 30, setup.** UE 5.8 project with the Remote Control API and the editor MCP server.
  First Muse Spark vision call; `reasoning` tokens count against `max_tokens`, so the agent
  uses large budgets.
- **Oct 30, harness.** `BP_TestHarness` built entirely through the MCP Blueprint tools. Fixed
  30 fps frame rate: the same replay gives bit-identical positions across PIE sessions, which
  is what makes 3/3 verification meaningful.
- **Oct 30, Muse Code isolation.** A canary test showed Muse Code's sandbox does not restrict
  reads, so every delegated lane runs under bubblewrap in its own worktree with `.env` invisible.
- **Oct 30, seeded bugs.** The first checkpoint run confirmed the decoy pit as a bug: the pawn
  kept moving under the floor and died outside the pit. The harness now reports where the pawn
  went through the floor, and the pit region has a capsule-radius margin.
- **Oct 30, agent loop.** Repro steps are never written by the model: they are the actions
  actually executed since the last reset. First sessions found 1–2 bugs; fixes were remembering
  filed bugs, batching up to 4 actions per turn, marking vanished objects as `missing`, declaring
  the walkable area in the spec, `reasoning_effort: low` (8 s to 3.5 s per turn) and a 4x4 m
  broken floor (sweep lanes kept landing on the edges of a 2x2 m one).
- **Oct 30, falling-alive fix.** The agent correctly reported a pawn still falling under the
  floor, but the predicate only counted death or KillZ, so a real bug was rejected. Being
  2 m under the floor now counts, measured at the floor-crossing point.
- **Oct 31, intermittent bug.** `Door2` fails only on odd level loads. Three consecutive replays
  always disagree, so the verifier never confirms it and the report labels it flaky.
- **Oct 31, open weights and video.** Muse Spark Open on Baseten as a drop-in explorer, a
  10-session benchmark, and a replay video per confirmed bug.

## How it works

```
[Python agent] --HTTP--> [UE 5.8 PIE + Remote Control API]
   |                        BP_TestHarness: GetState, MoveTo, Interact, Jump,
   |                        LookAt, Step(seconds), Screenshot, ResetLevel, SetCamera
   |- Sweep:    scripted lanes 2 m apart cover the walkable area; on any fall
   |            they stop and hand the judgment to the explorer
   |- Explorer: Muse Spark (Meta Model API), sees screenshot + state + spec,
   |            judges falls against the spec, exercises every object and
   |            files bug hypotheses
   |- Verifier: resets the level, replays the repro steps 3 times and evaluates
   |            deterministic predicates on GetState()
   '- Report:   repro steps, before/after screenshots, verdict
```

The game runs turn-based: it stays paused while the model thinks and advances a fixed
number of seconds per action, so model latency never affects the results.

## MVP scope

- One greybox level with 3 seeded bugs and 1 decoy:
  1. Floor without collision. Predicate: `!PawnAlive || LastZ < KillZ || LastZ < -200`, outside
     the intentional regions in `spec.json`. The engine destroys the pawn below `KillZ`, so `GetState` reports its
     last known Z and the XY where it went through the floor.
  2. Door with a misaligned trigger. Predicate: door stays closed after `Interact` within 150 cm.
  3. Pickup that doesn't increment the counter. Predicate: inventory unchanged although the pickup was destroyed.
  4. Decoy: a pit that `spec.json` declares intentional. It must be rejected.
  5. Intermittent: `Door2` fails only on odd level loads. It must never be confirmed.
- `spec.json`: the game's invariants in natural language, each paired with a predicate.
- Muse Spark Open on Baseten as an interchangeable cheap explorer (same chat-completions interface,
  model `meta-models/muse-spark-open-1026`).

## Success criteria

1. One command runs a full session in under 10 minutes for under US$5.
2. At least 2 of the 3 seeded bugs are found and confirmed by the verifier 3 out of 3 times.
3. No non-reproducible bug is ever marked as confirmed, and the decoy is rejected.
4. Every report can be reproduced by a human from its steps alone.

## Results

Each session is one `python3 agent/session.py` run from a fresh PIE. Summaries come from
`python3 scripts/summarize_runs.py . runs/<list>.txt`.

**Benchmark 1** (Oct 31, 5 sessions per provider, alternating):

| Explorer | Sessions with ≥2 bugs | All 3 bugs | False positives | Intermittent door confirmed | Mean time | Mean cost |
|---|---|---|---|---|---|---|
| Muse Spark 1.3 (Meta Model API) | 5/5 | 3/5 | 0 | never | 7.0 min | US$0.19 |
| Muse Spark Open (Baseten) | 5/5 | 3/5 | 0 | never | 7.6 min | US$0.17 |

**Benchmark 2** (Oct 31, 3 sessions per provider, final prompt that tests each object in its
own attempt, replay video on):

| Explorer | Sessions with ≥2 bugs | All 3 bugs | False positives | Intermittent door confirmed | Mean time | Mean cost |
|---|---|---|---|---|---|---|
| Muse Spark 1.3 (Meta Model API) | 3/3 | 0/3 | 0 | never | 6.9 min | US$0.20 |
| Muse Spark Open (Baseten) | 3/3 | 0/3 | 0 | never | 8.5 min | US$0.09 |

Every session in both benchmarks stayed under 9 minutes and US$0.21. In benchmark 2 every
session confirmed the door and the pickup but missed the floor without collision: testing
objects first left less of the budget for sweeping the map, and the sweep lanes missed the hole.

## Roadmap

Submission deadline: **Wednesday, November 4, 9:00 PM ET**.

| Day | Work | Checkpoint |
|---|---|---|
| Fri, Oct 30 | Setup: repo, UE, Remote Control, MCP, Muse Code authenticated. | Done. |
| Sat, Oct 31 (2–3 h) | Greybox map + `BP_TestHarness` with `GetState`, `Step`, `MoveTo`, `Screenshot` and `ResetLevel`, driven from Python. | Done Fri night: the pawn moves over HTTP and replays are bit-identical across PIE sessions. |
| Sun, Nov 1 (2–3 h) | 3 seeded bugs + 1 decoy, `spec.json`, replay verifier (no LLM). | Done Fri night: `agent/check_seeded.py` confirms all 3 bugs 3/3 and rejects the decoy (from two directions) and a harmless walk. |
| Mon, Nov 2 (full day) | Agent loop with Muse Spark + report. | Done Fri night: a session confirmed all 3 bugs 3/3 with no false positives in 5.3 min for US$0.18. |
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

Open `unreal/PlaytestArena` in UE 5.8, press Play, then:

```bash
python3 agent/session.py             # full session: explore, verify, report in runs/<timestamp>/
python3 agent/check_seeded.py        # verifier check with hand-written repros (no LLM)
for t in agent/test_*.py; do python3 $t; done
```

The explorer never writes repro steps: when Muse Spark files a bug, the repro is the list of
actions actually executed since the last level reset, so the verifier replays exactly what
happened. Muse Spark runs with `reasoning_effort: low` (`--effort`), about 3.5 s per turn.

## Repository layout

- `agent/`: explorer, verifier, report, replay videos and the session runner (stdlib only).
- `tasks/`: the prompts given to Muse Code for each delegated module.
- `scripts/muse-lane.sh`: runs one Muse Code task in an isolated worktree.
- `unreal/PlaytestArena/`: UE 5.8 project with the greybox level, seeded bugs and `BP_TestHarness`.
