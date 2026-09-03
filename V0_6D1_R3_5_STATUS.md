# v0.6D1-R3.5 Status

**Verdict:** `PASS_TIME_RESOLVED_VA_HEADROOM_INSTRUMENTATION_AND_DYNAMIC_SENSITIVITY_RUNPACK_CANDIDATE__FULL_210_TO_150_DUAL_REPLAY_PENDING`

## Closed
- Non-invasive time-resolved VA instrumentation implemented around the exact R3.4/D3.3A operators.
- R3.5 ceiling sensitivity variable exposed for q=0.08 and q=0.10 without changing `mu`, `b`, or `q*=0.045`.
- Diagnostic unclipped Riccati probe implemented without feedback into the scientific state.
- Root lineage / axis near-ceiling records included.
- Same-step event context included.
- R3.5 q=0.08 is bit-exact to R3.4 on 210→209 Ma across population, traits, VA, RI, isolation clock, contact, IDs, and events.
- q=0.08 and q=0.10 are identical over 210→208 Ma before any ceiling contact.
- Eventful q=0.08 validation 210→206 Ma: 15 fissions, 3 coalescences, 0 speciation/extinction, no clipping, peak q=0.0262317562.
- Full tests: **102/102 PASS**.
- Formal audit: **110/110 PASS**.

## Pending
The authoritative R3.5 result requires the paired full local replay 210→150 Ma for q=0.08 and q=0.10. Until those two telemetry traces are audited, 150 Ma remains **not authorized** as a continuation checkpoint.

## Why the full sensitivity is local
Each 210→150 Ma replay is a long production execution. R3.5 deliberately packages the instrumentation and deterministic paired runner rather than weakening cadence/resolution to fit a short hosted execution.
