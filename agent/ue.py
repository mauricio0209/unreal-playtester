"""Tiny Remote Control client for BP_TestHarness (stdlib only)."""

import json
import os
import time
import urllib.error
import urllib.request

BASE_URL = os.environ.get("UE_RC_URL", "http://127.0.0.1:30010")
HARNESS_PATH = os.environ.get("UE_HARNESS_PATH", "/Game/Maps/UEDPIE_0_Arena.Arena:PersistentLevel.BP_TestHarness")
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
