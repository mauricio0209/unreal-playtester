"""Explorer: Muse Spark plays the level turn by turn and files bug hypotheses.

The model never writes repro steps. When it files a bug, the repro is the list of actions
actually executed since the last level reset, so the verifier replays exactly what happened.
"""

import json
import math
import shutil
import time
from pathlib import Path

import verifier
from llm import image_part

SYSTEM = """You are an expert QA playtester for a 3D first-person game. Your job is to find \
bugs: places where the game breaks one of the invariants in the spec below.

Each turn you get a screenshot of what the player sees, the game state as JSON and your recent \
history. Reply with exactly ONE JSON object and nothing else, in one of these shapes:

{"thought": "<one short sentence>", "testing": "<invariant id>", "actions": [<action>, ...]}
{"thought": "<one short sentence>", "bug": {"invariant": "<invariant id>", "title": "<short title>", "hypothesis": "<what you observed and why it breaks the invariant>"}}
{"thought": "<one short sentence>", "done": "<what you tested>"}  end the session: refused while an invariant was never tested

"actions" holds 1 to 4 actions executed in order, e.g. a move_to followed by a step. A reset must be alone.

Actions:
{"type": "walk_to", "x": <cm>, "y": <cm>}  walk to a point and keep going until you arrive or are blocked (up to 12 s); prefer it to move_to + step
{"type": "move_to", "x": <cm>, "y": <cm>}  walk in a straight line toward a point on the ground
{"type": "look_at", "x": <cm>, "y": <cm>, "z": <cm>}  turn the camera toward a point
{"type": "jump"}
{"type": "interact"}  use whatever is in front of you (doors etc.)
{"type": "step", "seconds": <0.5 to 8>}  let the game run; nothing moves until you step
{"type": "reset"}  reload the level and start a fresh attempt

Rules:
- The game is paused between turns. move_to, jump and interact only take effect during the next step.
- To interact with an object, walk_to its exact location from the state: you stop when you bump \
into it, which is within interaction range. Stopping short of it can leave you out of range.
- Walking speed is about 600 cm/s. Coordinates are in cm; the player stands about 90 cm above the floor.
- File a bug right after you observe it, BEFORE any reset: the repro steps are taken automatically \
from your actions since the last reset. Then the level resets for you.
- Use the state JSON, not only the image: it is ground truth for position, inventory and object states.
- Anything the spec lists under "intentional" is by design and is NOT a bug.
- A scripted sweep walks the walkable area in straight lanes about 200 cm apart, each lane from \
a fresh level load, and runs between your turns. It hands control to you when the player falls: \
then judge the fall against the spec (check the intentional list) and file a bug or reset.
- Otherwise, exercise every invariant in the spec through the objects listed in Objects (walk \
into pickups, interact with doors from up close) and file what breaks. Test each invariant in its \
own attempt: reset before starting the next one, so every repro holds only the actions that \
invariant needs (an invariant may need a sequence, like picking something up before using \
something else). Try both what should work and what should not. When every invariant is done, \
explore what straight lanes could miss.
- After every turn the invariants are also checked automatically on the current attempt. When \
one holds you are told: confirm it with your own observation and file it, or say why not.
- "testing" names the invariant your actions are testing. Each turn you see how many attempts \
went to each invariant and which were never tested: test the untested ones before repeating one \
that already behaved correctly.
- Bugs you already filed are listed each turn. Never file the same invariant twice: spend your \
remaining turns finding different bugs.
- If PawnAlive is false the player is gone: file a bug if it is one, otherwise reset.

Spec:
"""

ACTION_KEYS = {"move_to": ("x", "y"), "look_at": ("x", "y", "z"), "jump": (), "interact": (),
               "step": ("seconds",)}


def _round(v):
    return {k: round(x) for k, x in v.items()} if isinstance(v, dict) else v


def _brief(state, known=()):
    """The state the model sees: rounded, without harness bookkeeping, and with objects that
    existed at the last reset but are gone now marked "missing"."""
    objects = {name: {"state": s, "location": _round(state["ActorLocations"].get(name))}
               for name, s in state["ActorStates"].items()}
    objects.update({name: {"state": "missing"} for name in known if name not in objects})
    return {
        "PlayerLocation": _round(state["PlayerLocation"]),
        "PawnAlive": state["PawnAlive"],
        "bIsFalling": state["bIsFalling"],
        "InventoryCount": state["InventoryCount"],
        "KillZ": state["KillZ"],
        "Objects": objects,
    }


def parse_reply(text):
    """Return the first JSON object in the model reply, or raise ValueError."""
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in reply")
    reply = json.loads(text[start:end + 1])
    kinds = ("actions" in reply or "action" in reply) + ("bug" in reply) + ("done" in reply) \
        if isinstance(reply, dict) else 0
    if kinds != 1:
        raise ValueError("reply must contain exactly one of 'actions', 'bug' or 'done'")
    if "bug" not in reply and "done" not in reply:
        actions = reply.pop("actions", None) or [reply.pop("action", None)]
        if not isinstance(actions, list) or not 1 <= len(actions) <= 4:
            raise ValueError("'actions' must be a list of 1 to 4 actions")
        reply["actions"] = actions
    return reply


def to_step(action):
    """Validate a model action and convert it to a verifier step dict (reset returns None)."""
    kind = action.get("type") if isinstance(action, dict) else None
    if kind == "reset":
        return None
    if kind == "walk_to":  # expanded into move_to + steps when executed (see _walk_to)
        step = {"action": "move_to", "x": action.get("x"), "y": action.get("y")}
        verifier._validate_steps([step])
        return dict(step, action="walk_to")
    if kind not in ACTION_KEYS:
        raise ValueError(f"unknown action type {kind!r}")
    step = {"action": kind, **{k: action.get(k) for k in ACTION_KEYS[kind]}}
    if kind == "step":
        secs = step["seconds"]
        if isinstance(secs, (int, float)) and not isinstance(secs, bool):
            step["seconds"] = min(max(float(secs), 0.5), 8.0)
    verifier._validate_steps([step])  # same trust boundary the verifier applies
    return step


def _do(ue, step):
    kind = step["action"]
    if kind == "step":
        return ue.step(step["seconds"])
    getattr(ue, kind)(*(step[k] for k in ACTION_KEYS[kind]))
    return ue.state()


def _walk_to(ue, step, chunk_s=1.0, max_s=12.0, arrive_cm=100.0, stuck_cm=20.0):
    """Run a walk_to as concrete move_to + step actions; return the executed (step, state)
    pairs, so the repro the verifier replays is exactly what happened."""
    move = {"action": "move_to", "x": step["x"], "y": step["y"]}
    state = _do(ue, move)
    done = [(move, state)]
    for _ in range(int(max_s / chunk_s)):
        before = state["PlayerLocation"]
        tick = {"action": "step", "seconds": chunk_s}
        state = _do(ue, tick)
        done.append((tick, state))
        loc = state["PlayerLocation"]
        if (not state.get("PawnAlive", True)
                or math.hypot(loc["X"] - step["x"], loc["Y"] - step["y"]) <= arrive_cm
                or math.hypot(loc["X"] - before["X"], loc["Y"] - before["Y"]) < stuck_cm):
            break
    return done


def _shot(ue, shots_dir, name):
    path = Path(shots_dir) / f"{name}.png"
    shutil.move(ue.screenshot(), path)
    return path


def _holding(trace, spec):
    """Invariant ids whose predicate holds on this attempt's trace."""
    held = []
    for inv in spec.get("invariants", []):
        predicate = verifier.PREDICATES.get(inv.get("predicate"))
        try:
            if predicate and predicate(trace, inv.get("params", {}) or {}, spec):
                held.append(inv["id"])
        except Exception:  # a hint is best effort; the verifier decides later
            continue
    return held


def sweep_lanes(spec, spacing=200, margin=100, chunk_s=2.0, speed=600):
    """Scripted coverage: one straight lane along X per Y row of the walkable area.

    Lanes are cheap and exhaustive; the model only judges what they turn up. Returns
    (lanes, fall params), or ([], None) when the spec has no walkable area or no fall invariant."""
    area = (spec.get("level") or {}).get("walkable_area")
    fall = next((i for i in spec.get("invariants", []) if i.get("predicate") == "fell_out_of_world"),
                None)
    if not area or not fall:
        return [], None
    x0, x1 = area["min"]["X"] + margin, area["max"]["X"] - margin
    ys = range(int(area["min"]["Y"] + margin), int(area["max"]["Y"] - margin) + 1, spacing)
    chunks = int((x1 - x0) / speed / chunk_s) + 1
    # move_to is re-sent each chunk so the walk never depends on a target surviving a step
    lanes = [[{"action": "move_to", "x": x0, "y": y}, {"action": "step", "seconds": chunk_s}] +
             [s for _ in range(chunks) for s in ({"action": "move_to", "x": x1, "y": y},
                                                 {"action": "step", "seconds": chunk_s})]
             for y in ys]
    return lanes, fall.get("params", {})


def explore(ue, llm, spec, shots_dir, max_turns=40, deadline_s=360.0, log=print):
    shots_dir = Path(shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)
    system = SYSTEM + json.dumps(spec, indent=1)
    started = time.monotonic()
    hypotheses, history, episode, filed = [], [], [], []
    actions = 0
    state = ue.reset()
    trace, hinted, attempt_tested = [{"action": None, "state": state}], set(), set()
    known = set(state["ActorStates"])
    before = _shot(ue, shots_dir, "t000")
    note = "Fresh level load."
    lanes, fall_params = sweep_lanes(spec)
    ids = [inv["id"] for inv in spec["invariants"]]
    tested = dict.fromkeys(ids, 0)  # attempts per invariant, as the model declared them

    def count_attempt(invariant):
        if invariant not in attempt_tested:
            attempt_tested.add(invariant)
            tested[invariant] += 1

    def fell(s):  # any fall, intentional or not: judging it is the model's job
        return verifier.fell_out_of_world([{"state": s}], fall_params, {})

    for turn in range(1, max_turns + 1):
        while lanes and not fell(state) and time.monotonic() - started <= deadline_s:
            lane = lanes.pop(0)
            state, episode = ue.reset(), []
            trace, hinted, attempt_tested = [{"action": None, "state": state}], set(), set()
            known = set(state["ActorStates"])
            before = _shot(ue, shots_dir, f"t{turn:03d}_lane{len(lanes)}")
            for step in lane:
                state = _do(ue, step)
                episode.append(step)
                trace.append({"action": step, "state": state})
                actions += 1
                if fell(state):
                    break
            loc = _round(state["PlayerLocation"])
            history.append(f"sweep lane y={lane[0]['y']} -> at {loc}, alive={state['PawnAlive']}")
            log(f"sweep lane y={lane[0]['y']}: at {loc}, fell={fell(state)}")
            if fell(state):
                note = ("The scripted sweep stopped because the player fell: file a bug if "
                        "this breaks an invariant, otherwise reset.")
            elif not lanes:  # sweep done: object repros must not carry a lane's steps
                state, episode = ue.reset(), []
                trace, hinted, attempt_tested = [{"action": None, "state": state}], set(), set()
                known = set(state["ActorStates"])
                before = _shot(ue, shots_dir, f"t{turn:03d}_swept")
                note = "Scripted sweep finished. Level was reset."
        if time.monotonic() - started > deadline_s:
            log(f"deadline reached after {turn - 1} turns")
            break
        shot = before if turn == 1 and not episode else _shot(ue, shots_dir, f"t{turn:03d}")
        user = (f"Turn {turn}/{max_turns}. {note}\n"
                f"Recent history:\n" + ("\n".join(history[-12:]) or "(none)") +
                f"\nActions since last reset: {len(episode)}\n"
                f"Bugs already filed: {', '.join(filed) or 'none'}\n"
                f"Attempts per invariant: {', '.join(f'{i} x{n}' for i, n in tested.items() if n) or 'none'}"
                f"; never tested: {', '.join(i for i, n in tested.items() if not n) or 'none'}\n"
                f"State: {json.dumps(_brief(state, known))}")
        text = llm.chat([{"role": "system", "content": system},
                         {"role": "user", "content": [{"type": "text", "text": user},
                                                      image_part(shot)]}])
        try:
            reply = parse_reply(text)
            if "done" in reply:
                untested = [i for i, n in tested.items() if not n]
                if untested:
                    raise ValueError(f"not done: never tested {', '.join(untested)}")
                log(f"turn {turn}: done: {str(reply['done'])[:120]}")
                break
            if "bug" in reply:
                bug = reply["bug"]
                steps_done = [i for i, s in enumerate(episode) if s["action"] == "step"]
                if not steps_done:
                    raise ValueError("a bug needs at least one step since the last reset")
                if bug.get("invariant") not in {i["id"] for i in spec["invariants"]}:
                    raise ValueError(f"unknown invariant {bug.get('invariant')!r}")
                hypotheses.append({"title": str(bug.get("title", "")),
                                   "hypothesis": str(bug.get("hypothesis", "")),
                                   # actions after the last step never took effect
                                   "invariant": bug["invariant"],
                                   "steps": episode[:steps_done[-1] + 1],
                                   "before": before, "after": shot})
                count_attempt(bug["invariant"])
                filed.append(f"{bug['invariant']} ({bug.get('title')})")
                log(f"turn {turn}: BUG {bug['invariant']}: {bug.get('title')}")
                history.append(f"t{turn}: filed bug '{bug.get('title')}' -> level reset")
                steps = [None]
            else:
                steps = [to_step(a) for a in reply["actions"]]
                if None in steps and len(steps) > 1:
                    raise ValueError("a reset must be the only action in its turn")
                if steps != [None] and not state["PawnAlive"]:
                    raise ValueError("the player is gone: file a bug or reset")
                if steps != [None]:
                    if reply.get("testing") not in tested:
                        raise ValueError("'testing' must name the invariant id these actions test")
                    count_attempt(reply["testing"])
        except (ValueError, KeyError, TypeError) as e:  # json.JSONDecodeError is a ValueError
            note = f"Your last reply was rejected: {e}. Reply with one valid JSON object."
            history.append(f"t{turn}: invalid reply ({e})")
            log(f"turn {turn}: invalid reply: {e}")
            continue

        actions += steps == [None]  # executed actions are counted as they run
        if {h["invariant"] for h in hypotheses} >= {i["id"] for i in spec["invariants"]}:
            log(f"every invariant filed after {turn} turns")
            break
        if steps == [None]:  # bug filed or explicit reset: start a fresh episode
            state, episode = ue.reset(), []
            trace, hinted, attempt_tested = [{"action": None, "state": state}], set(), set()
            known = set(state["ActorStates"])
            before = _shot(ue, shots_dir, f"t{turn:03d}_reset")
            note = "Level was reset."
            if "bug" not in reply:
                history.append(f"t{turn}: reset")
            continue
        for step in steps:
            for done, state in (_walk_to(ue, step) if step["action"] == "walk_to"
                                else [(step, _do(ue, step))]):
                episode.append(done)
                trace.append({"action": done, "state": state})
                actions += 1
        fired = [i for i in _holding(trace, spec) if i not in hinted and i not in
                 {h["invariant"] for h in hypotheses}]
        hinted.update(fired)
        note = (f"Automatic check: {', '.join(fired)} holds on this attempt. File it if what you "
                "see confirms it." if fired else "")
        loc = _round(state["PlayerLocation"])
        history.append(f"t{turn}: {json.dumps(steps)} -> at {loc}, alive={state['PawnAlive']}, "
                       f"inventory={state['InventoryCount']}, "
                       f"objects={ {n: o['state'] for n, o in _brief(state, known)['Objects'].items()} }")
        log(f"turn {turn}: {reply.get('thought', '')[:80]} | {steps}")

    return {"hypotheses": hypotheses, "actions": actions}
