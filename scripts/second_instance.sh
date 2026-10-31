#!/usr/bin/env bash
# Starts the second editor instance and its PIE with no clicks, then waits until the harness
# answers on Remote Control. Safe to rerun: it reuses an editor already up on the MCP port.
# Usage: scripts/second_instance.sh [map]   (map defaults to Vault)
set -euo pipefail
map=${1:-Vault}
repo=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
project_win='C:\UnrealProjects\PlaytestArena2\PlaytestArena.uproject'
editor='C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe'
mcp="python3 $repo/scripts/editor_mcp.py --port 8001"
rc=http://127.0.0.1:30011

if ! $mcp editor_toolset.toolsets.scene.SceneTools get_current_level >/dev/null 2>&1; then
  echo "launching the second editor"
  powershell.exe -NoProfile -Command "Start-Process -FilePath '$editor' -ArgumentList '\"$project_win\"'"
  for _ in $(seq 120); do  # first launch may compile shaders
    $mcp editor_toolset.toolsets.scene.SceneTools get_current_level >/dev/null 2>&1 && break
    sleep 5
  done
fi
$mcp editor_toolset.toolsets.scene.SceneTools get_current_level >/dev/null || {
  echo "second editor never answered on MCP port 8001" >&2; exit 1; }

if ! $mcp EditorToolset.EditorAppToolset IsPIERunning | grep -q true; then
  $mcp editor_toolset.toolsets.scene.SceneTools load_level "{\"level_path\": \"/Game/Maps/$map\"}"
  # "PIE ended before warmup" is reported even when PIE keeps running: the harness check decides
  $mcp EditorToolset.EditorAppToolset StartPIE \
    '{"options": {"bSimulate": false, "playMode": "PlayMode_InViewPort", "warmupSeconds": 0}}' || true
fi

harness="/Game/Maps/UEDPIE_0_$map.$map:PersistentLevel.BP_TestHarness_C_0"
for _ in $(seq 30); do
  if (cd "$repo/agent" && UE_RC_URL=$rc UE_HARNESS_PATH="$harness" \
      python3 -c "import ue; ue.state()") >/dev/null 2>&1; then
    echo "second instance ready: $map playing, Remote Control on $rc"; exit 0
  fi
  sleep 2
done
echo "harness never answered on $rc (check the port settings in PlaytestArena2/Config)" >&2
exit 1
