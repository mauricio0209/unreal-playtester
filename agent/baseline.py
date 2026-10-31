"""Scripted no-LLM baseline explorer.

Same interface as explorer.explore: it runs sweep lanes then one episode per
object, files a hypothesis the first time an invariant predicate holds, and
returns {"hypotheses": [...], "actions": <int>}. Standard library only.
"""

import math
import time
from pathlib import Path

import explorer
import verifier

SPEED_CM_S = 600.0
CHUNK_S = 8.0
STEP_S = 1.0


def _is_num(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _object_steps(player_loc, obj_loc):
    """Steps for one object episode: move_to, travel steps, interact, two steps."""
    px = player_loc.get("X", 0) if isinstance(player_loc, dict) else 0
    py = player_loc.get("Y", 0) if isinstance(player_loc, dict) else 0
    ox, oy = obj_loc.get("X"), obj_loc.get("Y")
    if not _is_num(ox) or not _is_num(oy):
        return None
    if not _is_num(px) or not _is_num(py):
        px, py = 0, 0
    total = math.hypot(ox - px, oy - py) / SPEED_CM_S + STEP_S
    chunks = max(1, math.ceil(total / CHUNK_S - 1e-9))
    steps = [{"action": "move_to", "x": ox, "y": oy}]
    remaining = total
    for _ in range(chunks):
        seconds = min(CHUNK_S, remaining)
        steps.append({"action": "step", "seconds": seconds})
        remaining -= seconds
    steps.append({"action": "interact"})
    steps.append({"action": "step", "seconds": STEP_S})
    steps.append({"action": "step", "seconds": STEP_S})
    return steps


def _check(trace, spec, filed):
    """Return the first newly-broken invariant on this trace, or None."""
    for inv in spec.get("invariants", []) or []:
        if not isinstance(inv, dict) or inv.get("id") in filed:
            continue
        predicate = verifier.PREDICATES.get(inv.get("predicate"))
        if predicate is None:
            continue
        if predicate(trace, inv.get("params", {}) or {}, spec):
            return inv
    return None


def explore(ue, llm, spec, shots_dir, max_turns=40, deadline_s=360.0, log=print):
    del llm, max_turns  # scripted: no model, no turn budget
    shots_dir = Path(shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    hypotheses, filed = [], set()
    actions = 0
    episode_index = 0

    probe = ue.reset()
    actors = probe.get("ActorStates") or {}
    object_names = sorted(name for name in actors)

    lanes, _ = explorer.sweep_lanes(spec)
    episodes = [("lane", lane) for lane in lanes] + [("object", name) for name in object_names]

    for kind, item in episodes:
        if time.monotonic() - started >= deadline_s:
            log(f"deadline reached before episode {episode_index}")
            break
        if kind == "lane":
            label, steps = f"lane {episode_index}", list(item)
        else:
            locs = probe.get("ActorLocations") or {}
            loc = locs.get(item) if isinstance(locs, dict) else None
            if not isinstance(loc, dict):
                log(f"episode {episode_index} object {item}: no location, skipped")
                continue
            steps = _object_steps(probe.get("PlayerLocation"), loc)
            if steps is None:
                log(f"episode {episode_index} object {item}: bad location, skipped")
                continue
            label = f"object {item}"
        state = ue.reset()
        before = explorer._shot(ue, shots_dir, f"baseline_{episode_index:03d}_before")
        trace = [{"action": None, "state": state}]
        done_steps = []
        for step in steps:
            state = explorer._do(ue, step)
            done_steps.append(step)
            actions += 1
            trace.append({"action": step, "state": state})
            hit = _check(trace, spec, filed)
            if hit is not None:
                filed.add(hit["id"])
                hypotheses.append({
                    "title": f"{hit['id']} broken (scripted check)",
                    "hypothesis": f"Scripted {label} episode broke {hit['id']}.",
                    "invariant": hit["id"],
                    "steps": list(done_steps),
                    "before": before,
                    "after": None,
                })
                log(f"episode {episode_index} ({label}): filed {hit['id']}")
            if not state.get("PawnAlive", True):
                break
        after = explorer._shot(ue, shots_dir, f"baseline_{episode_index:03d}_after")
        for hypothesis in hypotheses:
            if hypothesis["after"] is None and hypothesis["before"] == before:
                hypothesis["after"] = after
        log(f"episode {episode_index} ({label}): {len(done_steps)} actions")
        episode_index += 1

    return {"hypotheses": hypotheses, "actions": actions}
