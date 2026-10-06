#!/bin/bash
# Usage: CLAUDE_CODE_OAUTH_TOKEN=... ./scripts/run_all.sh
# Agent/model/effort follow the Klavis brief; check .github/harbor-run-defaults.yml
# in the TB repo before running (see README "Agent configuration").
set -euo pipefail
T=tasks/electric-orbit-raising
mkdir -p results

# 1. static checks (run from a terminal-bench checkout: TB=/path/to/terminal-bench)
for c in "$TB"/scripts/checks/check-*.sh; do bash "$c" "$PWD/$T"; done 2>&1 | tee results/static-checks.log

# 2. implementation rubric
harbor check "$T" -r "$TB/docs/prompts/task-implementation.toml" 2>&1 | tee results/rubric.log

# 3. oracle + nop
harbor run -p "$T" --agent oracle 2>&1 | tee results/oracle.log
harbor run -p "$T" --agent nop    2>&1 | tee results/nop.log

# 4. standard trials: 3 x codex, 3 x claude-code
harbor run -p "$T" -k 3 --agent codex --model openai/gpt-6.1-sol \
  --env docker --yes --ae CODEX_FORCE_AUTH_JSON=1 --ak reasoning_effort=xhigh 2>&1 | tee results/run-codex.log
harbor run -p "$T" -k 3 --agent claude-code --model anthropic/claude-opus-5.5 \
  --env docker --yes --ae CLAUDE_FORCE_OAUTH=1 --ae CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
  --ae CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000 --ak reasoning_effort=max 2>&1 | tee results/run-claude.log

# 5. adversarial trials: 1 x each
C=$(./scripts/make_cheat_variant.sh)
harbor run -p "$C" --agent codex --model openai/gpt-6.1-sol \
  --env docker --yes --ae CODEX_FORCE_AUTH_JSON=1 --ak reasoning_effort=xhigh 2>&1 | tee results/cheat-codex.log
harbor run -p "$C" --agent claude-code --model anthropic/claude-opus-5.5 \
  --env docker --yes --ae CLAUDE_FORCE_OAUTH=1 --ae CLAUDE_CODE_OAUTH_TOKEN="$CLAUDE_CODE_OAUTH_TOKEN" \
  --ae CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000 --ak reasoning_effort=max 2>&1 | tee results/cheat-claude.log
