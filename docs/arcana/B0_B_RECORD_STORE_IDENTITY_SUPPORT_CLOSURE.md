# B0-B — WORLD_HISTORY Record, Store Identity and Support Closure

**Scope:** closes generic record/store identity, payload identity/integrity primitives, and support-query classification in the existing R6 core. No scientific authority or payload was changed.

## Implementation

### Store manifest and reopen behavior

`HistoryStore` now creates and validates a deterministic `metadata/store_manifest.json` on initialization. The manifest is:

- `store_kind`: `ARCANA_R6_FILE_HISTORY_STORE`
- `schema_version`: `ARCANA_R6_FILE_HISTORY_STORE_V0`
- `identity_format_version`: `1`
- `record_layout_version`: `1`

It contains no root path or timestamp. Creation uses the existing immutable atomic file-write mechanism. An existing store without a manifest receives the metadata manifest without rewriting its records; incompatible or unreadable manifests fail closed with `StoreSchemaError`. The store remains filesystem JSON; SQLite and migrations were not introduced.

### Typed read verification

Every exposed persisted read path now reconstructs its record model and verifies deterministic identity before returning:

- domain state
- provenance
- event
- checkpoint
- provider binding
- temporal role records
- refinement branch

Dictionary-shaped public results remain dictionaries for compatibility, but are returned only after typed validation. Enumerations also validate records. Missing records retain `FileNotFoundError`; malformed or identity-mismatched records raise `RecordIntegrityError`. Invalid/missing store manifests raise `StoreSchemaError`.

### Payload identity and integrity

`PayloadIdentity` represents a SHA-256 algorithm/digest pair independently of semantic record IDs. `PayloadReference` parses known existing SHA-256 reference forms while retaining the original string for serialization; opaque legacy strings remain readable but cannot be verified without a digest.

`verify_payload(reference, source)` explicitly checks available bytes, a filesystem path, or a binary stream against the digest in the typed reference. It performs no resolution, network access, storage, copy, or CAS operation. Unsupported opaque references and digest mismatches raise `PayloadIntegrityError`.

`DomainStateEnvelope` accepts a typed reference and exposes a typed `payload_reference` view, but stores/serializes the same legacy string. Therefore existing V0/V1 state bodies and state IDs are unchanged by this type addition. Distinct state envelopes may retain distinct IDs while sharing one payload digest/reference. Payload identity never substitutes for `DomainStateId`.

### Support-query behavior

For a requested cell absent from all same-time `CELL_SET` states, `state_at` now returns `OUTSIDE_SUPPORT` with the requested cell and declared cell IDs. When a requested cell cannot be evaluated against a non-cell selector such as `GRID`, `REGION`, `GLOBAL` or `NONE`, it returns `SUPPORT_MISMATCH` with selector kinds. It does not interpolate or choose a nearest cell. Existing distinctions for missing domain/time, UNKNOWN, NOT_APPLICABLE, OUTSIDE_SCOPE, known zero/false and conflicts remain.

This is a bounded exact-cell rule, not general GIS containment. `H14` remains partial.

## Compatibility and scientific boundary

- Legacy opaque `payload_ref` strings still round-trip.
- Existing V0/V1 state schema decoding remains supported.
- State identity calculation and serialized fields are preserved.
- Existing stores with records but no manifest initialize metadata without rewriting those records.
- No payload backend, content-addressed store, database, migration framework or resolver is selected.
- No scientific values, authority, provider interpretation, canonical state, ShellSet mechanics, T1, or `dt` changed.

## Validation

Focused B0-B module: **7 passed**.

Default active R6 suite: **259 passed**. The active suite includes the new B0-B tests; the baseline was 252.

`git diff --check`: PASS.

## Acceptance status

| Gate | Post B0-B | Evidence / remaining limit |
|---|---|---|
| H1 write/read integrity | IMPLEMENTED_AND_TESTED | Typed reads verify identity for all persisted record families; direct corruption tests cover each family. |
| H2 close/reopen identity | IMPLEMENTED_AND_TESTED | Deterministic manifest, new store instance, existing-record/no-manifest initialization and incompatible-version rejection tested. |
| H7 UNKNOWN/value distinction | IMPLEMENTED_AND_TESTED | UNKNOWN, NOT_APPLICABLE and OUTSIDE_SCOPE remain separate; known `0`, `0.0` and `false` query as FOUND. |
| H9 append-only identity guarantees | IMPLEMENTED_AND_TESTED | Immutable conflict behavior remains; all semantic record reads validate key/content identity. |
| H13 payload integrity | IMPLEMENTED_AND_TESTED | Generic explicit digest verification tested for bytes, path and binary stream; no implicit resolver/store is provided. |
| H14 support boundaries | PARTIAL | Exact CELL_SET outside support and unresolved non-cell selector mismatch are distinguished; no broad geometry containment. |

Other B0-A statuses remain unchanged: H3/H15 remain implemented and tested; H4/H6/H8/H10/H11/H16/H17/H18 remain partial; H5/H12 remain missing. B0-B did not add difference/WHY, forcing, replay execution, branch isolation, accounting, multi-record transactions or minimal-state extraction.

## Changed files

- `src/arcana_worldsim/r6/identity.py`
- `src/arcana_worldsim/r6/provenance.py`
- `src/arcana_worldsim/r6/state.py`
- `src/arcana_worldsim/r6/temporal.py`
- `src/arcana_worldsim/r6/store.py`
- `src/arcana_worldsim/r6/query.py`
- `tests/test_r6_world_history_b0_b.py`
- `docs/arcana/B0_B_RECORD_STORE_IDENTITY_SUPPORT_CLOSURE.md`
