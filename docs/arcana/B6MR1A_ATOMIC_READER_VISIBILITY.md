# B6M-R1A Atomic Reader Visibility

## A. Scope and source

This infrastructure-only stage extends the B0-C transaction contract with a
committed read-view for the canonical local WORLD_HISTORY store. Qualification
source is recorded in `outputs/r6_b6m_r1a_atomic_reader_visibility/`.

## B. Visibility contract

Typed records are visible only when their identities occur in the immutable
committed read-view selected by `.history_visibility/CURRENT.json`. Physical
record files and transaction markers are not visibility authority. Each
logical query pins one view before resolving records, so publication during a
compound query cannot mix generations.

## C. Publication and writers

Writers serialize with a per-root in-process lock and an exclusive local
process lock. A complete content-addressed view manifest is installed before
publication. `os.replace` of a same-directory temporary pointer over
`CURRENT.json` is the single reader-visible linearization point. On Windows,
the implementation fails closed unless the store is on a fixed local NTFS
volume. Direct filesystem inspection is outside the supported-reader
guarantee.

## D. Recovery and migration

Before the pointer switch, records and view manifests are unreachable
orphans; recovery restores the previous complete view. After the switch,
recovery validates and completes the new transaction. Ambiguous view lineage
fails closed. Legacy stores without a pointer require explicit deterministic
migration; ordinary opens do not infer membership from raw directories.

The canonical migration is metadata-only. It must preserve the B6M0 store
identity, all 14 T0 domain-state records at 210 Ma, two provenance records,
the single authority anchor, and the absence of T1. The retained machine
evidence records before/after hashes for every pre-existing canonical file.

## E. Concurrency qualification

Deterministic tests cover visibility barriers, uncommitted record hiding,
thread and independent-process pinned readers, compound-query coherence,
stale parent rejection, idempotence, and interruption before/after the switch.
The guarantee applies to WORLD_HISTORY typed/query APIs on the supported
local filesystem; it does not protect arbitrary readers or network filesystems.

## F. Scientific boundary

No scientific payload, T0 state, candidate payload, topology, or model value is
changed. This stage does not publish T1, select another dt, run mechanics, or
execute a transition. If qualified, the only next action is to resume the
separately governed atomic first-T1 publication stage.

## G. Evidence

See the machine-readable result, migration hashes, validation outcomes, and
artifact manifest under
`outputs/r6_b6m_r1a_atomic_reader_visibility/`.
