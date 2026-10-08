# Static checks and implementation rubric (v5, final)

## Static checks
All `scripts/checks/check-*.sh` pass on `tasks/telemetry-archive-reconcile`
(raw output: `results/raw/checks.txt`): canary strings, instruction ending,
internet settings, pinned installs, no bare nproc, separate verifier mode,
required task.toml fields and README sections, task name, timeouts within the
8 h cap, no trial-time fetches, verifier tooling baked into the image.

Fixes needed along the way: separate verifier mode (tests/Dockerfile and
`artifacts = ["/app/reconciler"]`), canary lines, absolute paths and the
canonical last line in instruction.md, `category = "Software"`, and the
`## Task Metadata` section in the README format the checker parses.

## Implementation rubric
`harbor check` with `task-implementation.toml`, Claude Code, Opus 5.5
(job `2026-10-08__10-43-59`, cost $0.86): every criterion passes;
Artifact Efficiency is not applicable (raw output: `results/raw/rubric.txt`).

A first review (job `2026-10-07__16-40-47`) failed 7 criteria, all fixed:
difficulty explanation (real-world role, synthetic data statement),
verification explanation and README (wrong scenario count), category, stray
`__pycache__`, verifier execution isolation (root-only `/logs/verifier`,
cleanup of agent processes before the reward is written), and CTRF reporting.

Two earlier attempts with Sonnet 5 produced no result file. Harbor looks for
`/app/check-result.json` (artifact manifest of job `2026-10-07__16-10-00`);
in at least one of them the reviewing agent reported writing it under
`/app/task/` instead. A third attempt failed on an expired OAuth token (401).
