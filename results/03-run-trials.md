# Standard trials (/run)

| Task | Agent / model | Job | Wall time | Reward | Verifier |
|---|---|---|---|---|---|
| v1 | claude-code / opus-5-5 max | local job | first valid file at 17 min | 1.0 | 1330.84 kg final mass vs 1310 kg threshold (oracle 1323.7 kg) |
| v2 | claude-code / opus-5-5 max | local job | 16 min | 1.0 | all four defects fixed |
| v2 | codex / gpt-6-astra xhigh | local job | 6 min | 1.0 | all four defects fixed |
| v3 | codex / gpt-6-astra xhigh | local job | 23 min | 1.0 | weekly NSE 0.86, volume error 8.3% (oracle 0.70, 9.3%) |
| v4 | codex / gpt-6-astra xhigh | `tar-codex-1` | 16m 04s | 1.0 | 22/22 scenarios, 169 crash runs, 0 failed |
| v5 | codex / gpt-6-astra xhigh | `tar-v5-codex-1` | 34m 43s (agent ~28 min) | 1.0 | 30/30 scenarios, 180 crash runs, 0 failed |

Commands follow the pattern in the root README (`harbor run -p <task> -k 1 -n 1
--agent <agent> --model <model> --env docker --yes ...`); Claude Code runs add
`--ae CLAUDE_FORCE_OAUTH=1 --ae CLAUDE_CODE_OAUTH_TOKEN=... --ae
CLAUDE_CODE_MAX_OUTPUT_TOKENS=128000 --ak reasoning_effort=max` and were run
one at a time (`-n 1`) because parallel Opus trials exhaust the subscription
rate limit. Job directories stay local (`jobs/` is git-ignored because it can
contain credentials). Task details for v1–v3 are in `06-design-history.md`.

Following the stop rule fixed before the v5 trial, no further standard trials
were run once a trial solved the task: the "all trials must fail" bar was
already out of reach and each Opus trial can use a full subscription window.

Log note: `tar-codex-1` used `CODEX_FORCE_AUTH_JSON=1`. Harbor treats keys
containing AUTH as secret and replaced every literal `1` in copied artifacts
with `[REDACTED]`; the reward in `result.json` is unaffected. Later runs use
`=yes`.
