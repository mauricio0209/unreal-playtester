"""Tiny Remote Control client for BP_TestHarness (stdlib only)."""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("UE_RC_URL", "http://127.0.0.1:30010")
HARNESS_PATH = os.environ.get("UE_HARNESS_PATH", "/Game/Maps/UEDPIE_0_Arena.Arena:PersistentLevel.BP_TestHarness_C_0")
SCREENSHOT_DIR = Path(
    os.environ.get(
        "UE_SCREENSHOT_DIR",
        "/mnt/c/UnrealProjects/unreal-playtester/unreal/PlaytestArena/Saved/Screenshots/WindowsEditor",
    )
)
_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))  # RC is localhost: bypass proxy


class UEError(Exception):
    pass


def call(function: str, **params) -> dict:
    body = json.dumps(
        {
            "objectPath": HARNESS_PATH,
            "functionName": function,
            "parameters": params,
            "generateTransaction": False,
        }
    ).encode()
    req = urllib.request.Request(
        BASE_URL + "/remote/object/call",
        data=body,
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    try:
        with _OPENER.open(req, timeout=10) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        raise UEError(f"HTTP {e.code}: {e.read().decode()}") from e
    except (urllib.error.URLError, OSError) as e:
        raise UEError(f"connection failed: {e}") from e


def state() -> dict:
    return call("GetState")


def move_to(x: float, y: float) -> None:
    call("MoveTo", X=x, Y=y)


def jump() -> None:
    call("Jump")


def look_at(x: float, y: float, z: float) -> None:
    call("LookAt", X=x, Y=y, Z=z)


def set_camera(mode: str) -> None:
    """Runs the console command `camera <mode>`: "freecam" (chase view) or "default"."""
    call("SetCamera", Mode=mode)


def interact() -> None:
    call("Interact")


def screenshot(timeout: float = 10.0) -> Path:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    before = {p.name for p in SCREENSHOT_DIR.glob("*.png") if p.is_file()}
    call("Screenshot")
    deadline = time.monotonic() + timeout
    while True:
        for p in sorted(SCREENSHOT_DIR.glob("*.png")):
            if p.name in before or not p.is_file():
                continue
            try:
                size1 = p.stat().st_size
            except OSError:
                continue
            if size1 == 0:
                continue
            time.sleep(0.1)
            try:
                size2 = p.stat().st_size
            except OSError:
                continue
            if size2 != 0 and size2 == size1:
                return p
        if time.monotonic() >= deadline:
            raise UEError(f"screenshot timed out after {timeout}s")
        time.sleep(0.05)


def reset(timeout: float = 60.0) -> dict:
    old = state()["BootTime"]
    call("ResetLevel")
    deadline = time.monotonic() + timeout
    while True:
        try:
            s = state()
        except UEError:
            pass
        else:
            if s["BootTime"] != old:
                return s
        if time.monotonic() >= deadline:
            raise UEError(f"reset timed out after {timeout}s")
        time.sleep(0.25)


def step(seconds: float, timeout: float = 30.0) -> dict:
    start = state()["StepId"]
    call("Step", Seconds=seconds)
    deadline = time.monotonic() + timeout
    while True:
        s = state()
        if s["StepId"] > start and not s["bStepping"]:
            return s
        if time.monotonic() >= deadline:
            raise UEError(f"step timed out after {timeout}s")
        time.sleep(0.05)
