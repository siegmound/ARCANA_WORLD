# B0-C — WORLD_HISTORY Persistence Failure Boundaries and Atomicity

## Contract

`HistoryStore.append_transaction(records)` accepts a non-empty iterable of already-formed typed R6 state, provenance, event, checkpoint, temporal or refinement-branch records. It does not accept paths or arbitrary filesystem operations. One writer is supported.

- **Success:** every requested record has been published and the durable logical commit marker exists before the method returns.
- **Ordinary failure before commit:** rollback removes only newly published transaction records. The call raises after rollback; if rollback cannot finish, recovery metadata remains and the store fails closed on the next open if state is ambiguous.
- **Process interruption:** the next `HistoryStore` initialization deterministically rolls back an uncommitted transaction or validates and finalizes a committed one.
- **Conflict:** typed IDs are verified, duplicate targets rejected, and existing target bytes compared before the transaction directory or any target record is created. Byte-identical existing records are idempotent/pre-existing members.
- **Visibility:** no guarantee of atomic visibility to another concurrent process during the short publication window. Concurrent writers are outside scope.

The guarantee is recoverable logical atomicity for a single writer on a local filesystem. It is not a claim of cross-platform full power-loss durability or database ACID semantics.

## Journal and state model

Internal transaction metadata is stored under `.history_transactions/<transaction-id>/`:

```text
manifest.json
PREPARED.json
PUBLISHING.json
COMMITTED.json
staged/<ordinal>.json
```

Only the markers reached by the operation exist. The manifest contains the deterministic operational transaction ID, current store schema, and each safe bucket/key, staged relative name, expected SHA-256 of the canonical serialized record, and whether identical bytes existed before publication. No absolute path or timestamp is stored. Transaction identity is a SHA-256 over this operational manifest content; it does not replace or enter semantic state/event/checkpoint/provenance identities.

All inputs are serialized and identity-checked, duplicate paths rejected, and existing content preflighted before journal staging. After every staged record and the manifest are installed, `PREPARED` is written; `PUBLISHING` is written before the first target. Target files are installed with a no-overwrite hard link from the staged file.

**Logical commit point:** atomic installation of `COMMITTED.json`, after all target files are present. A committed journal is only finalized on reopen if every target exists with its expected digest. An incomplete committed bundle fails closed.

## Rollback and recovery

Before commit, rollback walks the manifest. A newly published target is removed only if its current bytes match the journal’s expected digest. Pre-existing identical targets are preserved. Missing pre-existing targets, unexpected target content, malformed markers, invalid transaction IDs, invalid paths, duplicate journal targets, or a corrupt manifest raise `TransactionRecoveryError`; recovery never guesses which content to delete.

After successful rollback or committed validation, the journal directory is atomically renamed under `.history_transactions/.retired/` before best-effort deletion. Retired cleanup cannot change record files. Reopen may safely retry deletion. Recovery is idempotent.

A journal directory with no manifest and no publication evidence is discarded only when it is empty. If stage content or state markers exist without a valid manifest, recovery fails closed because the transaction state is ambiguous.

## Durability and platform boundary

Record and journal files are flushed and `fsync`ed before their directory entries are installed. On platforms/filesystems that expose directory descriptors, directory `fsync` is attempted after link, rename and removal operations. Unsupported directory `fsync` is best-effort and does not fail normal Windows operation. Windows therefore gets process-interruption recovery and file flushes, but no asserted portable directory-entry or full power-loss guarantee. Device/controller caches, filesystem guarantees and sudden power failure remain outside proof.

## Fault-injection and regression evidence

`tests/test_r6_world_history_b0_c.py` uses only synthetic typed records. It tests complete publish/reopen, preflight conflict with no new target, ordinary failures before publication/after one/after multiple/before commit, preservation of byte-identical and unrelated pre-existing records, simulated process interruption followed by a new store instance, idempotent recovery, corrupted-journal fail-closed behavior, committed cleanup interruption/reopen finalization, and unchanged idempotent single-record append.

- Focused B0-C tests: **11 passed**.
- Default active R6 suite: **270 passed** (259 baseline after B0-B plus 11 B0-C cases).
- `py_compile`: PASS for changed Python modules/tests.
- `git diff --check`: PASS.

## Gate and remaining limits

**H18: IMPLEMENTED_AND_TESTED** for the declared single-writer, process-interruption, local-filesystem logical atomicity contract. Full power-loss durability and concurrent atomic visibility are explicitly excluded.

The transaction API currently covers the existing typed state/provenance/event/checkpoint/temporal/refinement record classes. Provider binding records remain supported by their existing single-record append/read API; they do not yet have a typed immutable envelope accepted into a multi-record bundle. There is no concurrent-writer coordination, multi-record query isolation, remote-filesystem guarantee, or proven full power-loss durability. No B0-D replay/forcing behavior was added.

## Changed files

- `src/arcana_worldsim/r6/store.py`
- `tests/test_r6_world_history_b0_c.py`
- `docs/arcana/B0_C_PERSISTENCE_FAILURE_ATOMICITY_CLOSURE.md`
