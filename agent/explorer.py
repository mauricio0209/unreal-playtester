"""Explorer: Muse Spark plays the level turn by turn and files bug hypotheses.

The model never writes repro steps. When it files a bug, the repro is the list of actions
actually executed since the last level reset, so the verifier replays exactly what happened.
"""

import json
import shutil
import time
from pathlib import Path

import verifier
from llm import image_part

SYSTEM = """You are an expert QA playtester for a 3D first-person game. Your job is to find \
bugs: places where the game breaks one of the invariants in the spec below.

Each turn you get a screenshot of what the player sees, the game state as JSON and your recent \
history. Reply with exactly ONE JSON object and nothing else, in one of these shapes:

{"thought": "<one short sentence>", "actions": [<action>, ...]}
{"thought": "<one short sentence>", "bug": {"invariant": "<invariant id>", "title": "<short title>", "hypothesis": "<what you observed and why it breaks the invariant>"}}

"actions" holds 1 to 4 actions executed in order, e.g. a move_to followed by a step. A reset must be alone.

Actions:
{"type": "move_to", "x": <cm>, "y": <cm>}  walk in a straight line toward a point on the ground
{"type": "look_at", "x": <cm>, "y": <cm>, "z": <cm>}  turn the camera toward a point
{"type": "jump"}
{"type": "interact"}  use whatever is in front of you (doors etc.)
{"type": "step", "seconds": <0.5 to 8>}  let the game run; nothing moves until you step
{"type": "reset"}  reload the level and start a fresh attempt

Rules:
- The game is paused between turns. move_to, jump and interact only take effect during the next step.
- Walking speed is about 600 cm/s. Coordinates are in cm; the player stands about 90 cm above the floor.
- File a bug right after you observe it, BEFORE any reset: the repro steps are taken automatically \
from your actions since the last reset. Then the level resets for you.
- Use the state JSON, not only the image: it is ground truth for position, inventory and object states.
- Anything the spec lists under "intentional" is by design and is NOT a bug.
- Explore systematically: try every object, and cover the whole walkable area of every hall \
(corners, edges, strips between areas), not only the paths between objects. Level geometry can be broken anywhere.
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
    if not isinstance(reply, dict) or ("actions" in reply or "action" in reply) == ("bug" in reply):
        raise ValueError("reply must contain exactly one of 'actions' or 'bug'")
    if "bug" not in reply:
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


def _shot(ue, shots_dir, name):
    path = Path(shots_dir) / f"{name}.png"
    shutil.move(ue.screenshot(), path)
    return path


def explore(ue, llm, spec, shots_dir, max_turns=40, deadline_s=360.0, log=print):
    shots_dir = Path(shots_dir)
    shots_dir.mkdir(parents=True, exist_ok=True)
    system = SYSTEM + json.dumps(spec, indent=1)
    started = time.monotonic()
    hypotheses, history, episode, filed = [], [], [], []
    actions = 0
    state = ue.reset()
    known = set(state["ActorStates"])
    before = _shot(ue, shots_dir, "t000")
    note = "Fresh level load."

    for turn in range(1, max_turns + 1):
        if time.monotonic() - started > deadline_s:
            log(f"deadline reached after {turn - 1} turns")
            break
        shot = before if turn == 1 else _shot(ue, shots_dir, f"t{turn:03d}")
        user = (f"Turn {turn}/{max_turns}. {note}\n"
                f"Recent history:\n" + ("\n".join(history[-12:]) or "(none)") +
                f"\nActions since last reset: {len(episode)}\n"
                f"Bugs already filed: {', '.join(filed) or 'none'}\n"
                f"State: {json.dumps(_brief(state, known))}")
        text = llm.chat([{"role": "system", "content": system},
                         {"role": "user", "content": [{"type": "text", "text": user},
                                                      image_part(shot)]}])
        try:
            reply = parse_reply(text)
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
        except (ValueError, KeyError, TypeError) as e:  # json.JSONDecodeError is a ValueError
            note = f"Your last reply was rejected: {e}. Reply with one valid JSON object."
            history.append(f"t{turn}: invalid reply ({e})")
            log(f"turn {turn}: invalid reply: {e}")
            continue

        actions += len(steps)
        if steps == [None]:  # bug filed or explicit reset: start a fresh episode
            state, episode = ue.reset(), []
            known = set(state["ActorStates"])
            before = _shot(ue, shots_dir, f"t{turn:03d}_reset")
            note = "Level was reset."
            if "bug" not in reply:
                history.append(f"t{turn}: reset")
            continue
        for step in steps:
            state = _do(ue, step)
            episode.append(step)
        note = ""
        loc = _round(state["PlayerLocation"])
        history.append(f"t{turn}: {json.dumps(steps)} -> at {loc}, alive={state['PawnAlive']}, "
                       f"inventory={state['InventoryCount']}, "
                       f"objects={ {n: o['state'] for n, o in _brief(state, known)['Objects'].items()} }")
        log(f"turn {turn}: {reply.get('thought', '')[:80]} | {steps}")

    return {"hypotheses": hypotheses, "actions": actions}
