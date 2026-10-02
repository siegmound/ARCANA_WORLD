# R6 B0-G — Minimal State and Storage Accounting Closure

## Scope and authority

B0-G adds generic retention declarations, a domain-adapter extraction boundary,
and explicit logical storage measurements. The core does not name scientific
fields or choose domain retention. The producer adapter remains responsible for
which producer items are materialized or reconstructable. Accounting reports
are operational observations; paths and measured byte counts never enter
scientific identities.

This work does not change scientific authorization, initial-world payloads,
checkpoint density, or engine execution. `runtime_authorized=true` remains
limited to `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`.
`mechanics_authorized=false`, `forward_evolution_authorized=false`,
`dt_selected=false`, `t1_created=false`, and `canonical_state_changed=false`.

## Retention and minimal-state contract

`r6.retention` defines the generic actions `MATERIALIZE`, `DERIVE`, `REFINE`,
`STATIC`, `FORCING`, and `DISCARD`. Each declaration has a producer item ID,
information role, requiredness, and reconstruction references. `SYSTEM_MEMORY`
is explicit and cannot be declared `DISCARD`.

The existing `planning.RetentionClass` remains the record-lifecycle policy
(`RETAIN_ALWAYS`, `RETAIN_EVENT`, `RETAIN_CHECKPOINT`, `RETAIN_QUERY_VIEW`,
`RECOMPUTABLE`, `EPHEMERAL`). It does not classify individual producer
products or declare their reconstruction closure, so this contract complements
that registry without changing it.

The action describes a retention decision, while the role explains why the
information matters. Query outputs and future system memory can both be
materialized; an apparently unobservable memory value remains required when
future evolution depends on it. This is the fixture's `memory_state` rule.

DERIVE and REFINE declarations require an explicit replay/refinement recipe,
retained parent, forcing, static/provider authority, or deterministic adapter
anchor. Extraction validation then checks that required forcing/static
identities and parent items are present. Required materialized items must map
to one or more `DomainStateEnvelope` records. Undeclared output, omitted
required states, missing dependencies, duplicate classifications, and history
or branch scope mismatches fail closed.

The generic `DomainExtractor` protocol receives opaque producer output and
returns `MinimalStateExtractionResult`. The core validates that result and does
not parse ShellSet, climate, hydrology, NEMO, or other engine layouts. The
result reports the contract ID, persistent state IDs, forcing/static and
reconstruction identities, omitted item IDs, and validation status. It does
not retain raw producer output or large diagnostics.

### Synthetic qualification fixture

The B0-G test uses `core_state` and `memory_state` as materialized records,
`derived_display` as a recipe/parent-derived value, `forcing` as an identified
dependency, and diagnostic/intermediate values as discarded. It writes typed
records and forcing into a temporary `HistoryStore`, reopens the store, queries
state/history/WHY, and calculates deterministic future state from the reopened
minimal state. The result matches the complete fixture's expected evolution;
the query difference reports exact equality. Omitting `memory_state`, omitting
the forcing, or omitting the reconstruction recipe fails validation. No
production ARCANA state is read or written.

### Initial-world compatibility

The existing initial-world producer is `ADAPTER_NEEDED`, not incompatible.
`InitialWorldFields` exposes a packed array inventory and the materializer emits
one deterministic NPZ with several semantic state envelopes sharing its
payload reference. That is compatible with the generic result/store boundary,
but the existing producer does not yet declare the six retention actions per
field. B0-G does not add that adapter or rematerialize the governed package.

## Storage accounting

`r6.storage` accepts explicit `AccountingScope` roots. It never walks the
repository by default and does not infer category from file extension. The
caller assigns each root as `CANONICAL_METADATA`, `CANONICAL_PAYLOAD`,
`INDEX`, `SCRATCH`, `PROVIDER_CACHE`, `REFINEMENT_CACHE`, or
`QUALIFICATION_EVIDENCE`; `OPERATIONAL_METADATA` distinguishes transaction
journals from canonical records.

Measurements report file count and logical `st_size` bytes per category.
Traversal and report ordering are deterministic. Paths are normalized to
resolved POSIX form in operational output. Duplicate physical files are
counted once; a physical file assigned to different categories is rejected.
Overlapping directory roots are rejected. Symlinks and reparse points are
recorded as excluded and never followed. Missing optional roots are recorded;
missing required paths fail closed. External payloads are supplied explicitly
and counted in `CANONICAL_PAYLOAD`, independently of semantic state references.

`history_store_scope()` accounts the store manifest and typed record buckets as
`CANONICAL_METADATA`, and `.history_transactions` as
`OPERATIONAL_METADATA`. External payload locations remain outside
`HistoryStore` ownership. Repeated State A/State B references to one path (or
filesystem object) are counted once.

The canonical persistent measure is the sum of canonical metadata and payload
logical bytes. The hard ceiling is strictly less than decimal 500 GB:
`500,000,000,000` bytes. Equality is over the cap. Tests inject a small cap;
there are no per-domain quotas, target checkpoint counts, or warning
thresholds.

## Gate status and limits

- **H12 storage accounting:** `IMPLEMENTED_AND_TESTED` for explicit local
  filesystem scopes and logical bytes. Physical allocated bytes, remote stores,
  repository discovery, and concurrent mutation during measurement are out of
  scope.
- **H16 minimal-state extraction:** `IMPLEMENTED_AND_TESTED` for the generic
  contract, injected adapter boundary, fail-closed dependency checks, and
  synthetic minimal-state reopen/evolution fixture. Domain-specific field
  policies and production initial-world extraction adapters remain future work.
- **H14 support boundaries:** remains `PARTIAL`; this change does not add
  general GIS containment.

Windows validation covers Python source and synthetic fixtures only. It does
not qualify ShellSet, OrbData, mechanics, or a scientific runtime.
