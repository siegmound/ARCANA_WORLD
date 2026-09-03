# ARCANA WorldSim v0.6D1-R5.3
## Corridor-Conditioned Demographic Persistence and Bottleneck Validation

R5.3 is the first demographic/neutral-genetic challenge after the R5.1 cradle and R5.2 connectivity work.

### Authority
- R5.2 final seal is immutable parent evidence.
- R5.1 robust cradle families and J14 spatial authority define the ARCANA spatial network.
- RangeShiftR geometry/output is **not** promoted into CDMetaPOP input authority.
- R5.2 sensitivity results are carried only as reporting strata attached to each robust family.
- CDMetaPOP 3.08 is pinned to commit `3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118`.

### Scientific question
Given ARCANA-defined cradle/network structure, how robust are standardized demographic systems to progressively stronger bottleneck challenge conditions, and what engine-native loss/recovery of population size and neutral diversity is observed?

### Standardized diagnostic scale
The CDMetaPOP census values are deliberately **not** mapped to literal ARCANA individuals:
- D0: source N0=60, patch K=120
- D1: source N0=30, patch K=90
- D2: source N0=12, patch K=60

Each robust family is represented by its q99 R5.1 core plus downstream J14 occupancy-supported patches, deterministically capped at 32 patches. R5.2 RangeShiftR cells are never used to construct that network.

Neutral genetics uses 16 biallelic loci with no selection and zero mutation. These are diagnostic markers, not canonical ARCANA genome architecture.

### Evidence
Only the already-governed CDMetaPOP readout fields are adjudicative evidence fields:
`Year`, `N_Initial`, `Alleles`, `He`, `Ho`.

Extinction, severe bottlenecks or diversity loss are valid results. They never count as runtime failure. Scientific PASS/FAIL is not inferred automatically from those numbers.

### Execution size
12 robust families x 3 fixed stress profiles x 2 fixed seeds = 72 streams.

A one-stream full-input pilot must pass before the remaining corpus runs. `-Resume` reuses only streams with exact seed + engine commit metadata.

### Seal policy
R5.3 intentionally produces a scientific **candidate**, not a seal. The project now seals only substantial multi-step scientific blocks. R5.3 should remain candidate/audit evidence while the demographic/genetic block continues (e.g. NEMO/contact validation), then receive one larger closure seal later.
