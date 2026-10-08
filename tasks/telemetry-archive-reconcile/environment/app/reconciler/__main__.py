"""Entry point: python -m reconciler"""
import json
import pickle

from . import _durable as d
from .core import Reconciler

SNAPSHOT_EVERY = 200


def main():
    raw = d.get("snapshot")
    rec = pickle.loads(raw) if raw else Reconciler()
    sent = len(rec.audit)
    count = 0
    while True:
        ev = d.poll()
        if ev is None:
            break
        rec.process(ev)
        for a in rec.audit[sent:]:
            d.emit(a["seqno"], a)
        sent = len(rec.audit)
        d.ack(ev["i"])
        count += 1
        if count % SNAPSHOT_EVERY == 0:
            d.put("snapshot", pickle.dumps(rec))
    d.write_output("archive.json", json.dumps(rec.archive()).encode())


main()
