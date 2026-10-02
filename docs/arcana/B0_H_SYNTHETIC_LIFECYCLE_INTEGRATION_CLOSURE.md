# R6 B0-H — Synthetic WORLD_HISTORY Lifecycle Integration

## Result scope

B0-H integrates the existing B0-B through B0-G primitives in a synthetic,
non-scientific lifecycle. It adds no production runtime behavior and makes no
changes to governed scientific authority. All values and states are
`FIXTURE_ONLY` (or explicit `UNKNOWN`/`OUTSIDE_SCOPE`), with deterministic
fixture IDs and tiny payloads.

## Lifecycle exercised

One compact fixture builds a history and parent branch, publishes initial
records atomically, closes the store, and reopens the filesystem-backed store.
The initial transaction contains minimal-state records, provenance, event,
forcing, checkpoint, expected replay output, and `ReplayRecipe`. A fault-injected
publication is recovered before retry; no partial bundle is visible and
pre-existing records survive recovery.

At `fixture:t0`, the fixture distinguishes known numeric zero, known false,
`UNKNOWN`, `OUTSIDE_SCOPE`, a missing domain, a missing timestamp, an exact
cell outside `CELL_SET`, and a `REGION` selector that cannot answer a cell
query. No interpolation is used. All persisted typed records are read back
through their validating store APIs.

The B0-G retention contract materializes core state and required future
memory, references forcing, reconstructs a display value from its recipe and
parent, and omits diagnostics/scratch. Replay resolves the checkpoint,
restart-state closure, forcing, event, provenance, runtime identity,
configuration hash, and seed. Its injected arithmetic runner produces
`fixture:t1`; state and payload identities match the expected record and
authority remains `FIXTURE_ONLY`. `execute_replay` leaves store records
unchanged; the verified output is then submitted through `append_state`.

Queries prove chronological history, a known changed value, exact zero change,
false-to-true categorical change, and `UNKNOWN_INPUT` difference behavior.
WHY follows the declared replay recipe, checkpoint, parent states, forcing,
event, provenance, and fixture authority/source reference without rerunning
replay.

A separate refinement branch is declared from the parent state/checkpoint.
The B0-F reconstruction executor verifies the two child outputs; the branch,
materialized recipe, and child states are committed using the branch-bound
transaction. Parent state bytes and parent history IDs remain unchanged.
Child history contains only child states; child WHY can traverse to the parent
and checkpoint. Parent/child difference fails closed on incompatible spatial
support.

The store is reopened a second time. State/history/difference/WHY, replay,
refinement reconstruction, and accounting reproduce their prior semantic
results. A second fresh fixture root uses reversed initial insertion order;
semantic IDs, payload identities, query ordering, replay result, refinement
IDs, retention decisions, and canonical byte totals match. Filesystem times
and journal temporary IDs are not compared.

## Storage and failure qualification

Explicit scopes account the HistoryStore manifest/typed buckets as canonical
metadata, transaction journals as operational metadata, and external payloads
as canonical payload. Two references to one external payload count it once.
Scratch is separately classified and excluded from canonical persistent
bytes. A tiny cap override verifies both under-cap and exceeded outcomes.
During interrupted publication, staged records are hard links to destination
record paths; those shared inodes count once as canonical metadata, while
journal manifests and markers remain operational metadata.

Disposable copies test semantic-record tampering, payload-byte tampering,
forcing tampering, refinement-recipe tampering, and an ambiguous transaction
journal. Each is detected or rejected before trusted use. Interrupted initial
publication is recovered on a new store instance; a second reopen is
idempotent, preserves the sentinel record, and allows a complete retry.

## Integrated H1–H18 matrix

| Gate | Result | Integrated evidence / scope |
|---|---|---|
| H1 write integrity | PASS_INTEGRATED | Immutable typed records and injected transaction recovery |
| H2 reopen identity | PASS_INTEGRATED | Two real filesystem reopen boundaries and typed reads |
| H3 state query | PASS_INTEGRATED | Known state and explicit support statuses |
| H4 history query | PASS_INTEGRATED | Deterministic chronological history |
| H5 difference | PASS_INTEGRATED | Numeric change, zero change, categorical transition, unknown input |
| H6 WHY | PASS_INTEGRATED | Replay/refinement causal records and source references |
| H7 UNKNOWN | PASS_INTEGRATED | UNKNOWN state and UNKNOWN_INPUT difference preserved |
| H8 replay | PASS_INTEGRATED | Resolved closure, runtime/config/seed checks, verified runner output |
| H9 append-only | PASS_SCOPED | Immutable outputs, no replay auto-write, explicit append |
| H10 branch isolation | PASS_INTEGRATED | Parent bytes/IDs unchanged; child records remain branch-scoped |
| H11 reconstructability | PASS_INTEGRATED | B0-G recipe/parent/forcing references and B0-F child reconstruction |
| H12 storage accounting | PASS_INTEGRATED | Explicit category scopes, deduplication and cap check |
| H13 payload integrity | PASS_INTEGRATED | Reopen identity separation and tampered-byte rejection |
| H14 support boundaries | PASS_SCOPED | Exact cell-set, unknown/outside and unsupported-selector behavior; general GIS containment remains outside scope |
| H15 authority | PASS_INTEGRATED | Fixture authority remains explicit across replay/refinement |
| H16 minimal state | PASS_INTEGRATED | Required memory retained; display derived; diagnostics omitted |
| H17 deterministic ordering | PASS_INTEGRATED | Reversed insertion across fresh roots yields same semantic order/results |
| H18 failure atomicity | PASS_INTEGRATED | Injected interruption, no partial publication, idempotent recovery |

## Scientific side-effect boundary

The fixture does not load or change a governed T0 payload or scientific
authority. It does not select `dt`, create a canonical T1, promote a provider,
run ShellSet, or execute OrbData mechanics. Only synthetic `fixture:t0` and
`fixture:t1` are used. Existing authorization values remain unchanged.

## Limits

This qualifies the current local file-backed store and injected deterministic
adapters. It does not qualify remote object stores, general GIS containment,
scientific replay adapters, production checkpoint density, or concurrent
filesystem mutation during an accounting pass. The replay API resolves an
expected output state record as part of its current validation contract; the
test confirms execution itself does not add records and then explicitly calls
the normal append API for the verified result.
