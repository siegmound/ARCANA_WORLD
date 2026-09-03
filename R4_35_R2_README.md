# ARCANA WorldSim v0.6D1-R4.35-R2
## Schema-True Authority Reader Repair + R4.35 Reseal

R4.35-R1 proved four consumer-schema assumptions were wrong:

1. R4.3 seed authority is 23 jobs × 4 ordered replicate seeds = 92 frozen seeds.
2. J18 R4.23 explicitly selects `snapshot_deme_state` + `snapshot_active`;
   `cha2_deme_state` is not a competing selector for the J18 binding.
3. J18 `grid_row/grid_col` are continuous coordinates within the explicit
   R3.28 `90x180` grid authority and must be preserved directly, with no `+0.5`.
4. J21 arrays encode grid axes before the final variable axis, and both
   `anchor_age_ka` copies are exact-equivalent canonical authority copies.

R2 corrects only these readers/validators and reseals the R4.35 source manifest.

It does not modify R4.3/R3.28/R4.23/R4.31, execute Geonomics, materialize
native Geonomics params, call make_model, execute numeric targets, perform
readjudication, or change canonical state.

Run:
    .\run_v0_6D1_R4_35_R2_repair_and_reseal.ps1
