"""Tests for report.py. Run: python3 agent/test_report.py"""

import tempfile
from pathlib import Path

import report


def sample_session(**overrides):
    session = {
        "started": "2026-11-02T10:00:00",
        "model": "muse-spark-1.3",
        "actions": 57,
        "cost_usd": 0.42,
        "duration_s": 380.5,
    }
    session.update(overrides)
    return session


def sample_finding(**overrides):
    finding = {
        "title": "Door does not open when interacting next to it",
        "hypothesis": "the door trigger looks misaligned",
        "invariant": "door_opens",
        "invariant_description": "Doors open when the player interacts within 150 cm.",
        "steps": [
            {"action": "move_to", "x": 3350, "y": 0},
            {"action": "step", "seconds": 3.0},
            {"action": "interact"},
            {"action": "step", "seconds": 1.0},
        ],
        "verdict": {
            "invariant": "door_opens",
            "confirmed": True,
            "runs": [True, True, True],
            "reason": "bug reproduced in all 3 runs",
        },
        "before": "shots/f1_before.png",
        "after": "shots/f1_after.png",
    }
    finding.update(overrides)
    return finding


def t_flaky_verdict_labelled():
    flaky = {"invariant": "door_opens", "confirmed": False, "runs": [False, True, False],
             "reason": "bug reproduced in 1 of 3 runs"}
    with tempfile.TemporaryDirectory() as tmp:
        text = report.write_report(tmp, sample_session(),
                                   [sample_finding(verdict=flaky)]).read_text()
    assert "Verdict: Flaky, not confirmed (1/3 runs reproduced)" in text, text


def t_describe_step_move_to():
    assert report.describe_step({"action": "move_to", "x": 3350, "y": 0}) == \
        "Walk to (3350, 0)"


def t_describe_step_move_to_rounds():
    assert report.describe_step({"action": "move_to", "x": 3350.6, "y": 0.4}) == \
        "Walk to (3351, 0)"


def t_describe_step_look_at():
    assert report.describe_step({"action": "look_at", "x": 100, "y": 0, "z": 50}) == \
        "Look at (100, 0, 50)"


def t_describe_step_jump():
    assert report.describe_step({"action": "jump"}) == "Jump"


def t_describe_step_interact():
    assert report.describe_step({"action": "interact"}) == "Press Interact"


def t_describe_step_step():
    assert report.describe_step({"action": "step", "seconds": 3.0}) == \
        "Let the game run for 3.0 s"


def t_summary_counts():
    with tempfile.TemporaryDirectory() as tmp:
        findings = [
            sample_finding(),
            sample_finding(title="Second bug"),
            sample_finding(
                title="Decoy pit",
                verdict={"invariant": "no_fall_out_of_world",
                         "confirmed": False, "runs": [False, False, False],
                         "reason": "no fall outside the pit"}),
        ]
        path = report.write_report(tmp, sample_session(), findings)
        text = Path(path).read_text(encoding="utf-8")
        assert "2 confirmed bugs" in text, text
        assert "1 rejected hypotheses" in text, text


def t_confirmed_before_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        rejected = sample_finding(
            title="Rejected one",
            verdict={"invariant": "door_opens", "confirmed": False,
                     "runs": [True, False, False], "reason": "flaky"})
        confirmed = sample_finding(title="Confirmed one")
        path = report.write_report(tmp, sample_session(), [rejected, confirmed])
        text = Path(path).read_text(encoding="utf-8")
        assert text.index("Confirmed one") < text.index("Rejected one"), text
        assert text.index("## Confirmed bugs") < text.index("## Rejected hypotheses")


def t_verdict_per_run_results():
    with tempfile.TemporaryDirectory() as tmp:
        path = report.write_report(tmp, sample_session(), [sample_finding()])
        text = Path(path).read_text(encoding="utf-8")
        assert "3/3 runs reproduced" in text, text


def t_repro_steps_and_fresh_load():
    with tempfile.TemporaryDirectory() as tmp:
        path = report.write_report(tmp, sample_session(), [sample_finding()])
        text = Path(path).read_text(encoding="utf-8")
        assert "Start from a fresh level load." in text, text
        assert "1. Walk to (3350, 0)" in text, text
        assert "3. Press Interact" in text, text


def t_session_table():
    with tempfile.TemporaryDirectory() as tmp:
        path = report.write_report(tmp, sample_session(), [sample_finding()])
        text = Path(path).read_text(encoding="utf-8")
        for expected in ("muse-spark-1.3", "2026-11-02T10:00:00", "57",
                         "380.5", "0.42"):
            assert expected in text, (expected, text)


def t_missing_screenshots_no_image_line():
    with tempfile.TemporaryDirectory() as tmp:
        finding = sample_finding(before=None, after=None)
        path = report.write_report(tmp, sample_session(), [finding])
        text = Path(path).read_text(encoding="utf-8")
        assert "![" not in text, text


def t_screenshots_present():
    with tempfile.TemporaryDirectory() as tmp:
        path = report.write_report(tmp, sample_session(), [sample_finding()])
        text = Path(path).read_text(encoding="utf-8")
        assert "![Before](shots/f1_before.png)" in text, text
        assert "![After](shots/f1_after.png)" in text, text


def t_explorer_text_escaped():
    with tempfile.TemporaryDirectory() as tmp:
        evil = "Nice bug\n# Injected heading\n![x](http://evil)"
        finding = sample_finding(title=evil, hypothesis=evil)
        path = report.write_report(tmp, sample_session(), [finding])
        text = Path(path).read_text(encoding="utf-8")
        assert "![x](http://evil)" not in text, text
        assert "\n# Injected heading" not in text, text
        assert "\\# Injected heading" in text, text
        assert "\\!\\[x\\]" in text, text


def t_file_written_under_run_dir():
    with tempfile.TemporaryDirectory() as tmp:
        run_dir = str(Path(tmp) / "run123")
        path = report.write_report(run_dir, sample_session(), [sample_finding()])
        assert isinstance(path, Path), path
        assert path == Path(run_dir) / "report.md"
        assert path.is_file()
        assert "# Session report" in path.read_text(encoding="utf-8")


def t_replay_lines_present():
    with tempfile.TemporaryDirectory() as tmp:
        finding = sample_finding(video_gif="videos/bug1.gif",
                                 video_mp4="videos/bug1.mp4")
        path = report.write_report(tmp, sample_session(), [finding])
        text = Path(path).read_text(encoding="utf-8")
        assert "![Replay](videos/bug1.gif)" in text, text
        assert "[Replay video (MP4)](videos/bug1.mp4)" in text, text
        assert text.index("Press Interact") < text.index("![Replay]"), text


def t_replay_lines_absent_without_video():
    with tempfile.TemporaryDirectory() as tmp:
        path = report.write_report(tmp, sample_session(), [sample_finding()])
        text = Path(path).read_text(encoding="utf-8")
        assert "Replay" not in text, text
        finding = sample_finding(video_gif=None, video_mp4=None)
        path = report.write_report(tmp, sample_session(), [finding])
        text = Path(path).read_text(encoding="utf-8")
        assert "Replay" not in text, text


def main():
    tests = sorted(
        [(name, fn) for name, fn in globals().items()
         if name.startswith("t_") and callable(fn)]
    )
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
