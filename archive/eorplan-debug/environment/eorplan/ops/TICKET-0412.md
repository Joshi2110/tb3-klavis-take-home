# TICKET-0412 — eorplan predictions disagree with flight data

Reporter: Flight Dynamics, constellation ops
Priority: high

eorplan is used to plan the orbit-raising campaigns of the whole fleet and
its predictions no longer match what we fly.

- SAT-1: the regression test against the reconstructed flight data
  (`regression/test_sat1_flight.py`, data in `telemetry/sat1_flight.json`)
  is red. The eclipse event times are the most visibly off.
- SAT-2 (`configs/sat2.json`): we do not have a clean reconstruction yet,
  but at day 20 the orbit determination put the semi-major axis about
  130 km above the eorplan prediction, and the gauged propellant mass was
  about 8 kg higher than predicted.

Please bring eorplan in line with the model specification
(`docs/SPEC.md`). We will check it against flight data from several other
spacecraft (different power systems, launch seasons and orbits) before
using it for the next campaign. The steering law (`eorplan/guidance.py`)
is flight code and must not be touched; the CLI and output format must
stay as they are.
