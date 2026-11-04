"""Assemble the demo video from the storyboard in beats.py.

    python3 video/build.py renders runs/<run>   # writes video/build/renders.json (deck URLs to screenshot)
    python3 video/build.py video runs/<run>     # needs the renders and video/build/beats/vNN.mp3

The deck (video/deck.html) is screenshotted at 1920x1080 by a browser; overlays have a
transparent background. Writes video/out/demo.mp4. Needs ffmpeg with libx264.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

sys.path.insert(0, str(Path(__file__).parent))
from beats import BEATS  # noqa: E402

MODE, RUN = sys.argv[1], Path(sys.argv[2])
B = Path("video/build")
R = B / "renders"
SEG = B / "seg"
OUT = Path("video/out")
FPS, W, H = 30, 1920, 1080
LEAD, GAP, FADE = 0.4, 0.35, 0.2
DECK = "http://localhost:8766/deck.html"
ENC = ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p", "-r", str(FPS)]
UPSCALE = f"scale={W}:{H}:flags=lanczos,unsharp=5:5:0.6,setsar=1,fps={FPS}"


def turn_text(n):
    for line in (RUN / "explore.log").read_text().splitlines():
        m = re.match(rf"turn {n}: (.*?)(?: \| \[.*)?$", line)
        if m:
            text = m[1]
            if text.startswith("BUG "):
                return f"Turn {n} · Bug filed: {text.split(': ', 1)[1]}", True
            return f"Turn {n} · {text}", False
    raise ValueError(f"turn {n} not in the log")


def render(name, **params):
    """Register a deck screenshot; return its PNG path."""
    path = R / f"{name}.png"
    RENDERS[str(path)] = f"{DECK}?{urlencode(params)}"
    return path


RENDERS = {}


def plan():
    """Each beat as a list of shots: (kind, source, overlay or None, share of the beat)."""
    beats = []
    for i, (_, spec) in enumerate(BEATS):
        kind, shots = spec["kind"], []
        overlay = None
        if "overlay" in spec:
            slide, step = spec["overlay"]
            overlay = render(f"o_{slide}_{step}", slide=slide, step=step, overlay=1)
        if kind == "card":
            for step in spec["steps"]:
                shots.append(("still", render(f"c_{spec['slide']}_{step}", slide=spec["slide"],
                                              step=step), None))
        elif kind in ("clip", "tiles"):
            shots.append((kind, RUN / "videos" / f"{spec['video']}.mp4", overlay))
        elif kind == "shot":
            shots.append(("frame", RUN / "shots" / f"t{spec['turn']:03d}.png", overlay))
        elif kind == "turns":
            for n in spec["turns"]:
                text, bug = turn_text(n)
                params = dict(slide="turn", overlay=1, text=text)
                if bug:
                    params["bug"] = 1
                if spec.get("rule"):
                    params["rule"] = spec["rule"]
                shots.append(("frame", RUN / "shots" / f"t{n:03d}.png",
                              render(f"o_turn_{n}", **params)))
        beats.append((spec, shots))
    return beats


def ff(*args):
    subprocess.run(["ffmpeg", "-v", "error", "-y", *map(str, args)], check=True)


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                 "-of", "csv=p=0", str(path)], capture_output=True, text=True,
                                check=True).stdout)


def make_shot(kind, src, overlay, secs, out, spec):
    """One shot of exactly secs seconds at 1920x1080."""
    if kind == "still":
        ff("-loop", 1, "-t", secs, "-i", src, "-vf", f"scale={W}:{H},setsar=1,fps={FPS}",
           *ENC, out)
        return
    if kind == "frame":
        inputs, base = ["-loop", 1, "-t", secs, "-i", src], f"[0]{UPSCALE}[b]"
    elif kind == "clip":
        speed = duration(src) / secs  # fit the whole replay into the beat
        inputs = ["-i", src]
        base = f"[0]setpts=PTS/{max(speed, 1.0):.4f},{UPSCALE},tpad=stop_mode=clone:stop_duration={secs}[b]"
    else:  # tiles: three copies of the replay, side by side on the deck background
        speed = 1.0 if spec.get("freeze") else max(duration(src) / secs, 1.0)
        tile = (f"setpts=PTS/{speed:.4f},scale=600:338:flags=lanczos,"
                f"tpad=stop_mode=clone:stop_duration={secs}")
        if spec.get("freeze"):  # hold the last frame: the bug state
            tile = f"trim=start={duration(src) - 0.1:.2f},setpts=PTS-STARTPTS,scale=600:338:flags=lanczos,tpad=stop_mode=clone:stop_duration={secs}"
        inputs = ["-i", src]
        base = (f"color=c=0x0f1115:s={W}x{H}:r={FPS}:d={secs}[bg];[0]{tile},split=3[t1][t2][t3];"
                f"[bg][t1]overlay=40:400[x1];[x1][t2]overlay=660:400[x2];[x2][t3]overlay=1280:400,"
                f"fps={FPS}[b]")
    graph = base
    if overlay:
        inputs += ["-loop", 1, "-t", secs, "-i", overlay]
        graph += f";[b][1]overlay=0:0:format=auto[v]"
        last = "[v]"
    else:
        last = "[b]"
    ff(*inputs, "-filter_complex", graph, "-map", last, "-t", secs, *ENC, out)


def main():
    beats = plan()
    if MODE == "renders":
        R.mkdir(parents=True, exist_ok=True)
        (B / "renders.json").write_text(json.dumps(RENDERS, indent=1))
        print(len(RENDERS), "renders listed")
        return

    SEG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(exist_ok=True)
    voices = [B / "beats" / f"v{i:02d}.mp3" for i in range(len(BEATS))]
    shots, starts, t = [], [], 0.0
    for i, (spec, beat_shots) in enumerate(beats):
        length = duration(voices[i]) + GAP + (LEAD if i == 0 else 0) + spec.get("hold", 0)
        starts.append(t + (LEAD if i == 0 else 0))
        for kind, src, overlay in beat_shots:
            shots.append((kind, src, overlay, length / len(beat_shots), spec))
        t += length
    total = t

    # shots whose caption changes in place are joined by hard cuts into one unit (a crossfade
    # would overlap two texts); units are joined by crossfades
    units = []
    for n, shot in enumerate(shots):
        if n and shot[0] == "frame" and shot[2] and shots[n - 1][2] and shots[n - 1][0] == "frame":
            units[-1].append(shot)
        else:
            units.append([shot])
    paths, lengths = [], []
    for u, unit in enumerate(units):
        extra = FADE if u < len(units) - 1 else 0  # covered by the next crossfade
        parts = []
        for n, (kind, src, overlay, secs, spec) in enumerate(unit):
            out = SEG / f"u{u:03d}_{n}.mp4"
            make_shot(kind, src, overlay, secs + (extra if n == len(unit) - 1 else 0), out, spec)
            parts.append(out)
        if len(parts) == 1:
            paths.append(parts[0])
        else:
            lst = SEG / f"u{u:03d}.txt"
            lst.write_text("".join(f"file '{p.resolve()}'\n" for p in parts))
            ff("-f", "concat", "-safe", 0, "-i", lst, "-c", "copy", SEG / f"u{u:03d}.mp4")
            paths.append(SEG / f"u{u:03d}.mp4")
        lengths.append(sum(shot[3] for shot in unit))

    inputs, graph, prev, offset = [], [], "[0]", 0.0
    for p in paths:
        inputs += ["-i", p]
    for n in range(1, len(paths)):
        offset += lengths[n - 1]
        graph.append(f"{prev}[{n}]xfade=transition=fade:duration={FADE}:offset={offset:.3f}[x{n}]")
        prev = f"[x{n}]"
    ff(*inputs, "-filter_complex", ";".join(graph), "-map", prev, *ENC, SEG / "picture.mp4")

    a_inputs, mix = [], []
    for i, v in enumerate(voices):
        a_inputs += ["-i", v]
        ms = int(starts[i] * 1000)
        mix.append(f"[{i}]adelay={ms}:all=1[a{i}]")
    mix.append("".join(f"[a{i}]" for i in range(len(voices)))
               + f"amix=inputs={len(voices)}:normalize=0,apad,atrim=0:{total:.3f}[a]")
    ff(*a_inputs, "-filter_complex", ";".join(mix), "-map", "[a]", "-ar", 48000, SEG / "audio.wav")

    ff("-i", SEG / "picture.mp4", "-i", SEG / "audio.wav", "-map", "0:v", "-map", "1:a",
       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart",
       OUT / "demo.mp4")
    print(OUT / "demo.mp4", f"{duration(OUT / 'demo.mp4'):.1f} s")


if __name__ == "__main__":
    main()
