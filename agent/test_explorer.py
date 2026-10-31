"""Tests for explorer.py with a fake game and a scripted model. Run: python3 agent/test_explorer.py"""

import tempfile
from pathlib import Path

import explorer

SPEC = {"invariants": [{"id": "door_opens", "description": "d", "predicate": "p"}],
        "intentional": []}


def state(alive=True, x=0):
    return {"PlayerLocation": {"X": x, "Y": 0, "Z": 90}, "PawnAlive": alive, "bIsFalling": False,
            "InventoryCount": 0, "KillZ": -1000, "ActorStates": {"Door1": "closed"},
            "ActorLocations": {"Door1": {"X": 3500, "Y": 0, "Z": 150}}}


class FakeUE:
    def __init__(self, tmp, die_on_step=False):
        self.tmp, self.n, self.calls, self.die = Path(tmp), 0, [], die_on_step

    def screenshot(self):
        self.n += 1
        p = self.tmp / f"ue{self.n}.png"
        p.write_bytes(b"\x89PNG fake")
        return p

    def reset(self):
        self.calls.append("reset")
        return state()

    def state(self):
        return state()

    def move_to(self, x, y):
        self.calls.append(("move_to", x, y))

    def interact(self):
        self.calls.append("interact")

    def jump(self):
        self.calls.append("jump")

    def step(self, seconds):
        self.calls.append(("step", seconds))
        return state(alive=not self.die, x=500)


class FakeLLM:
    def __init__(self, replies):
        self.replies, self.seen = list(replies), []

    def chat(self, messages):
        self.seen.append(messages)
        return self.replies.pop(0) if self.replies else '{"action": {"type": "step", "seconds": 1}}'


def run(replies, turns, die=False):
    with tempfile.TemporaryDirectory() as tmp:
        ue, llm = FakeUE(tmp, die), FakeLLM(replies)
        out = explorer.explore(ue, llm, SPEC, Path(tmp) / "shots", max_turns=turns, log=lambda *_: None)
        return out, ue, llm


def t_bug_repro_is_executed_actions():
    out, ue, _ = run([
        '{"thought": "go", "action": {"type": "move_to", "x": 3440, "y": 0}}',
        'Sure! {"action": {"type": "step", "seconds": 30}}',  # prose around JSON, clamped seconds
        '{"action": {"type": "interact"}}',
        '{"action": {"type": "step", "seconds": 1}}',
        '{"action": {"type": "jump"}}',  # never stepped: dropped from the repro
        '{"bug": {"invariant": "door_opens", "title": "Door stuck", "hypothesis": "h"}}',
    ], turns=6)
    [h] = out["hypotheses"]
    assert h["steps"] == [{"action": "move_to", "x": 3440, "y": 0},
                          {"action": "step", "seconds": 8.0},
                          {"action": "interact"},
                          {"action": "step", "seconds": 1.0}], h["steps"]
    assert h["before"].name == "t000.png" and h["after"].name == "t006.png"
    assert ue.calls.count("reset") == 2  # initial + after filing
    assert out["actions"] == 6


def t_invalid_replies_are_fed_back_not_executed():
    out, ue, llm = run([
        "no json here",
        '{"action": {"type": "teleport"}}',
        '{"bug": {"invariant": "door_opens", "title": "t", "hypothesis": "h"}}',  # no step yet
        '{"bug": {"invariant": "made_up", "title": "t", "hypothesis": "h"}}',
    ], turns=4)
    assert out["hypotheses"] == [] and out["actions"] == 0
    assert ue.calls == ["reset"]
    last_user = llm.seen[-1][1]["content"][0]["text"]
    assert "rejected" in last_user, last_user


def t_dead_pawn_only_allows_bug_or_reset():
    out, ue, _ = run([
        '{"action": {"type": "move_to", "x": 1, "y": 1}}',
        '{"action": {"type": "step", "seconds": 1}}',
        '{"action": {"type": "move_to", "x": 2, "y": 2}}',  # rejected: pawn is gone
        '{"action": {"type": "reset"}}',
    ], turns=4, die=True)
    assert ("move_to", 2, 2) not in ue.calls
    assert ue.calls.count("reset") == 2


def t_action_batches_and_filed_memory():
    out, ue, llm = run([
        '{"actions": [{"type": "move_to", "x": 3440, "y": 0}, {"type": "step", "seconds": 6},'
        ' {"type": "interact"}, {"type": "step", "seconds": 1}]}',
        '{"bug": {"invariant": "door_opens", "title": "Door stuck", "hypothesis": "h"}}',
        '{"actions": [{"type": "move_to", "x": 1, "y": 1}, {"type": "reset"}]}',  # reset not alone
        '{"actions": []}',
    ], turns=4)
    [h] = out["hypotheses"]
    assert [s["action"] for s in h["steps"]] == ["move_to", "step", "interact", "step"]
    assert ("move_to", 1, 1) not in ue.calls
    assert out["actions"] == 5  # 4 batched actions + the bug
    texts = [m[1]["content"][0]["text"] for m in llm.seen]
    assert "Bugs already filed: none" in texts[0]
    assert "door_opens (Door stuck)" in texts[2], texts[2]
    assert "rejected" in texts[3]


def t_vanished_objects_marked_missing():
    s = state()
    s["ActorStates"] = {}
    s["ActorLocations"] = {}
    assert explorer._brief(s, {"Pickup1"})["Objects"] == {"Pickup1": {"state": "missing"}}


def t_screenshot_sent_every_turn():
    _, _, llm = run([], turns=2)
    for msgs in llm.seen:
        img = msgs[1]["content"][1]
        assert img["image_url"]["url"].startswith("data:image/png;base64,"), img


def main():
    tests = sorted((n, f) for n, f in globals().items() if n.startswith("t_"))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
