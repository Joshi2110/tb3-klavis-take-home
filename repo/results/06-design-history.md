# Design history

I started from the domains I know best (orbital mechanics, numerical
optimisation, physics-based modelling) and moved toward systems engineering as
each design fell. Every candidate went through the same filter before a paid
trial: build the oracle, check that nop fails, and try cheap baselines to see
whether the problem has an easy way out. Five candidates were dropped at that
stage; five reached a trial.

## v1 electric-orbit-raising
Minimum-propellant low-thrust GTO→GEO transfer with J2 and eclipses; independent
RK4 verifier at two step sizes. Oracle: Q-law + multiple shooting (IPOPT),
1323.7 kg final mass; threshold 1310 kg; rubric all green.
Result: Opus 5.5 solved it with 1330.84 kg (beat the oracle); first valid file
at 17 min. Costates + Gauss-Newton, then an averaged supersynchronous optimum;
the agent wrote three independent verifiers of its own.
Lesson: with threshold optimisation the oracle's quality is uncertain, and
moving the threshold to the agent's score would be adversarial selection.

## Prototypes discarded without a trial
- Robust guidance: Q-law is already a robust feedback law; falls back to a mass
  threshold; executing agent code in the verifier opens a cheat surface.
- Earth–Moon CR3BP low-thrust L1→L2 Lyapunov: direct transcription + IPOPT
  from a straight-line guess is feasible in 4 min.
- Light-curve attitude inversion: naive multistart finds the truth in 1 of 300
  starts; no trapping local minima.
- PINN on reconstructed Haas & Gallimore data: Vp identical at the 5 radii (a
  copy scores zero error); radial structure is a reconstruction artefact.
- Hydrology, snow years (Fish River, USGS 01013500 + Daymet): HBV NSE 0.90 vs
  gradient boosting 0.85, margin too small.

## v2 eorplan-debug
Mission-analysis tool with 4 coupled defects (J2000 epoch, Kaula normalisation,
kW vs W, efficiency counted twice), a pair (B+D) that cancels on telemetry, a
decoy, runuser isolation, symlink hole closed.
Result: Opus 5.5 solved it in 16 min, GPT-6 Astra in 6 min. All four fixes at
3.4 min by line-by-line spec/code comparison, then a clean reimplementation and
80 random configurations.
Lesson: once the spec defines the behaviour, every spec-defined defect is
detectable by self-verification.

## v3 snowmelt-runoff-prediction
Discharge visible only mid-July to November; predict the March–June melt. Real
anonymised data. Oracle HBV with snow priors: weekly NSE 0.70, volume error
9.3%. Statistical baselines: NSE −0.5, volume error 72%.
Result: GPT-6 Astra solved it in 23 min with NSE 0.86 and volume error 8.3%
(beat the oracle): ensemble of conceptual models, explicit treatment of snow
parameter non-identifiability, sensitivity analysis, backward correction from
July.
Lesson: extrapolation to a hidden regime no longer traps current models.

## v4 telemetry-archive-reconcile
Ground-segment archive reconciler: multi-station passes, recorder playback,
14-bit counter wrap vs reboot ambiguity, retractions, crash/restart with
at-least-once delivery and exactly-once audit. Two opposing requirements (never
guess, always drain). Verifier: exact audit stream vs reference, 22 scenarios
regenerated from seeds, 169 crash/restart runs.
Result: GPT-6 Astra solved it, first try (see 05).

## v5 telemetry-archive-reconcile + provisional decisions
See 05. Solved by GPT-6 Astra in about 28 minutes of agent time.
