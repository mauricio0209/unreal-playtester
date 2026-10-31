"""Tests for session.py. Run: python3 agent/test_session.py"""

import io
import json
import tempfile
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

import session
import verifier

NOW = datetime(2026, 10, 31, 12, 0, 0)
STAMP = "20261031-120000"


def make_state(**overrides):
    state = {
        "StepId": 0,
        "bStepping": False,
        "PawnAlive": True,
        "PlayerLocation": {"X": 0, "Y": 0, "Z": 100},
        "Velocity": {"X": 0, "Y": 0, "Z": 0},
        "LastZ": 100,
        "KillZ": -1000,
        "bIsFalling": False,
        "InventoryCount": 0,
        "BootTime": 0.0,
        "ActorStates": {},
        "ActorLocations": {},
    }
    state.update(overrides)
    return state


NORMAL = make_state()
DEAD = make_state(PawnAlive=False, LastZ=-2000)


class FakeUE:
    """Scripted ue double: each reset() starts the next run of states."""

    def __init__(self, runs):
        self._runs = runs
        self.resets = 0

    def reset(self):
        index = min(self.resets, len(self._runs) - 1)
        self.resets += 1
        self._states = self._runs[index]
        self._i = 0
        return self._states[0]

    def _advance(self):
        if self._i + 1 < len(self._states):
            self._i += 1
        return self._states[self._i]

    def state(self):
        return self._states[self._i]

    def move_to(self, x, y):
        raise ValueError("fake ue cannot move_to")

    def jump(self):
        self._advance()

    def look_at(self, x, y, z):
        self._advance()

    def interact(self):
        self._advance()

    def step(self, seconds):
        return self._advance()


def make_hypotheses(shots_dir):
    shots = Path(shots_dir)
    fall = [{"action": "step", "seconds": 1.0}]
    calm = [{"action": "step", "seconds": 1.0}]
    return [
        {"title": "Fall out of world", "hypothesis": "gap in the floor",
         "invariant": "no_fall_out_of_world", "steps": fall,
         "before": shots / "h1_before.png",
         "after": shots / "h1_after.png"},
        {"title": "Fall duplicate", "hypothesis": "same gap again",
         "invariant": "no_fall_out_of_world", "steps": fall,
         "before": None, "after": None},
        {"title": "Unreachable spot", "hypothesis": "ue cannot get there",
         "invariant": "door_opens",
         "steps": [{"action": "move_to", "x": 10, "y": 20}],
         "before": None, "after": None},
        {"title": "Door maybe", "hypothesis": "door might stick",
         "invariant": "door_opens", "steps": calm,
         "before": shots / "h4_before.png", "after": None},
    ]


class FakeExplorer:
    def __init__(self, actions=9):
        self._actions = actions
        self.calls = []

    def explore(self, ue, llm_client, spec, shots_dir, max_turns=40,
                deadline_s=360.0, log=print):
        self.calls.append({"ue": ue, "llm": llm_client, "spec": spec,
                           "shots_dir": Path(shots_dir),
                           "max_turns": max_turns, "deadline_s": deadline_s})
        return {"hypotheses": make_hypotheses(shots_dir),
                "actions": self._actions}


def make_client():
    return SimpleNamespace(model="test-model", cost_usd=0.0123456)


def make_ue():
    return FakeUE([[NORMAL, DEAD]] * 3 + [[NORMAL, NORMAL]] * 3)


def run_session(argv=None, actions=9):
    tmp = tempfile.TemporaryDirectory()
    ue = make_ue()
    client = make_client()
    explorer = FakeExplorer(actions=actions)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = session.main(argv=[] if argv is None else argv, ue=ue,
                          client=client, explorer_mod=explorer, now=NOW,
                          run_root=tmp.name)
    run_dir = Path(tmp.name) / "runs" / STAMP
    return tmp, run_dir, ue, client, explorer, buf.getvalue(), rc


def t_run_dir_layout():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        assert rc == 0, rc
        assert run_dir.is_dir(), run_dir
        assert (run_dir / "shots").is_dir()
        assert (run_dir / "report.md").is_file()
        assert (run_dir / "session.json").is_file()
    finally:
        tmp.cleanup()


def t_explore_defaults():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        assert len(explorer.calls) == 1
        call = explorer.calls[0]
        assert call["ue"] is ue
        assert call["llm"] is client
        assert call["max_turns"] == 40, call
        assert call["deadline_s"] == 360.0, call
        assert call["shots_dir"] == run_dir / "shots", call
        assert "invariants" in call["spec"]
    finally:
        tmp.cleanup()


def t_custom_turns_minutes():
    tmp = tempfile.TemporaryDirectory()
    try:
        explorer = FakeExplorer()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = session.main(argv=["--turns", "5", "--minutes", "20"],
                              ue=make_ue(), client=make_client(),
                              explorer_mod=explorer, now=NOW,
                              run_root=tmp.name)
        assert rc == 0
        assert explorer.calls[0]["max_turns"] == 5
        assert explorer.calls[0]["deadline_s"] == 20 * 60.0 * 0.6
    finally:
        tmp.cleanup()


def t_confirmed_verdict():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        verdict = doc["findings"][0]["verdict"]
        assert verdict["confirmed"] is True, verdict
        assert verdict["runs"] == [True, True, True], verdict
    finally:
        tmp.cleanup()


def t_duplicate_skipping():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        verdict = doc["findings"][1]["verdict"]
        assert verdict["confirmed"] is False, verdict
        assert verdict["runs"] == [], verdict
        assert verdict["reason"] == "duplicate of a confirmed bug", verdict
        # 3 resets for the first hypothesis, 0 for the duplicate,
        # 1 (then ue raises) for the ValueError one, 3 for the last one,
        # plus 1 for the replay video of the single confirmed finding
        # (which fails gracefully here: the fake ue has no screenshot).
        assert ue.resets == 8, ue.resets
    finally:
        tmp.cleanup()


def t_valueerror_rejection():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        verdict = doc["findings"][2]["verdict"]
        assert verdict["confirmed"] is False, verdict
        assert verdict["runs"] == [], verdict
        assert "fake ue cannot move_to" in verdict["reason"], verdict
    finally:
        tmp.cleanup()


def t_rejected_verdict_with_runs():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        verdict = doc["findings"][3]["verdict"]
        assert verdict["confirmed"] is False, verdict
        assert verdict["runs"] == [False, False, False], verdict
        assert isinstance(verdict["reason"], str) and verdict["reason"]
    finally:
        tmp.cleanup()


def t_relative_screenshot_paths():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        first = doc["findings"][0]
        assert first["before"] == "shots/h1_before.png", first
        assert first["after"] == "shots/h1_after.png", first
        second = doc["findings"][1]
        assert second["before"] is None and second["after"] is None, second
        fourth = doc["findings"][3]
        assert fourth["before"] == "shots/h4_before.png", fourth
        assert fourth["after"] is None, fourth
        text = (run_dir / "report.md").read_text(encoding="utf-8")
        assert "shots/h1_before.png" in text, text
    finally:
        tmp.cleanup()


def t_session_json_contents():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        info = doc["session"]
        assert info["started"] == "2026-10-31T12:00:00", info
        assert info["model"] == "test-model", info
        assert info["actions"] == 9, info
        assert info["cost_usd"] == 0.0123, info
        assert isinstance(info["duration_s"], float)
        assert info["duration_s"] >= 0
        assert len(doc["findings"]) == 4
        assert len(doc["hypotheses"]) == 4
        raw = doc["hypotheses"][0]
        assert raw["before"] == str(run_dir / "shots" / "h1_before.png"), raw
        assert raw["after"] == str(run_dir / "shots" / "h1_after.png"), raw
    finally:
        tmp.cleanup()


def t_invariant_description():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        spec = verifier.load_spec(str(Path(session.__file__).resolve().parent
                                       / "spec.json"))
        expected = {inv["id"]: inv["description"]
                    for inv in spec["invariants"]}
        for finding in doc["findings"]:
            assert finding["invariant_description"] == expected[
                finding["invariant"]], finding
    finally:
        tmp.cleanup()


def t_prints_report_and_summary():
    tmp, run_dir, ue, client, explorer, out, rc = run_session()
    try:
        assert str(run_dir / "report.md") in out, out
        assert "1 confirmed" in out, out
    finally:
        tmp.cleanup()


class FakeVideo:
    def __init__(self):
        self.calls = []

    def record(self, ue, steps, out_dir, name, chunk_s=0.2, fps=10):
        self.calls.append({"ue": ue, "steps": list(steps),
                           "out_dir": Path(out_dir), "name": name})
        out_dir = Path(out_dir)
        return {"mp4": out_dir / f"{name}.mp4",
                "gif": out_dir / f"{name}.gif", "frames": 2}


class RaisingVideo:
    def record(self, *args, **kwargs):
        raise RuntimeError("ffmpeg blew up")


def run_session_with_video(argv=None, video_mod=None, actions=9):
    tmp = tempfile.TemporaryDirectory()
    ue = make_ue()
    client = make_client()
    explorer = FakeExplorer(actions=actions)
    buf = io.StringIO()
    with redirect_stdout(buf):
        rc = session.main(argv=[] if argv is None else argv, ue=ue,
                          client=client, explorer_mod=explorer, now=NOW,
                          run_root=tmp.name, video_mod=video_mod)
    run_dir = Path(tmp.name) / "runs" / STAMP
    return tmp, run_dir, ue, client, explorer, buf.getvalue(), rc


def t_videos_for_confirmed_only():
    video = FakeVideo()
    tmp, run_dir, ue, client, explorer, out, rc = run_session_with_video(
        video_mod=video)
    try:
        assert rc == 0, rc
        assert len(video.calls) == 1, video.calls
        call = video.calls[0]
        assert call["ue"] is ue, call
        assert call["name"] == "bug1", call
        assert call["out_dir"] == run_dir / "videos", call
        assert call["steps"] == [{"action": "step", "seconds": 1.0}], call
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        first = doc["findings"][0]
        assert first["video_gif"] == "videos/bug1.gif", first
        assert first["video_mp4"] == "videos/bug1.mp4", first
        assert not Path(first["video_gif"]).is_absolute()
        assert not Path(first["video_mp4"]).is_absolute()
        for finding in doc["findings"][1:]:
            assert finding["video_gif"] is None, finding
            assert finding["video_mp4"] is None, finding
        text = (run_dir / "report.md").read_text(encoding="utf-8")
        assert "videos/bug1.gif" in text, text
    finally:
        tmp.cleanup()


def t_no_video_skips_recording():
    video = FakeVideo()
    tmp, run_dir, ue, client, explorer, out, rc = run_session_with_video(
        argv=["--no-video"], video_mod=video)
    try:
        assert rc == 0, rc
        assert video.calls == [], video.calls
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        for finding in doc["findings"]:
            assert finding["video_gif"] is None, finding
            assert finding["video_mp4"] is None, finding
        assert (run_dir / "report.md").is_file()
    finally:
        tmp.cleanup()


def t_video_failure_still_reports():
    tmp, run_dir, ue, client, explorer, out, rc = run_session_with_video(
        video_mod=RaisingVideo())
    try:
        assert rc == 0, rc
        assert (run_dir / "report.md").is_file()
        doc = json.loads((run_dir / "session.json").read_text(
            encoding="utf-8"))
        assert doc["findings"][0]["video_gif"] is None
        assert doc["findings"][0]["video_mp4"] is None
        assert "1 confirmed" in out, out
    finally:
        tmp.cleanup()


def t_script_provider_runs_without_llm():
    tmp = tempfile.TemporaryDirectory()
    try:
        explorer = FakeExplorer()
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = session.main(argv=["--provider", "script"], ue=make_ue(),
                              client=None, explorer_mod=explorer, now=NOW,
                              run_root=tmp.name)
        assert rc == 0
        assert explorer.calls[0]["llm"] is None, explorer.calls
        doc = json.loads((Path(tmp.name) / "runs" / STAMP / "session.json")
                         .read_text(encoding="utf-8"))
        assert doc["session"]["cost_usd"] == 0, doc["session"]
    finally:
        tmp.cleanup()


def main():
    tests = sorted((name, fn) for name, fn in globals().items()
                   if name.startswith("t_") and callable(fn))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
