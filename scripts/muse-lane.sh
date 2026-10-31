#!/usr/bin/env bash
# Runs one Muse Code task in its own git worktree under bubblewrap, so Muse cannot see
# /mnt/c (the real repo and its .env), /tmp, or other tools' credentials. Only the repo's
# .git is exposed so the worktree works; .env was never committed.
# Usage: scripts/muse-lane.sh <lane> <tasks/file.md> [model]
set -euo pipefail
lane=$1 task=$2 model=${3:-muse-spark-1.3-contributor}
repo=$(git rev-parse --show-toplevel)
wt=$HOME/projects/pt-wt/$lane
[ -d "$wt" ] || git -C "$repo" worktree add -q -b "muse/$lane" "$wt" HEAD
mkdir -p "$(dirname "$wt/$task")" && cp "$repo/$task" "$wt/$task"  # the task file may be uncommitted

exec bwrap --ro-bind / / --dev /dev --proc /proc \
  --tmpfs /mnt/c --tmpfs /tmp --tmpfs "$HOME/.claude" --tmpfs "$HOME/.config/gh" \
  --bind "$repo/.git" "$repo/.git" --bind "$wt" "$wt" \
  --bind "$HOME/.config/muse" "$HOME/.config/muse" \
  --bind "$HOME/.local/share/muse" "$HOME/.local/share/muse" \
  --chdir "$wt" \
  muse exec --model "$model" --reasoning-effort medium --no-foreign-personal-context \
    --disable-web-tools --prompt-file "$task"
