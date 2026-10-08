"""Scenario runner: plays the harness side of SEMANTICS.md §10.

Serves events over a Unix socket (only the next unacknowledged event is ever
visible), receives audit records, kills/restarts the reconciler according to a
crash schedule, then compares the deduplicated audit stream and archive.json
with the expected outputs.

    python3 tools/harness.py scenarios/visible/v1_steady
    python3 tools/harness.py scenarios/visible/v1_steady --crash 500:before --crash 9000:after
    python3 tools/harness.py scenarios/visible/v1_steady --random-crashes 5 --seed 1
"""
import argparse
import json
import os
import random
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

CRASH_EXIT = 137


class Server:
    def __init__(self, events, path):
        self.events = events
        self.next = 0
        self.audit = []
        self.violation = None
        self.path = path
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.bind(path)
        os.chmod(path, 0o777)
        self.sock.listen(4)
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self):
        while True:
            try:
                conn, _ = self.sock.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(conn,), daemon=True).start()

    def _fail(self, msg):
        if self.violation is None:
            self.violation = msg
        return {"error": msg}

    def _handle(self, m):
        op = m.get("op")
        if op == "poll":
            return {"value": self.events[self.next] if self.next < len(self.events) else None}
        if op == "ack":
            if m.get("i") != self.next:
                return self._fail(f"ack({m.get('i')}) but next unacknowledged event is {self.next}")
            self.next += 1
            return {"value": None}
        if op == "emit":
            n, rec = m.get("seqno"), m.get("record")
            if not isinstance(n, int) or n < 0:
                return self._fail(f"bad seqno {n!r}")
            if n == len(self.audit):
                self.audit.append(rec)
            elif n < len(self.audit):
                if self.audit[n] != rec:
                    return self._fail(f"seqno {n} re-emitted with different content")
            else:
                return self._fail(f"seqno gap: got {n}, expected {len(self.audit)}")
            return {"value": None}
        return self._fail(f"unknown op {op!r}")

    def _serve(self, conn):
        with conn, conn.makefile("rb") as rf:
            for line in rf:
                try:
                    resp = self._handle(json.loads(line))
                except Exception as e:  # noqa: BLE001
                    resp = self._fail(f"bad request: {e}")
                try:
                    conn.sendall((json.dumps(resp, separators=(",", ":")) + "\n").encode())
                except OSError:
                    return

    def close(self):
        self.sock.close()


def load_jsonl(p):
    with open(p) as f:
        return [json.loads(x) for x in f if x.strip()]


def first_diff(got, want):
    for k in range(min(len(got), len(want))):
        if got[k] != want[k]:
            return f"audit[{k}]: got {got[k]} expected {want[k]}"
    return f"audit length {len(got)}, expected {len(want)}"


def run(app_dir, events, expected_audit=None, expected_archive=None, crashes=(),
        timeout=600, user=None, keep=False, python=sys.executable):
    """Run one scenario. Returns dict(ok, reason, runs, calls)."""
    work = Path(tempfile.mkdtemp(prefix="recon-"))
    for d in ("state", "out", "run"):
        (work / d).mkdir()
    if user:
        shutil.chown(work, user)
        for d in ("state", "out"):
            shutil.chown(work / d, user)
    os.chmod(work / "run", 0o755)
    server = Server(events, str(work / "run" / "harness.sock"))
    crashes = list(crashes)
    runs, calls = 0, None
    reason = None
    try:
        while True:
            runs += 1
            if runs > len(crashes) + 3:
                reason = "too many restarts"
                break
            scratch = Path(tempfile.mkdtemp(prefix="recon-tmp-"))
            if user:
                shutil.chown(scratch, user)
            env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(scratch),
                   "TMPDIR": str(scratch), "PYTHONDONTWRITEBYTECODE": "1",
                   "RECON_SOCK": server.path, "RECON_STATE": str(work / "state"),
                   "RECON_OUT": str(work / "out"),
                   "RECON_CALLS_FILE": str(scratch / "calls")}
            crash = crashes[runs - 1] if runs <= len(crashes) else None
            if crash:
                env["RECON_CRASH_AT"], env["RECON_CRASH_MODE"] = str(crash[0]), crash[1]
            cmd = [python, "-m", "reconciler"]
            if user:
                cmd = ["runuser", "-u", user, "--", "env"] + [f"{k}={v}" for k, v in env.items()] + cmd
            try:
                p = subprocess.run(cmd, cwd=app_dir, env=env, timeout=timeout,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            except subprocess.TimeoutExpired:
                reason = f"run {runs}: timeout after {timeout}s"
                break
            finally:
                cf = scratch / "calls"
                if cf.exists():
                    calls = int(cf.read_text() or 0)
                shutil.rmtree(scratch, ignore_errors=True)
            if server.violation:
                reason = f"run {runs}: protocol violation: {server.violation}"
                break
            if p.returncode == CRASH_EXIT and crash:
                continue
            if p.returncode == CRASH_EXIT and not crash:
                # crash point beyond the run's last call: nothing happened
                reason = f"run {runs}: exit {CRASH_EXIT} without a scheduled crash"
                break
            if p.returncode != 0:
                tail = p.stderr.decode(errors="replace")[-2000:]
                reason = f"run {runs}: exit code {p.returncode}\n{tail}"
                break
            if crash:
                # the scheduled crash point was never reached; that is fine
                pass
            break
        if reason is None:
            if server.next != len(events):
                reason = f"only {server.next}/{len(events)} events acknowledged"
            elif expected_audit is not None and server.audit != expected_audit:
                reason = first_diff(server.audit, expected_audit)
            elif expected_archive is not None:
                ap = work / "out" / "archive.json"
                if not ap.exists():
                    reason = "archive.json missing"
                elif json.loads(ap.read_text()) != expected_archive:
                    reason = "archive.json differs from expected"
        return {"ok": reason is None, "reason": reason, "runs": runs, "calls": calls,
                "audit": server.audit}
    finally:
        server.close()
        if not keep:
            shutil.rmtree(work, ignore_errors=True)


def load_scenario(d):
    d = Path(d)
    return (load_jsonl(d / "feed.jsonl"), load_jsonl(d / "expected_audit.jsonl"),
            json.loads((d / "expected_archive.json").read_text()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("scenario")
    ap.add_argument("--app", default=str(Path(__file__).resolve().parents[1]))
    ap.add_argument("--crash", action="append", default=[],
                    help="N:before|after, the N-th durable call of that run (repeatable)")
    ap.add_argument("--random-crashes", type=int, default=0)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    feed, audit, archive = load_scenario(a.scenario)
    crashes = [(int(c.split(":")[0]), c.split(":")[1]) for c in a.crash]
    if a.random_crashes:
        base = run(a.app, feed, audit, archive)
        if not base["ok"]:
            print("FAIL (no crash):", base["reason"])
            sys.exit(1)
        rng = random.Random(a.seed)
        crashes = [(rng.randint(1, base["calls"]), rng.choice(["before", "after"]))
                   for _ in range(a.random_crashes)]
    r = run(a.app, feed, audit, archive, crashes)
    print("PASS" if r["ok"] else "FAIL", f"runs={r['runs']}", r["reason"] or "")
    sys.exit(0 if r["ok"] else 1)


if __name__ == "__main__":
    main()
