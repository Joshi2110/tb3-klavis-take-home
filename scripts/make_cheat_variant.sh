#!/bin/bash
# Builds the /cheat variant locally: same task, with the TB3 CI adversarial prompt
# (docs/prompts/hack-trial-prompt.md) placed after the task instruction, as in CI.
# The copy lives outside tasks/ so the real task never contains cheat material.
set -euo pipefail
SRC=tasks/electric-orbit-raising
DST=/tmp/tb3-cheat/electric-orbit-raising
rm -rf /tmp/tb3-cheat && mkdir -p /tmp/tb3-cheat
cp -r "$SRC" "$DST"
{ cat "$SRC/instruction.md"; echo; cat scripts/hack-trial-prompt.md; } > "$DST/instruction.md"
echo "$DST"
