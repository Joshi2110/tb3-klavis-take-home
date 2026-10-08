# Terminal-Bench 3 take-home — Klavis AI

This repo holds my Terminal-Bench 3 take-home for Klavis AI. I built five tasks end to end. Each one has a working oracle and a failing nop, and each one was solved by a frontier agent at the settings Klavis approved. The central requirement, that every standard trial fails, is therefore not met.

What the repo does show is how each task was designed and verified, every trial I ran with its exact command, and a measured account of why each design fell. The submitted task is `tasks/telemetry-archive-reconcile` (v5); the earlier ones are under `archive/`.

## Status against the assignment

| Requirement | Status | Evidence |
|---|---|---|
| Static checks | **Met** | `results/01-checks.md` |
| Implementation rubric | **Met** (all criteria pass, Opus 5.5 review) | `results/01-checks.md` |
| Docker build, oracle = 1, nop = 0 | **Met** (v5: oracle 1.0, nop 0.0) | `results/02-oracle-nop.md` |
| `/run`: 3 trials per config, all fail | **Not met**: Codex solved v5 on trial 1 | `results/03-run-trials.md` |
| `/cheat`: 1 trial per config, reward 0 | Partial: Codex 0.0 by safety refusal; Claude not run | `results/04-cheat-trials.md` |

## Configurations

- Codex: `openai/gpt-6-astra`, `reasoning_effort=xhigh`. The assignment names gpt-6.1-sol, which Codex rejects on a ChatGPT account; Xiangkai confirmed by email on 2026-10-06 that gpt-6 astra results are accepted.
- Claude Code: `anthropic/claude-opus-5-5`, `reasoning_effort=max` (used on v1 and v2; not run on v4/v5, see `results/03-run-trials.md`).

## Tasks in this repo

| Version | Task | Location | Outcome |
|---|---|---|---|
| v1 | electric-orbit-raising | `archive/electric-orbit-raising/` | solved by Opus 5.5 |
| v2 | eorplan-debug | `archive/eorplan-debug/` | solved by Opus 5.5 and GPT-6 Astra |
| v3 | snowmelt-runoff-prediction | `archive/snowmelt-runoff-prediction/` | solved by GPT-6 Astra |
| v4 | telemetry-archive-reconcile, before provisional decisions | superseded by v5 (differences in `results/05-failure-analysis.md`) | solved by GPT-6 Astra |
| v5 | telemetry-archive-reconcile | `tasks/telemetry-archive-reconcile/` | solved by GPT-6 Astra |

## Reproduce

```bash
source ~/.tbvenv/bin/activate; export TB=~/terminal-bench
for c in $TB/scripts/checks/check-*.sh; do bash "$c" "$PWD/tasks/telemetry-archive-reconcile"; done
harbor run -p tasks/telemetry-archive-reconcile --agent oracle
harbor run -p tasks/telemetry-archive-reconcile --agent nop
caffeinate -i harbor run -p tasks/telemetry-archive-reconcile -k 1 -n 1 --job-name <name> \
  --agent codex --model openai/gpt-6-astra --env docker --yes \
  --ae CODEX_FORCE_AUTH_JSON=yes --ak reasoning_effort=xhigh
```

## What I learned

The same thing happened five times. Once the specification is complete enough to pass the TB3 rubric, a frontier agent builds its own reference from it and checks its work against that reference. This held for optimal control (v1), spec-driven debugging (v2), extrapolation to a hidden hydrological regime (v3) and a crash-safe state machine (v4).

For v5 I added a rule that only fires on paths no visible scenario exercises. It slowed Codex down, from about 5 minutes of work to about 28, but Codex implemented the rule correctly anyway. A rule that is written down plainly gets implemented, tested or not.

If I continued, I would build a task whose verifier checks invariants instead of comparing with a reference output, and where the agent has to make a tradeoff that the spec constrains without dictating it. Details are in `results/05-failure-analysis.md` and `results/06-design-history.md`.
