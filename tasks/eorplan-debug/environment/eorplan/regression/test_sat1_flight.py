"""Regression of eorplan against the SAT-1 flight reconstruction."""
import json
import pathlib

from eorplan.propagate import predict

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOL = {"a_km": 5.0, "e": 1e-4, "i_deg": 0.01, "mass_kg": 0.05}
EVENT_TOL_S = 30.0


def _load(name):
    return json.loads((ROOT / name).read_text())


def test_sat1_matches_flight():
    cfg = _load("configs/sat1.json")
    flight = _load("telemetry/sat1_flight.json")
    pred = predict(cfg)
    for got, ref in zip(pred["checkpoints"], flight["checkpoints"]):
        for key, tol in TOL.items():
            assert abs(got[key] - ref[key]) <= tol, (ref["day"], key, got[key], ref[key])
    assert [k for _, k in pred["eclipse_events"]] == [k for _, k in flight["eclipse_events"]]
    worst = max(abs(a[0] - b[0]) for a, b in zip(pred["eclipse_events"], flight["eclipse_events"]))
    assert worst <= EVENT_TOL_S, worst
