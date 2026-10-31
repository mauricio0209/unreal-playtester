# Task: replay videos for confirmed bugs

Create `agent/replay_video.py` and `agent/test_replay_video.py`, and make small, targeted edits
to `agent/session.py`, `agent/report.py`, `agent/test_session.py` and `agent/test_report.py`.
Python 3.14, standard library only, plus the `ffmpeg` binary (installed at `/usr/bin/ffmpeg`,
call it with `subprocess`, never through a shell). Keep the existing style. Run every
`agent/test_*.py` you touch and make sure they all pass before finishing.

## Context

A deterministic verifier replays each bug's repro steps from a fresh level load. For the demo
and the report we want a short video of one replay of every confirmed bug: the viewer sees,
in first person, the player fall through the floor, or stand at a door that never opens.

`ue` (see `agent/ue.py`) exposes `reset() -> state`, `step(seconds) -> state`,
`move_to(x, y)`, `look_at(x, y, z)`, `jump()`, `interact()`, and `screenshot() -> Path` (a
new 960x540 PNG written by the engine; move it, do not copy it, so the engine folder does not
fill up). Steps are dicts: `{"action": "move_to", "x":, "y":}`, `{"action": "look_at",
"x":, "y":, "z":}`, `{"action": "jump"}`, `{"action": "interact"}`,
`{"action": "step", "seconds":}`.

## `agent/replay_video.py`

```python
def record(ue, steps, out_dir, name, chunk_s=0.2, fps=10) -> dict
    # ue.reset(); screenshot as frame 0. Run the steps in order; non-step actions are called
    # directly. A step of S seconds is split into ceil(S / chunk_s) calls of
    # ue.step(<= chunk_s) whose durations sum to S, with a screenshot after each call.
    # Frames go to out_dir/<name>_frames/000000.png, 000001.png, ...
    # Then encode with ffmpeg (-y, -loglevel error):
    #   out_dir/<name>.mp4: libx264, yuv420p, -framerate fps
    #   out_dir/<name>.gif: same frames, scaled to width 480, palettegen/paletteuse
    # Delete the frames folder afterwards. Return {"mp4": Path, "gif": Path, "frames": n}.
    # Raise RuntimeError with ffmpeg's stderr if encoding fails.
```

This replay is illustrative only: splitting steps can change the simulation slightly, so it
must never be used to decide a verdict. Say so in the module docstring.

## `agent/session.py`

After all verdicts are computed, for every confirmed finding call
`replay_video.record(ue, steps, run_dir / "videos", f"bug{i}")` (i = 1, 2, ... over confirmed
findings) and store `"video_gif"` and `"video_mp4"` in the finding as paths relative to
run_dir. Add a `--no-video` flag that skips this. If `record` raises, log the error, leave
both fields None and continue (a missing video must never lose the report). Make the module
injectable like the others: `main(..., video_mod=None)`.

## `agent/report.py`

If a finding has `video_gif`, add after the repro steps:
`![Replay](<video_gif>)` and, if `video_mp4` is set, a line `[Replay video (MP4)](<video_mp4>)`.

## Tests

- `test_replay_video.py`: a fake `ue` whose `screenshot()` writes a real tiny PNG (build it
  with zlib + struct, e.g. 64x36 solid colour that changes per frame). Check the chunking
  (a 1.0 s step with chunk 0.2 gives five `step(0.2)` calls; 0.5 s gives 0.2, 0.2, 0.1 within
  float tolerance), the frame count, that mp4 and gif exist and are non-empty, that the frames
  folder is removed, and that non-step actions are forwarded. Skip the encoding asserts with a
  printed note if `shutil.which("ffmpeg")` is None.
- `test_session.py`: videos recorded only for confirmed findings, relative paths, `--no-video`
  skips, and a raising video module still produces the report.
- `test_report.py`: replay lines present when `video_gif` is set, absent otherwise.
