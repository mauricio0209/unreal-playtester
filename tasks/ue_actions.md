# Task: extend `agent/ue.py` with the remaining harness actions

Edit only `agent/ue.py` and `agent/test_ue.py`. Python 3.14, standard library only. Keep the
existing style and keep all existing tests passing. Run `python3 agent/test_ue.py` before
finishing.

## Harness contract (Unreal side, already decided)

All calls go through the existing `call(function, **params)`.

| Blueprint function | Params | Notes |
|---|---|---|
| `MoveTo` | `X`, `Y` (float) | Sets a walk target; the pawn walks during the next `Step`. |
| `Jump` | none | Takes effect during the next `Step`. |
| `LookAt` | `X`, `Y`, `Z` (float) | Turns the camera toward a world point immediately. |
| `Interact` | none | Interacts with the nearest interactable within 200 cm. |
| `Screenshot` | none | Writes a PNG asynchronously (about one frame later) into the screenshot folder. |
| `ResetLevel` | none | Reloads the level. The harness is destroyed and recreated; calls fail with HTTP errors while it loads. |

`GetState()` returns:
`StepId` int, `bStepping` bool, `PawnAlive` bool, `PlayerLocation` {X,Y,Z}, `Velocity` {X,Y,Z},
`LastZ` float, `KillZ` float, `bIsFalling` bool, `InventoryCount` int, `BootTime` float
(differs after every level load), `ActorStates` {name: str}, `ActorLocations` {name: {X,Y,Z}}.

## Add to `agent/ue.py`

```python
SCREENSHOT_DIR  # Path from env UE_SCREENSHOT_DIR, default
                # /mnt/c/UnrealProjects/unreal-playtester/unreal/PlaytestArena/Saved/Screenshots/WindowsEditor

def move_to(x: float, y: float) -> None
def jump() -> None
def look_at(x: float, y: float, z: float) -> None
def interact() -> None

def screenshot(timeout: float = 10.0) -> Path
    # Note the PNGs already in SCREENSHOT_DIR (create the dir if missing), call("Screenshot"),
    # then wait for a new *.png whose size is non-zero and unchanged across two polls 0.1 s
    # apart. Return its path. Raise UEError on timeout.

def reset(timeout: float = 60.0) -> dict
    # Read BootTime from state(), call("ResetLevel"), then poll state() every 0.25 s,
    # ignoring UEError while the level loads, until BootTime differs from the old value.
    # Return that state. Raise UEError on timeout.
```

## Tests to add (extend the existing fake server)

1. Each action sends the right `functionName` and `parameters`.
2. `screenshot` returns the new file when the fake server writes a PNG into a temp
   `SCREENSHOT_DIR` after a short delay, and ignores PNGs that existed before the call.
3. `screenshot` raises `UEError` when no file appears.
4. `reset` returns the new state when the fake server answers HTTP 500 for a few polls and
   then reports a new `BootTime`.

Do not touch any other file.
