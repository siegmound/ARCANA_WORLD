# R4.11-R1 — Effective N0 Semantics Repair

The initial R4.11 candidate correctly re-extracted all 56 `summary_popAllTime.csv` files but compared their initial population against the raw sum of `PatchVars.N0`.

Pinned CDMetaPOP 3.08 does not initialize positive `N0` on non-natal patches. In `CDmetaPOP_PreProcess.py`, after selecting the first CDClimate `N0` knot, any patch with `Natal Grounds == 0` is forced to `N0 = 0` before `InitializeID`.

R4.7/R4.8/R4.9 intentionally write their start-state `N0` formula to every PatchVars row, including the generic example's non-natal migration patch. Therefore raw PatchVars N0 sum is not the engine-effective initialized population.

R4.11-R1 repairs only the integrity gate:
- preserve raw configured N0 sum;
- calculate engine-effective N0 using the pinned first-knot + non-natal-zeroing semantics;
- record the N0 amount removed by the engine rule;
- require `raw - effective == nonnatal_zeroed`;
- require summary `N_Initial` row 0 to equal engine-effective N0 exactly;
- keep lifecycle-chain validation unchanged;
- perform no engine rerun and no canonical write.

The previous blocked R4.11 result remains valid negative process evidence; it did not execute readjudication or modify canon.
