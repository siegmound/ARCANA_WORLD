# B6M-R1 first canonical T1 publication

## Result

**Blocked before canonical publication.** Source baseline `c01d40c6e9d88ab915fc43767d98a35b032bd49b` is readable on branch `r6/b6m-r1-atomic-first-t1-publication`. The complete active R6 suite passed: 448 passed, 0 failed, 0 errors.

## Blocking contract gap

The requested acceptance requires that no canonical reader can observe a partial T1 bundle. The qualified B0-C implementation does not promise this. `HistoryStore.append_transaction` states that concurrent visibility is outside its contract (`src/arcana_worldsim/r6/store.py:231`), publishes target files sequentially before its `COMMITTED` marker (`:295`), and typed reads directly inspect files without coordinating with that marker (`:488`). B6L likewise records `OUTSIDE_B0C_CONTRACT` for concurrent visibility. A single-writer successful-reopen guarantee is insufficient evidence for the stronger reader-visibility requirement.

## Canonical store preserved

The store remains `r6canonical_18bab1f51f02b62f6b78e893b24c9fd81f8d48b8ed30d513c6d19141ebf3e4a0`, with one T0 epoch at 210 Ma, 14 governed state records, one authority anchor, no active transactions, no T1, and 35,375 persistent bytes. The B6K candidate payload still hashes to `9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a`.

## Gates and next step

`t1_created=false`, `canonical_state_changed=false`, `topology_transition_executed=false`, `mechanics_authorized=false`, `forward_evolution_authorized=false`, `SECOND_DT_SELECTED=false`, and `T2_CREATED=false` remain in force. The next required stage is to authorize and qualify a narrowly scoped canonical transaction reader-visibility guarantee, then resume B6M-R1. No commit or push was made.

Machine-readable evidence is in `outputs/r6_b6m_r1_atomic_first_t1_publication/`.
