# Oracle and nop

| Task | Run | Reward | Notes |
|---|---|---|---|
| v4 | nop (Docker) | 0.0 | 3m 12s |
| v4 | oracle (local, verifier outside Docker) | pass | 22 scenarios, 169 crash/restart runs, 0 failures |
| v5 | oracle (Docker), job `v5-oracle` | 1.0 | 10m 49s; 30 scenarios, 180 crash/restart runs, 0 failures |
| v5 | nop (Docker), job `v5-nop` | 0.0 | 6m 39s |
| v5 final (after rubric fixes) | oracle (Docker), job `v5-oracle-3` | 1.0 | 10m 07s; 30 scenarios, 180 crash/restart runs, 0 failures |
| v5 final (after rubric fixes) | nop (Docker), job `v5-nop-3` | 0.0 | 6m 13s of trial time |

The v5 verifier runs in a separate container (`environment_mode = "separate"`),
receives only `/app/reconciler` as an artifact, regenerates its 30 scenarios
from seeds, and runs the reconciler as an unprivileged user.

After the implementation-rubric review, the verifier was hardened (root-only
`/logs/verifier`, per-run process-group cleanup, final cleanup of every
process of user `recon` before the reward is written, CTRF report at
`/logs/verifier/ctrf.json`). A first version killed every `recon` process after
each run, which also killed concurrent runs and made the oracle fail
(`v5-oracle-2`, reward 0.0); it was fixed before the final runs above.
