# ARCANA R6 — FAIR G2/G3 32/32 PASS and next coupled physical decision

Date: 2026-11-19. FAIR terminal supplied by operator. Verified commit:
`3efc07b3b573fae11d5cc91ce05dfc21a365a5de`.
Environment: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY`,
Conda `arcana-r6-linux`; detached checkout from
`r6/multiphysics-integration-20261026`.

## Operator-reported terminal

```text
HEAD is now at 3efc07b3 feat(r6): enforce exact G2 thermal lab coverage and single-owner G3 GPE force accounting
3efc07b3b573fae11d5cc91ce05dfc21a365a5de
................................ [100%]
32 passed in 0.25s
```

The previous instruction specified exactly these four files:

- `tests/test_r6_g2_exact_thermal_validity.py`
- `tests/test_r6_g3_gpe_force_accounting.py`
- `tests/test_r6_g2_viscoplastic_explore.py`
- `tests/test_r6_g3_gpe_hydrostatic.py`

Results support test success for source-oriented mathematical hypotheses,
exact cubic PRE temperature bounds, and candidate GPE force-channel
accounting. They **do not** establish actual material validity, real
basal normal support, external mantle tractions, force equilibrium or
SHELLS equivalence. The raw FAIR test reports/evidence were not pulled
into this GitHub environment; this report faithfully records the
operator's terminal rather than independently reproducing a run.

## Physical-closure decision — not yet ratified

**G2** needs a source-qualified crust/mantle material assignment with
full-column temperature/pressure/strain-rate validity, explicit water
fugacity and pore pressure/Biot, adequate brittle-friction/yield and
ductile response, and a conscious solver choice between original
SHELLS shared `eCreep` and a separately validated experimental two-exponent
continuum. No generic quartzite GT95 assignment to a T0 cold crust.

**G3 A** needs source-bound 5:8:11 north/south and other outer-cut traction
states, basal tangential traction/deep-mantle flow, basal normal reference,
and explicit one-owner gravitational potential energy without
`Squeez`/`Fixed` double-count. Source FEG elevation is
`NUMERICAL_DERIVED_SUPPORT`; the `-200000m` reference is EXPLORE-only.
The 8x8 and 16x16 norms are not net-force convergence evidence.
Then, and only then, can rank/gauge, conservation and mechanical
sensitivity be scientifically judged.

## Continuation

Do not request more shape-only FAIR checks or repeat 32/32 without a
changed codebase. The next meaningful deliverable is **one paired
G2/G3 physical parameter and provider decision** distinguishing
`SOURCE_AUTHENTIC`, `LITERATURE_ANALOGUE_EXPERIMENT`, `AUTHOR_RATIFIED`
and `UNKNOWN`, with fail-closed nulls for missing sources.
No auto-selection of geology or world physics.

```yaml
G2_software_tested: true
G3_force_accounting_tested: true
G2_physical_material_ratified: false
G3_physical_force_balance_ratified: false
MECHANICAL_SOLVE_AUTHORIZED: false
PHYSICAL_T1: null
D_024: ACTIVE
```
