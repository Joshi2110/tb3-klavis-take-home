"""Reference reconciler: event log in durable storage, deterministic replay.

Per event: put(ev/n) -> process -> emit this event's audit records -> ack.
On restart: replay the logged events through the engine, re-emit the audit
records of the last logged event (its emits may have been cut short), then
resume polling. A redelivered event that is already logged is only acked.
"""
import json

from . import _durable as d
from .engine import Engine


def main():
    eng = Engine()
    n = 0
    last = []
    while True:
        raw = d.get(f"ev/{n}")
        if raw is None:
            break
        before = len(eng.audit)
        eng.process(json.loads(raw))
        last = eng.audit[before:]
        n += 1
    for a in last:
        d.emit(a["seqno"], a)

    while True:
        ev = d.poll()
        if ev is None:
            break
        if ev["i"] < n:
            d.ack(ev["i"])
            continue
        d.put(f"ev/{n}", json.dumps(ev, separators=(",", ":")).encode())
        before = len(eng.audit)
        eng.process(ev)
        n += 1
        for a in eng.audit[before:]:
            d.emit(a["seqno"], a)
        d.ack(ev["i"])

    d.write_output("archive.json", json.dumps(eng.archive(), separators=(",", ":")).encode())


main()
