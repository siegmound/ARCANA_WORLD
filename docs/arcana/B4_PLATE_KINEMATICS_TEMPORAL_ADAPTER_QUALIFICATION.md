# B4 plate-kinematics temporal adapter qualification

## A. Source revision

Qualified repository revision: `45f863b0e9a4773f6ecc5052d877c56b5e002eb4` on `r6/b4-plate-kinematics-temporal-adapter`. Qualification binds the tracked authority documents at that HEAD and verifies the referenced external payload hashes before reading them.

The B4 adapter, runner, and test additions are uncommitted worktree files as requested. Their exact SHA256 values are recorded under `qualification_implementation.source_hashes` in `outputs/r6_b4_plate_kinematics_qualification/B4_RESULT.json`; the qualified authority/source HEAD remains the commit above.

## B. Authority basis

`R6_T0_CANONICAL_PLATE_KINEMATICS.json` is a `STOCHASTIC_CANONICAL_MODEL_REALIZATION` at 210 Ma, with 12 per-plate Euler angular-rate vectors in rad/year and the declared synthetic area-weighted least-squares no-net-rotation gauge. This is ARCANA-authored model state, not an Earth observation or reconstruction. The source uncertainty identifies a single member of an explicit synthetic prior; it does not provide an executed sensitivity ensemble.

The vector partition is model-derived from canonical T0 and supplies face plate IDs/topology identity. It does not supply a governed node-to-plate map. pyGPlates remains a candidate processor; it is neither the input authority nor a production-authorized derived authority. The FEG/runtime package is numerical runtime support only.

## C. Engine/tool status

The qualification did not invoke pyGPlates, ShellSet, or OrbData. Existing source records keep pyGPlates unauthorized for production. No engine output was promoted.

## D. Adapter contract

The adapter verifies tracked source blobs, semantic and raw kinematics identities, parent T0/vector-partition identities, external payload SHA/size, topology plate IDs, time anchor, reference frame, B3 evidence, and current motion/event authorization blockers. It emits a deterministic `ForcingRecord` with the 12 governed T0 Euler vectors and source provenance. Its derived record identity is not new scientific authority. No geometry is rotated and no canonical state is changed.

## E. Temporal support

The only supported temporal entry is the exact 210 Ma `INSTANT` anchor. Positive-duration validity and segment renewal/change law remain unbound/blocked. The B4 interval request fails closed. No interpolation, extrapolation, event time, or global dt is produced. The 30 candidate event pairs remain unknown; there are no qualified discontinuity boundaries.

## F. Plate/spatial support

Plate support is the whole governed set of IDs 0–11, cross-checked against 64,800 canonical face labels; the partition reports 1,983 boundary segments. This is face-level support only. Node/grid membership is unavailable and must not be inferred from numerical ownership or latitude/longitude.

## G. Real read-only qualification

The source was read and verified, converted to one T0 anchor forcing, atomically persisted with provenance and a qualification-only query index, then queried after destroying and reopening the store. WHY resolved the forcing and provenance with no unresolved references. Tracked authorities and external payloads had identical before/after hashes and sizes. The query index explicitly is not a T1 or evolved state.

## H. Synthetic edge cases

Focused tests use fixture-only two-plate, two-regime piecewise intervals. They cover regime-specific requests, a request crossing the boundary, unknown plate IDs, reference-frame mismatch, missing plate/grid mapping, unsupported real interval requests, and deterministic fixture forcing identity. Fixture values remain `FIXTURE_ONLY` and are not mixed into the real-source qualification.

## I. Forcing mapping

The real output is a `PLATE_KINEMATICS_T0_ANCHOR` `ForcingRecord`, supported at one instant and spatially scoped to the complete face plate-ID set. It retains source refs, source authority class, uncertainty, gauge, units, vectors, and the explicit absence of node mapping. The persisted identity was stable across repeated construction and after reopen.

## J. Replay/determinism

Repeated source-to-record builds matched ForcingId, driver payload identity, source and adapter provenance IDs, and qualification index state ID. Store reopen retained the typed forcing identity. This qualifies adapter binding/replay identity only; it is not mechanics replay.

## K. UNKNOWN/authority behavior

Unknown plate support, incompatible frame, absent plate/grid mapping, malformed source identity, and unsupported time requests fail closed. Missing motion is never replaced with zero. Positive-duration validity remains `UNKNOWN`.

## L. Downstream dependency contract

Available now: T0 plate IDs, per-plate instantaneous Euler rate vectors, gauge identity, and coarse face labels/topology. No additional interval quantity is derivable under current authority. pyGPlates processing is candidate-only. Missing: positive-duration motion law, node/grid membership, boundary accommodation/contact laws, topology transition schedule, and authorized interval constraints.

## M. ShellSet boundary

ShellSet input readiness is blocked. B4 did not execute it. A node support map and a governed interval/boundary contract must exist before an adapter output can be routed to mechanics; Earth5R/PB2002 remain outside ARCANA authority.

## N. Temporal constraints

The B4 temporal constraint output records one hard T0 anchor at 210 Ma, no valid intervals, no supported discontinuities, no event lead-time lower bound, and no selected dt. It is input evidence for later temporal integration, not a scheduler decision.

## O. Source immutability

All source hashes/sizes matched before and after. No governed source was written, regenerated, or copied into the qualification output. External payload references are logical and relative; machine-specific paths and mtimes are evidence only and are excluded from semantic identities.

## P. Storage/accounting

The temporary qualification store reopened successfully. Explicit WORLD_HISTORY accounting included its metadata and the two referenced external payloads once; canonical persistent bytes were `6,865,855`, below the `500,000,000,000`-byte cap. Qualification output artifacts are separate from this store accounting.

## Q. Remaining gaps

- positive-duration plate-rate validity, renewal law, and interval authority;
- governed plate-to-node/grid mapping;
- boundary type, polarity, accommodation, and contact semantics;
- topology transition/event schedule;
- future physical interval constraints and dt derivation.

## R. B5 readiness

Decision: `READY_FOR_B5_WITH_KINEMATIC_GAPS`. Recommended next domain: define and qualify authoritative spatial plate support together with boundary/topology transition semantics. This follows the measured missing dependencies and does not presume climate or another domain.

**B4 verdict:** `PASS_B4_PLATE_KINEMATICS_TEMPORAL_ADAPTER_QUALIFICATION`.

Maximum next-stage authorization: `AUTHORIZE_B5_MULTI_DOMAIN_TEMPORAL_INTEGRATION_DESIGN_AND_QUALIFICATION`. Mechanics, dt selection, T0 evolution, T1, forward evolution, and scientific production remain unauthorized.
