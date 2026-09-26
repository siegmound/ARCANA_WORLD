# R6 Ubuntu external payload migration manifest

The machine-local binary root is selected by `ARCANA_EXTERNAL_ROOT`; absent
that variable, R6 resolves `_ARCANA_EXTERNAL_SOURCES` beside the repository.
The canonical initial-world payload could not be rehashed in this session
because filesystem access was denied. Its registered byte size and SHA256 are
preserved exactly; no permission changes were attempted. The vector partition,
R3.28 clock source, and A1 reference were locally rehashed successfully.

| Payload | Requirement / role | Bytes | SHA256 | Ubuntu placement / status |
|---|---|---:|---|---|
| R6 initial physical geography | Required t0 state | 1,169,900 | `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c` | `$ARCANA_EXTERNAL_ROOT/r6/initial_world/r6run_85af40f36fcb86c23a3571744817780a28e22740f6eaa04ae432bfe7d21f7f65/R6_INITIAL_PHYSICAL_GEOGRAPHY.npz`; registered, rehash unavailable |
| R6 vector plate partition | Required for t0 topology diagnostics | 5,681,184 | `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab` | `$ARCANA_EXTERNAL_ROOT/r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz`; verified |
| R6 HistoryStore | Optional persisted history store, 9 states | — | — | Under the same `r6/initial_world/r6run_.../world_history` package directory; availability unverified |
| R3.28 replay | Required temporal-clock source; not material-state authority | 975,043 | `16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a` | repository-relative `outputs/v0_6D1_R3_28/...`; verified locally |
| A1 reference trajectory | Optional comparison input, never R6 history | 2,928,319 | `9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f` | repository-relative `references/v0_6D1_R3/...`; verified locally |

Copy non-Git payloads without transformation and verify their registered SHA256
on Ubuntu. The A1 and R3.28 rows retain their restricted scientific roles.
