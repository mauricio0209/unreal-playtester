"""Deterministic replay verifier for LLM-filed bug hypotheses.

No LLM is involved here: the level is reset, the repro steps are replayed,
and a deterministic predicate is evaluated on the recorded states. A bug is
confirmed only if the predicate holds in every replay run.

Standard library only.
"""

import json
import math

ALLOWED_ACTIONS = ("move_to", "jump", "look_at", "interact", "step")


def load_spec(path) -> dict:
    """Load a verifier spec file (see spec.json) and return it as a dict."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _require_numbers(step_dict: dict, index: int, keys: tuple) -> None:
    for key in keys:
        value = step_dict.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"step {index} action {step_dict.get('action')!r} "
                f"needs numeric {key!r}"
            )


def _validate_steps(steps: list) -> None:
    """Validate every step before the game is touched (trust boundary)."""
    if not isinstance(steps, list):
        raise ValueError("steps must be a list of dicts")
    for index, step_dict in enumerate(steps):
        if not isinstance(step_dict, dict):
            raise ValueError(f"step {index} must be a dict")
        action = step_dict.get("action")
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"step {index} has invalid action: {action!r}")
        if action == "move_to":
            _require_numbers(step_dict, index, ("x", "y"))
        elif action == "look_at":
            _require_numbers(step_dict, index, ("x", "y", "z"))
        elif action == "step":
            _require_numbers(step_dict, index, ("seconds",))
        # jump / interact take no parameters.


def run_steps(ue, steps) -> list[dict]:
    """Reset, replay steps, and return the trace.

    The trace is [{"action": None, "state": reset_state}, ...] with one
    entry per action holding the step dict and the state recorded after it
    (for ``step``, the state it returns).
    """
    _validate_steps(steps)
    reset_state = ue.reset()
    if reset_state is None:
        reset_state = ue.state()
    trace = [{"action": None, "state": reset_state}]
    for step_dict in steps:
        action = step_dict["action"]
        if action == "move_to":
            ue.move_to(step_dict["x"], step_dict["y"])
            recorded = ue.state()
        elif action == "jump":
            ue.jump()
            recorded = ue.state()
        elif action == "look_at":
            ue.look_at(step_dict["x"], step_dict["y"], step_dict["z"])
            recorded = ue.state()
        elif action == "interact":
            ue.interact()
            recorded = ue.state()
        elif action == "step":  # validated above; kept explicit, no else.
            recorded = ue.step(step_dict["seconds"])
        trace.append({"action": step_dict, "state": recorded})
    return trace


def _player_xy(state: dict):
    loc = state.get("PlayerLocation") or {}
    return loc.get("X"), loc.get("Y")


def _in_region(x, y, region) -> bool:
    if not isinstance(region, dict):
        return False
    try:
        minimum = region["min"]
        maximum = region["max"]
        min_x, max_x = minimum["X"], maximum["X"]
        min_y, max_y = minimum["Y"], maximum["Y"]
    except (KeyError, TypeError):
        return False
    if x is None or y is None:
        return False
    low_x, high_x = (min_x, max_x) if min_x <= max_x else (max_x, min_x)
    low_y, high_y = (min_y, max_y) if min_y <= max_y else (max_y, min_y)
    return low_x <= x <= high_x and low_y <= y <= high_y


def _is_num(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def fell_out_of_world(trace, params, spec) -> bool:
    """True if the pawn died, fell below KillZ, or is below `below_z` (already under the
    floor, still falling) outside intentional regions."""
    intentional = spec.get("intentional", []) or []
    below_z = params.get("below_z")
    for index, entry in enumerate(trace):
        state = entry["state"]
        died = "PawnAlive" in state and not state["PawnAlive"]
        last_z = state.get("LastZ")
        kill_z = state.get("KillZ")
        fell_below = _is_num(last_z) and (
            (_is_num(kill_z) and last_z < kill_z) or (_is_num(below_z) and last_z < below_z))
        if not (died or fell_below):
            continue
        # Where the pawn went through the floor; older states only carry the last known XY.
        floor = state.get("LastFloorLocation")
        x, y = (floor.get("X"), floor.get("Y")) if isinstance(floor, dict) else (None, None)
        for prev in range(index, -1, -1):
            if x is not None and y is not None:
                break
            x, y = _player_xy(trace[prev]["state"])
        excused = any(
            _in_region(x, y, area.get("region"))
            for area in intentional
            if isinstance(area, dict)
        )
        if not excused:
            return True
    return False


def _is_action(entry: dict, name: str) -> bool:
    action = entry.get("action")
    return isinstance(action, dict) and action.get("action") == name


def _distance_3d(a: dict, b: dict) -> float:
    return math.dist(
        (a["X"], a["Y"], a["Z"]),
        (b["X"], b["Y"], b["Z"]),
    )


def door_stays_closed_after_interact(trace, params, spec) -> bool:
    """True if a near-door interact never opened the door (with a later step)."""
    door = params.get("door")
    radius = params.get("radius")
    if door is None or not isinstance(radius, (int, float)):
        return False
    for index, entry in enumerate(trace):
        if not _is_action(entry, "interact") or index == 0:
            continue
        before = trace[index - 1]["state"]
        player = before.get("PlayerLocation") or {}
        actors = before.get("ActorLocations") or {}
        door_loc = actors.get(door)
        if not isinstance(player, dict) or not isinstance(door_loc, dict):
            continue
        try:
            distance = _distance_3d(player, door_loc)
        except (KeyError, TypeError):
            continue
        if distance > radius:
            continue
        if not any(_is_action(e, "step") for e in trace[index + 1:]):
            continue
        if all(
            (e["state"].get("ActorStates") or {}).get(door) != "open"
            for e in trace[index:]
        ):
            return True
    return False


def pickup_not_counted(trace, params, spec) -> bool:
    """True if the pickup vanished without InventoryCount going up."""
    pickup = params.get("pickup")
    if pickup is None:
        return False
    last_present_count = None
    seen_present = False
    for entry in trace:
        actors = entry["state"].get("ActorStates") or {}
        count = entry["state"].get("InventoryCount")
        if pickup in actors:
            seen_present = True
            last_present_count = count
        elif seen_present and count == last_present_count:
            return True
    return False


PREDICATES: dict[str, callable] = {
    "fell_out_of_world": fell_out_of_world,
    "door_stays_closed_after_interact": door_stays_closed_after_interact,
    "pickup_not_counted": pickup_not_counted,
}


def verify(ue, steps, invariant_id, spec, runs=3) -> dict:
    """Replay steps ``runs`` times; confirm only if every run shows the bug."""
    invariant = None
    for candidate in spec.get("invariants", []) or []:
        if isinstance(candidate, dict) and candidate.get("id") == invariant_id:
            invariant = candidate
            break
    if invariant is None:
        return {
            "invariant": invariant_id,
            "confirmed": False,
            "runs": [],
            "reason": f"unknown invariant: {invariant_id}",
        }
    predicate_name = invariant.get("predicate")
    predicate = PREDICATES.get(predicate_name)
    if predicate is None:
        return {
            "invariant": invariant_id,
            "confirmed": False,
            "runs": [],
            "reason": f"unknown predicate: {predicate_name}",
        }
    params = invariant.get("params", {}) or {}
    results = []
    for _ in range(runs):
        trace = run_steps(ue, steps)
        results.append(bool(predicate(trace, params, spec)))
    hits = sum(results)
    confirmed = len(results) > 0 and all(results)
    if confirmed:
        reason = f"bug reproduced in all {len(results)} runs"
    else:
        reason = f"bug reproduced in {hits} of {len(results)} runs"
    return {
        "invariant": invariant_id,
        "confirmed": confirmed,
        "runs": results,
        "reason": reason,
    }
