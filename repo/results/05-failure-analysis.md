# Analysis: why the tasks were solved

## v4: first try, no iteration
Trajectory: Codex read the starting code, `_durable.py` and the harness, wrote
an engine, and its first three harness runs (each with 6 random crashes) all
passed. No audit diff appears in the transcript. The specification reduced
every decision to a closed-form rule, so the engine could be written directly
from it.

## v5: slowed down, not stopped
v5 removed the guarantee that deadline decisions are always right and added a
rule that provisional decisions are reopened when later evidence contradicts
them, from three sources (a BOOTLOG, a proof that raises coverage, an attached
delivery). No visible scenario contains a contradiction. Four hand-written
"natural" variants that each miss one source pass every visible scenario and
fail at least one hidden family. Codex took about 28 minutes instead of about
5, and implemented all of it.

## Common cause
The rubric asks for a complete specification, and a complete specification is
exactly what lets a strong agent succeed. In every trajectory the agent read
the spec, wrote its own implementation or reference, and then used the visible
material only to confirm. v2 showed it first (all four defects fixed in 3.4
minutes by comparing spec and code line by line), v4 showed it most clearly
(first harness runs green, with crashes), and v5 showed that hiding the
relevant cases from the visible tests is not enough when the rule itself is
written down.

This matches the view of a domain expert I consulted: current agents beat
experts on well-defined problems with a clear answer, and still need guidance
when a problem calls for tradeoffs or judgement.

## Comparison with a design that held
A public durable-outbox take-home obtained 6/6 failures on the previous model
generation (gpt-5.6-sol and Opus 5, August 2026). Differences: invariant-based verification rather
than exact reference output; agents' own tests did not enforce the legal
transition whitelist; hidden schedules chosen by fuzzing against engines that
had solved an earlier version; two opposing requirements that force a
tradeoff, with agents failing in both directions.
