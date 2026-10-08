"""Archive reconciliation logic.

Frames are grouped by payload hash. The counter is unwrapped against the last
counter value seen in the current boot; an OBT regression is taken as a reboot.
"""

MOD = 16384
PERIOD = 250


class Reconciler:
    def __init__(self):
        self.boot = 0
        self.wraps = 0
        self.last_vc = None
        self.last_obt = None
        self.records = {}      # hash -> record
        self.deliveries = {}   # (station, rx_time, vc) -> hash
        self.audit = []

    def _log(self, i, rec, frm, to, cause):
        ident = to == "ARCHIVED" or (frm == "ARCHIVED" and to == "RETRACTED")
        self.audit.append({
            "seqno": len(self.audit), "event": i, "rid": rec["rid"],
            "from": frm, "to": to, "cause": cause,
            "boot": rec["boot"] if ident else None,
            "seq": rec["seq"] if ident else None,
            "hash": rec["hash"],
        })

    def _identify(self, vc, obt):
        if obt is not None and self.last_obt is not None and obt < self.last_obt:
            self.boot += 1
            self.wraps = 0
            self.last_vc = None
        if self.last_vc is not None and vc < self.last_vc - MOD // 2:
            self.wraps += 1
        self.last_vc = vc
        if obt is not None:
            self.last_obt = obt
        return self.boot, vc + MOD * self.wraps

    def process(self, ev):
        i, t = ev["i"], ev["type"]
        if t in ("FRAME", "PLAYBACK"):
            key = (ev["station"], ev["rx_time"], ev["vc"])
            self.deliveries[key] = ev["hash"]
            if ev["hash"] in self.records:
                return
            rec = {"rid": i, "hash": ev["hash"], "state": "SEEN", "boot": None, "seq": None}
            self.records[ev["hash"]] = rec
            self._log(i, rec, None, "SEEN", "DELIVERY")
            rec["boot"], rec["seq"] = self._identify(ev["vc"], ev["obt"])
            rec["state"] = "ARCHIVED"
            self._log(i, rec, "SEEN", "ARCHIVED", "PROOF")
        elif t == "RETRACT":
            h = self.deliveries.get((ev["station"], ev["ref_rx_time"], ev["vc"]))
            rec = self.records.get(h)
            if rec and rec["state"] == "ARCHIVED":
                rec["state"] = "RETRACTED"
                self._log(i, rec, "ARCHIVED", "RETRACTED", "RETRACT")
        # BOOTLOG and TICK: nothing to do yet

    def archive(self):
        rows = [{"boot": r["boot"], "seq": r["seq"], "hash": r["hash"]}
                for r in self.records.values() if r["state"] == "ARCHIVED"]
        return sorted(rows, key=lambda x: (x["boot"], x["seq"]))
