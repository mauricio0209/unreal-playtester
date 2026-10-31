"""Tests for replay_video.py. Run: python3 agent/test_replay_video.py"""

import shutil
import struct
import tempfile
import zlib
from pathlib import Path

import replay_video


def write_png(path, width, height, r, g, b):
    def chunk(ctype, data):
        piece = ctype + data
        return (struct.pack(">I", len(data)) + piece +
                struct.pack(">I", zlib.crc32(piece) & 0xffffffff))

    raw = b"".join(b"\x00" + bytes((r, g, b)) * width
                   for _ in range(height))
    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2,
                                      0, 0, 0)) +
           chunk(b"IDAT", zlib.compress(raw)) +
           chunk(b"IEND", b""))
    Path(path).write_bytes(png)


class FakeUE:
    def __init__(self, engine_dir):
        self.engine_dir = Path(engine_dir)
        self.engine_dir.mkdir(parents=True, exist_ok=True)
        self.resets = 0
        self.step_calls = []
        self.move_to_calls = []
        self.look_at_calls = []
        self.jumps = 0
        self.interacts = 0
        self.shots = 0

    def reset(self):
        self.resets += 1
        return {"ok": True}

    def step(self, seconds):
        self.step_calls.append(seconds)
        return {"ok": True}

    def move_to(self, x, y):
        self.move_to_calls.append((x, y))

    def look_at(self, x, y, z):
        self.look_at_calls.append((x, y, z))

    def jump(self):
        self.jumps += 1

    def interact(self):
        self.interacts += 1

    def screenshot(self):
        self.shots += 1
        path = self.engine_dir / f"shot_{self.shots:04d}.png"
        write_png(path, 64, 36, self.shots % 256, 100, 200)
        return path


def has_ffmpeg():
    return shutil.which("ffmpeg") is not None


def run_record(ue, steps, out_dir, name, **kwargs):
    try:
        return replay_video.record(ue, steps, out_dir, name, **kwargs)
    except FileNotFoundError as exc:
        if not has_ffmpeg():
            print(f"note: skipping encoding asserts ({exc})")
            return None
        raise


def t_chunk_exact():
    with tempfile.TemporaryDirectory() as tmp:
        ue = FakeUE(Path(tmp) / "engine")
        out = Path(tmp) / "out"
        result = run_record(ue, [{"action": "step", "seconds": 1.0}],
                            out, "bug1", chunk_s=0.2, fps=10)
        assert len(ue.step_calls) == 5, ue.step_calls
        for call in ue.step_calls:
            assert abs(call - 0.2) < 1e-9, ue.step_calls
        if result is None:
            return
        assert result["frames"] == 6, result
        assert result["mp4"].is_file() and result["mp4"].stat().st_size > 0
        assert result["gif"].is_file() and result["gif"].stat().st_size > 0
        assert not (out / "bug1_frames").exists()


def t_chunk_remainder():
    with tempfile.TemporaryDirectory() as tmp:
        ue = FakeUE(Path(tmp) / "engine")
        out = Path(tmp) / "out"
        result = run_record(ue, [{"action": "step", "seconds": 0.5}],
                            out, "bug1", chunk_s=0.2, fps=10)
        assert len(ue.step_calls) == 3, ue.step_calls
        expected = [0.2, 0.2, 0.1]
        for got, want in zip(ue.step_calls, expected):
            assert abs(got - want) < 1e-9, ue.step_calls
        assert abs(sum(ue.step_calls) - 0.5) < 1e-9, ue.step_calls
        if result is None:
            return
        assert result["frames"] == 4, result
        assert result["mp4"].stat().st_size > 0
        assert result["gif"].stat().st_size > 0
        assert not (out / "bug1_frames").exists()


def t_frames_and_forwarding():
    with tempfile.TemporaryDirectory() as tmp:
        ue = FakeUE(Path(tmp) / "engine")
        out = Path(tmp) / "out"
        steps = [
            {"action": "move_to", "x": 10, "y": 20},
            {"action": "step", "seconds": 1.0},
            {"action": "jump"},
            {"action": "interact"},
            {"action": "look_at", "x": 1, "y": 2, "z": 3},
        ]
        result = run_record(ue, steps, out, "bug2", chunk_s=0.2, fps=10)
        assert ue.resets == 1, ue.resets
        assert ue.move_to_calls == [(10, 20)], ue.move_to_calls
        assert ue.look_at_calls == [(1, 2, 3)], ue.look_at_calls
        assert ue.jumps == 1, ue.jumps
        assert ue.interacts == 1, ue.interacts
        assert len(ue.step_calls) == 5, ue.step_calls
        if result is None:
            return
        assert result["frames"] == 6, result
        assert result["mp4"].is_file() and result["mp4"].stat().st_size > 0
        assert result["gif"].is_file() and result["gif"].stat().st_size > 0
        assert not (out / "bug2_frames").exists()
        leftovers = list(ue.engine_dir.glob("*.png"))
        assert leftovers == [], leftovers


def main():
    tests = sorted((name, fn) for name, fn in globals().items()
                   if name.startswith("t_") and callable(fn))
    for name, fn in tests:
        fn()
        print(f"{name} ok")
    print(f"all {len(tests)} tests passed")


if __name__ == "__main__":
    main()
