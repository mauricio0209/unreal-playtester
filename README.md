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
  1. Floor without collision. Predicate: `Z < KillZ`.
  2. Door with a misaligned trigger. Predicate: door stays closed after `Interact` within 150 cm.
  3. Pickup that doesn't increment the counter. Predicate: inventory unchanged although the pickup was destroyed.
  4. Decoy: a pit that `spec.json` declares intentional. It must be rejected.
- `spec.json`: the game's invariants in natural language, each paired with a predicate.
- Muse Spark Open on Baseten as an interchangeable cheap explorer (same chat-completions interface).

## Success criteria

1. One command runs a full session in under 10 minutes for under US$5.
2. At least 2 of the 3 seeded bugs are found and confirmed by the verifier 3 out of 3 times.
3. No non-reproducible bug is ever marked as confirmed, and the decoy is rejected.
4. Every report can be reproduced by a human from its steps alone.

## Setup

```bash
cp .env.example .env   # then fill in your keys
```

## Repository layout

- `agent/`: Python agent, verifier and report (coming next).
- `unreal/PlaytestArena/`: UE 5.8 project with the greybox level, seeded bugs and `BP_TestHarness`.
