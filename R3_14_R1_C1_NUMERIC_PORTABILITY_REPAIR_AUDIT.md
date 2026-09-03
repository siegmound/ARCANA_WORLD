# v0.6D1-R3.14-R1 — C1 Numeric Portability Repair Audit

## Trigger
On Windows, the exact v0.6.1 sealed payload was successfully recovered and SHA-verified, but C1 aborted before provider construction with:

`ValueError: C1 orbital reconstruction does not reproduce sealed forcing exactly`

The failing gate used `np.array_equal` on values re-evaluated through transcendental functions (`cos`, later `log`/`exp`). Bitwise identity of such derived floating-point values is not a portable cross-platform invariant across libm/NumPy builds.

## Repair
- The five v0.6.1 payload hashes remain frozen and byte-authoritative.
- Exact sealed 100-year checkpoints remain authoritative and are loaded directly from the SHA-verified sealed history wherever serialized values exist.
- Re-evaluation of the v0.6.1 equations is retained as a formula/provenance gate, but the gate now requires a strict platform-stable numerical equivalence (`rtol=1e-10`, `atol=1e-12`) instead of byte identity.
- A materially changed formula still fails closed.
- No biological state, parameter, physics equation, orbital constants, CHA-2 parameter, adaptive-clock parameter, or R3.13 checkpoint is changed.
- Exact sealed 100-year anchors are never replaced by derived midpoint values.

## Validation
Updated local regression:
- R3.14 binding tests
- C1 portability tests
- R3.13 tests
- R3.12 tests

Result: `22/22 PASS`.

The repair is governance/numerical-portability only. R3.14 remains a binding-only stage and advances no biology.
