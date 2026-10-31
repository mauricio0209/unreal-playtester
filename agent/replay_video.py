"""Illustrative replay videos for confirmed bugs (standard library only).

A deterministic verifier replays each bug's repro steps from a fresh level
load. For the demo and the report we record a short first-person video of
one such replay per confirmed bug.

This replay is illustrative only: splitting ``step`` actions into smaller
chunks can change the simulation slightly, so it must never be used to
decide a verdict. Verdicts come from ``verifier``; this module only records
what one replay looked like.
"""

import math
import shutil
import subprocess
from pathlib import Path


def _run_ffmpeg(args) -> None:
    proc = subprocess.run(args, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or
                           f"ffmpeg failed with exit {proc.returncode}")


def record(ue, steps, out_dir, name, chunk_s=0.2, fps=10) -> dict:
    """Record one replay of ``steps`` and encode it as MP4 and GIF.

    Resets the level, screenshots frame 0, replays ``steps`` in order
    (non-step actions are called directly; each ``step`` of S seconds is
    split into ``ceil(S / chunk_s)`` calls of ``ue.step(<= chunk_s)``
    whose durations sum to S, with a screenshot after each call), then
    encodes ``out_dir/<name>.mp4`` and ``out_dir/<name>.gif`` with
    ffmpeg and deletes the ``out_dir/<name>_frames`` folder.
    """
    out_dir = Path(out_dir)
    frames_dir = out_dir / f"{name}_frames"
    frames_dir.mkdir(parents=True, exist_ok=True)

    ue.reset()
    index = 0

    def _grab_frame():
        nonlocal index
        src = Path(ue.screenshot())
        dst = frames_dir / f"{index:06d}.png"
        shutil.move(str(src), str(dst))
        index += 1

    _grab_frame()
    for step_dict in steps or []:
        action = step_dict.get("action")
        if action == "step":
            total = float(step_dict["seconds"])
            n = math.ceil(total / chunk_s) if chunk_s > 0 else 1
            for i in range(max(n, 0)):
                duration = min(chunk_s, total - i * chunk_s)
                ue.step(duration)
                _grab_frame()
        elif action == "move_to":
            ue.move_to(step_dict["x"], step_dict["y"])
        elif action == "look_at":
            ue.look_at(step_dict["x"], step_dict["y"], step_dict["z"])
        elif action == "jump":
            ue.jump()
        elif action == "interact":
            ue.interact()
        else:
            raise ValueError(f"unknown action: {action!r}")
    n_frames = index

    mp4_path = out_dir / f"{name}.mp4"
    gif_path = out_dir / f"{name}.gif"
    palette_path = frames_dir / "palette.png"
    pattern = str(frames_dir / "%06d.png")
    try:
        _run_ffmpeg(["ffmpeg", "-y", "-loglevel", "error",
                     "-framerate", str(fps), "-i", pattern,
                     "-c:v", "libx264", "-pix_fmt", "yuv420p",
                     str(mp4_path)])
        _run_ffmpeg(["ffmpeg", "-y", "-loglevel", "error",
                     "-framerate", str(fps), "-i", pattern,
                     "-vf", "scale=480:-1:flags=lanczos,palettegen",
                     str(palette_path)])
        _run_ffmpeg(["ffmpeg", "-y", "-loglevel", "error",
                     "-framerate", str(fps), "-i", pattern,
                     "-i", str(palette_path),
                     "-lavfi", "scale=480:-1:flags=lanczos[x];[x][1:v]paletteuse",
                     str(gif_path)])
    except Exception:
        shutil.rmtree(frames_dir, ignore_errors=True)
        raise
    shutil.rmtree(frames_dir, ignore_errors=True)
    return {"mp4": mp4_path, "gif": gif_path, "frames": n_frames}
