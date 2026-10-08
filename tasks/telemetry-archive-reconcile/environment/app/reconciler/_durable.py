"""Harness-owned I/O for the reconciler. Do not modify: the verifier replaces
this file with its own copy.

Events come from the harness over a Unix socket; only the next unacknowledged
event is ever visible. Audit records are published to the harness with emit().
put()/get() is the only storage that survives a restart.

Crash injection (used by tools/harness.py and by the verifier):
  RECON_CRASH_AT=N      crash at the N-th call (1-based) to ack/emit/put/write_output
  RECON_CRASH_MODE=before|after   crash before or after that call's effect
"""
import atexit
import json
import os
import socket

_SOCK = os.environ.get("RECON_SOCK", "/run/recon/harness.sock")
_STATE = os.environ.get("RECON_STATE", "/var/lib/recon/state")
_OUT = os.environ.get("RECON_OUT", "/out")
_CRASH_AT = int(os.environ.get("RECON_CRASH_AT", "0") or 0)
_CRASH_MODE = os.environ.get("RECON_CRASH_MODE", "before")
_CALLS_FILE = os.environ.get("RECON_CALLS_FILE")

_calls = 0
_conn = None
_rfile = None


def _crash_point(effect):
    global _calls
    _calls += 1
    if _calls == _CRASH_AT and _CRASH_MODE == "before":
        os._exit(137)
    result = effect()
    if _calls == _CRASH_AT:
        os._exit(137)
    return result


def _write_calls():
    if _CALLS_FILE:
        with open(_CALLS_FILE, "w") as f:
            f.write(str(_calls))


atexit.register(_write_calls)


def _rpc(msg):
    global _conn, _rfile
    if _conn is None:
        _conn = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        _conn.connect(_SOCK)
        _rfile = _conn.makefile("rb")
    _conn.sendall((json.dumps(msg, separators=(",", ":")) + "\n").encode())
    line = _rfile.readline()
    if not line:
        raise RuntimeError("harness closed the connection")
    resp = json.loads(line)
    if "error" in resp:
        raise RuntimeError("harness: " + resp["error"])
    return resp.get("value")


def poll():
    """Next unacknowledged event (dict), or None at end of feed."""
    return _rpc({"op": "poll"})


def ack(i):
    """Acknowledge event i. It will never be delivered again."""
    return _crash_point(lambda: _rpc({"op": "ack", "i": i}))


def emit(seqno, record):
    """Publish one audit record (at-least-once; see SEMANTICS.md §10)."""
    return _crash_point(lambda: _rpc({"op": "emit", "seqno": seqno, "record": record}))


def _path(key):
    return os.path.join(_STATE, key.encode().hex())


def _atomic(path, data):
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def put(key, data):
    """Atomic durable write of bytes under a string key."""
    if not isinstance(data, (bytes, bytearray)):
        raise TypeError("put() takes bytes")
    os.makedirs(_STATE, exist_ok=True)
    return _crash_point(lambda: _atomic(_path(key), bytes(data)))


def get(key):
    """Bytes stored under key, or None."""
    try:
        with open(_path(key), "rb") as f:
            return f.read()
    except FileNotFoundError:
        return None


def write_output(name, data):
    """Atomic write of bytes to the output directory."""
    if "/" in name or name.startswith("."):
        raise ValueError("bad output name")
    os.makedirs(_OUT, exist_ok=True)
    return _crash_point(lambda: _atomic(os.path.join(_OUT, name), bytes(data)))
