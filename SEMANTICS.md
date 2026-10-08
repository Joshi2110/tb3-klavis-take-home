# SEMANTICS.md — telemetry archive reconciler

This document is normative. The reconciler in `/app/reconciler/` must produce
exactly the outputs defined here for every feed that satisfies the harness
guarantees of §9. Where this document says "must", the verifier checks it.

## 1. Physical model

One spacecraft, one virtual channel. All times are integers in milliseconds on
a single ground timescale.

| Constant    | Value          | Meaning                                              |
|-------------|----------------|------------------------------------------------------|
| `PERIOD`    | 250            | ms between consecutive frames (4 frames/s, exact)    |
| `MOD`       | 16384          | virtual-channel counter modulus (14 bits)            |
| `L_LIVE`    | 2000           | max delay between generation and live reception      |
| `D_PLAY`    | 21600000       | max delay between generation and playback reception  |
| `T_RESOLVE` | 900000         | resolution deadline after first reception            |
| `MIN_BOOT`  | 60000          | every boot lasts longer than this                    |

Boot `b` starts at ground time `s_b`. Within a boot, frame number `seq`
(0, 1, 2, ...) is generated at exactly `g = s_b + PERIOD * seq`. Its counter is
`vc = seq mod MOD`. The counter restarts at 0 on every boot.

On-board time (`obt`) is the time since the start of the current boot:
`obt = PERIOD * seq`. It is carried only by time-tagged frames (a subset of live
frames) and by every playback frame. All other frames carry `obt = null`.

A frame's **identity** is `(boot, seq)`.

## 2. Events

The feed is a sequence of events with consecutive indices `i = 0, 1, 2, ...`.

```
BOOTLOG  {i, boot, boot_time}                       authoritative: s_boot = boot_time
FRAME    {i, station, rx_time, vc, obt, hash}       live reception
PLAYBACK {i, station, rx_time, vc, obt, hash}       recorder dump reception, obt never null
RETRACT  {i, station, rx_time, ref_rx_time, vc}     the delivery (station, ref_rx_time, vc) was corrupt
TICK     {i, time}                                  ground time has reached `time`
```

A **delivery** is one FRAME or PLAYBACK event. Its generation window is
`W = [rx_time - L_LIVE, rx_time]` for FRAME and `[rx_time - D_PLAY, rx_time]`
for PLAYBACK.

**Now.** `now` is the maximum, over all events processed so far including the
current one, of `rx_time` (FRAME, PLAYBACK, RETRACT) and `time` (TICK).
BOOTLOG does not advance `now`.

## 3. Records

A **record** groups all deliveries that carry the same `hash`. A delivery whose
`hash` matches an existing record is attached to it; otherwise it creates a new
record. A record's `rid` is the index of the event that created it.

A record has `vc`, `obt`, `first_rx` (the `rx_time` of the creating delivery)
and a window `W(r)`, the intersection of the windows of all its deliveries.
Deliveries of one frame share `vc`; a live copy may lack the `obt` that its
playback copy carries. The record's `obt` is the non-null value carried by any
of its deliveries, or null if none does. Attaching a delivery can therefore
narrow `W(r)` and add an `obt`, and both can make the record decidable.

A republished frame (correct payload sent after a retraction) has a new hash and
is therefore a new record.

## 4. States and legal transitions

```
(none)   -> SEEN        cause DELIVERY   record created
SEEN     -> ARCHIVED    cause PROOF      identity decidable (§5)
SEEN     -> IN_DOUBT    cause AMBIGUOUS  identity not decidable
IN_DOUBT -> ARCHIVED    cause PROOF      identity became decidable
IN_DOUBT -> ARCHIVED    cause DEADLINE   deadline rule (§6)
IN_DOUBT -> DISCARDED   cause RETRACT    payload retracted before identity was decided
ARCHIVED -> RETRACTED   cause RETRACT    archived payload retracted
ARCHIVED -> IN_DOUBT    cause CONTRADICTED  provisional identity contradicted (§6.1)
```

Every other transition is illegal. DISCARDED and RETRACTED are terminal.

A record archived with cause DEADLINE is **provisional** until it is retracted,
contradicted, or archived again with cause PROOF. A record archived with cause
PROOF is never contradicted (its identity was the only one possible) and its
identity never changes. A provisional record keeps its identity until it is
contradicted.

## 5. Knowledge and decidability

### 5.1 Knowledge

Knowledge consists only of BOOTLOGs and of records that have ever reached
ARCHIVED with cause PROOF (**proven records**, including ones later RETRACTED).
Records in IN_DOUBT, records archived by DEADLINE and DISCARDED records are not
knowledge.

Let `B` be the highest boot index received in a BOOTLOG. Boots `0..B` are
**known**, with exact starts `s_0 < s_1 < ... < s_B`.

The **coverage end** of boot `B` is
`c_B = max(s_B + MIN_BOOT, max{ s_B + PERIOD * seq : proven record with boot = B })`.
Boot `B` is proven alive up to `c_B` (by G8 or by a proven frame), so no boot
starts in `(s_B, c_B]`.

### 5.2 Hypotheses for a record

For a record `r` with window `W(r) = [w_lo, w_hi]`, a candidate `seq` satisfies
`seq >= 0`, `seq ≡ vc (mod MOD)`, and `seq = obt / PERIOD` if `obt` is not null.

**Known-boot hypotheses (K).** All pairs `(b, seq)` with `0 <= b <= B` such that
`g = s_b + PERIOD * seq` lies in `W(r)`, `g >= s_b`, and `g < s_{b+1}` when
`b < B`. No upper bound applies when `b = B`.

**Unknown-boot hypothesis (U).** True if some boot starting at `s > c_B` could
have generated the record. Let `seq0 = obt / PERIOD` if `obt` is not null, else
`seq0 = vc`. Then

```
U  <=>  w_hi - PERIOD * seq0 > c_B
```

An unknown boot's index cannot be determined (boots may be silent), so U never
yields an identity.

### 5.3 Decidability

A record is **decidable** iff U is false and K contains exactly one pair. Its
identity is then that pair.

Consequences worth stating: a frame whose counter dropped after the last proven
frame is typically ambiguous between "boot B, after a wrap" and "a new boot"
(R1); a later proven frame of boot B with a larger `g`, or the next BOOTLOG,
raises `c_B` or `B` and may make it decidable (R2). A frame that can only belong
to an unknown boot stays IN_DOUBT until its BOOTLOG or its deadline, even when
the reboot itself is obvious.

## 6. Deadline rule

A record still IN_DOUBT when `now >= first_rx + T_RESOLVE` is archived with
cause DEADLINE:

1. If K is non-empty: choose the pair with the largest `b`, then the smallest
   `seq` (same boot, i.e. counter wrap, whenever the counter is consistent with
   the nominal frame rate within the reception tolerance).
2. Otherwise: identity `(B + 1, seq0)` (reboot).

Deadline decisions are not knowledge (§5.1). They are not guaranteed to be
right: a reboot can mimic a wrap until its BOOTLOG arrives.

### 6.1 Contradiction

A provisional record `r` with identity `(b, seq)` is **consistent** while that
identity is still possible:

- if `b <= B`: `(b, seq)` belongs to K(r) (§5.2);
- if `b > B`: `seq ≡ vc (mod MOD)`, `seq = obt / PERIOD` if `obt` is not null,
  and `w_hi - PERIOD * seq > c_B`.

When a provisional record stops being consistent it goes back to IN_DOUBT
(cause CONTRADICTED) and loses its identity. Its deadline has already passed, so
unless it is decidable it is archived again by the deadline rule in the same
event, with the knowledge available then. Knowledge only grows, so a record that
has become inconsistent never becomes consistent again with the same identity.

Contradiction can come from a BOOTLOG, from a proof that raises `c_B`, or from a
delivery attached to the provisional record (a narrower window or a time tag).
RETRACTED records are never re-evaluated.

## 7. Event processing

Each event is processed in four steps. Audit records are emitted in step order,
and within a step in increasing `rid`.

1. **Ingest.**
   FRAME / PLAYBACK: attach to the record with the same hash, or create a record
   (`(none) -> SEEN`). An attachment updates `W` and `obt` whatever the state;
   for a provisional record, step 2 then re-evaluates it.
   RETRACT: find the record of the referenced delivery. IN_DOUBT becomes
   DISCARDED, ARCHIVED becomes RETRACTED, any other state: no effect.
   BOOTLOG: add the boot to knowledge.
   TICK: update `now`.
2. **Evidence.** Repeat until no change: every provisional record that is not
   consistent becomes IN_DOUBT (CONTRADICTED), and every SEEN or IN_DOUBT record
   that is decidable becomes ARCHIVED (PROOF). Each proof may raise `c_B`.
   Knowledge only grows, so the final result does not depend on iteration
   order. Emit this step's transitions sorted by `rid`; a record that is both
   contradicted and proven in this step emits CONTRADICTED first.
3. **Ambiguity.** Every record still SEEN becomes IN_DOUBT (AMBIGUOUS).
4. **Deadline.** Apply §6 to every IN_DOUBT record whose deadline has passed.

A record created in an event can therefore produce several audit records in
that same event.

## 8. Outputs

### 8.1 Audit

One audit record per transition:

```
{"seqno": n, "event": i, "rid": r, "from": "IN_DOUBT", "to": "ARCHIVED",
 "cause": "PROOF", "boot": 0, "seq": 16400, "hash": "..."}
```

`seqno` starts at 0 and increases by 1. `boot` and `seq` are set on transitions
to ARCHIVED and on ARCHIVED -> RETRACTED; they are `null` otherwise, including
on ARCHIVED -> IN_DOUBT.

Example: a frame archived by the deadline rule as `(0, 16400)` is contradicted
when event 9120 delivers `BOOTLOG(boot=1)`, and is then provable as `(1, 16)`.
Event 9120 emits, for that record:

```
{"seqno": 40211, "event": 9120, "rid": 8517, "from": "ARCHIVED", "to": "IN_DOUBT",
 "cause": "CONTRADICTED", "boot": null, "seq": null, "hash": "..."}
{"seqno": 40212, "event": 9120, "rid": 8517, "from": "IN_DOUBT", "to": "ARCHIVED",
 "cause": "PROOF", "boot": 1, "seq": 16, "hash": "..."}
```

### 8.2 Archive

The archive after event `i` (`as_of(i)`) is the set of records in state ARCHIVED
after processing event `i`, ordered by `(boot, seq)`, each reported as
`{"boot", "seq", "hash"}`. It is fully determined by the audit prefix up to
event `i`. At the end of the feed the reconciler writes the final archive to
`/out/archive.json`.

## 9. Harness guarantees

The verifier only uses feeds satisfying all of the following.

- G1. Event 0 is `BOOTLOG(boot=0)`. BOOTLOGs arrive in increasing boot order,
  each after at least one frame of that boot was generated.
- G2. Header fields (`vc`, `obt`, `rx_time`) are always correct; corruption only
  affects the payload. Reception delays respect `L_LIVE` and `D_PLAY`.
- G3. Distinct frames have distinct hashes. For a given frame, a second hash is
  delivered only after a RETRACT of every earlier hash. A retracted hash is
  never delivered again.
- G4. A RETRACT always references a delivery received in an earlier event.
- G5. Every record has at least one hypothesis (K non-empty or U true).
- G6. Every boot's BOOTLOG is delivered before the end of the feed.
- G7. The last event is a TICK whose time is past every record's deadline. At
  the end of the feed no record is SEEN or IN_DOUBT.
- G8. Consecutive boot starts differ by more than `MIN_BOOT`.

## 10. Delivery, persistence and crashes

The reconciler is started as `python -m reconciler` in `/app` and must interact
with the outside world only through the harness-owned module
`reconciler/_durable.py`. Do not modify it; the verifier replaces it with its
own copy.

```
poll()                 -> next unacknowledged event (dict) or None at end of feed
ack(i)                 -> event i is acknowledged and will never be delivered again
emit(seqno, record)    -> publish one audit record
put(key, data: bytes)  -> atomic durable write
get(key)               -> bytes or None
write_output(name, data: bytes) -> atomic write under /out
```

- `poll()` returns events in index order. After a restart it returns the first
  unacknowledged event, which may already have been partly or fully processed.
- `emit` is at-least-once. The receiver accepts a repeated `seqno` only with
  identical content; a gap in `seqno`, or a repeated `seqno` with different
  content, is a failure.
- Only data stored with `put` survives a restart. Everything else (memory,
  files, `/tmp`) is lost.
- The verifier kills the process (exit without cleanup) at a scheduled call to
  `ack`, `emit`, `put` or `write_output`, either before or after its effect,
  then restarts it with the same command. A run may crash several times.
- After the final restart the observable result must be identical to a run
  without crashes: the same audit stream (deduplicated by `seqno`) and the same
  `/out/archive.json`. The process exits 0 once `poll()` returns None and the
  archive is written.
