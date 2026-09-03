# v0.6D1-R4.1 — Multi-Engine Semantic Calibration, Controlled Microbenchmarks & Historical Window Execution Gate

## Status
`CANDIDATE — EXECUTABLE LOCAL EVIDENCE REQUIRED`

Parent authority: **v0.6D1-R4.0 SEALED**.

R4.1 is the first scientific execution stage after the multi-engine runtime/governance seal. It intentionally does **not** execute the seven World-1 historical revalidation windows. Before a 210 Ma→0 ka comparison is scientifically meaningful, each external engine must demonstrate executable behavior and ARCANA must freeze what its outputs mean, which quantities are comparable, and which engines have interpretive authority for each domain.

## Canonical invariants

- `ARCANA_WorldSim` remains the sole canonical world-state and clock owner.
- External engines remain evidence providers/oracles only.
- No external result writes canonical state.
- No parameter is automatically promoted.
- R3.19–R3.39 remain preserved as `ARCANA_REDUCED_ORDER_BASELINE_A`.
- Deep biological coupling remains `OFF`.
- A benchmark PASS does **not** imply agreement with ARCANA.
- A benchmark FAIL is preserved as evidence; thresholds are not lowered to force a PASS.

## Why controlled microbenchmarks come before paleohistory

R4.0 proved that the pinned executables exist. That is necessary but insufficient. The engines use different ontologies:

- NEMO uses literal genetically explicit individuals and population-genetic life cycles.
- Geonomics uses spatially explicit individuals, landscapes and optional genomic/ARG state.
- Madingley uses functional heterotroph cohorts and autotroph stocks rather than ARCANA species identity.
- RangeShiftR uses individual-based demographic/dispersal/range dynamics.
- CDMetaPOP uses spatial demogenetic populations and landscape movement.
- SLiM uses explicit forward-time population genetics and tree-sequence ancestry.

Therefore R4.1 validates **executable semantics**, not numerical equality between native engine state variables.

## Controlled benchmark suite

### B1 — NEMO admixture convergence
A two-deme, eight-locus, symmetric-migration NEMO 2.4.2 run uses the already validated R3.6D/R3.7 life-cycle syntax. Initial allele-frequency separation is fixed before execution. PASS requires a finite final gap, materialized qfreq output, and a final mean frequency gap lower than the pre-result initial gap. This validates realized migration/recombination/finite-N behavior only; it does not equate NEMO `N` with ARCANA population units.

### B2 — Geonomics spatial demography
The documented Geonomics default model is executed. R4.1 extracts terminal species abundance and occupied-cell support from `Model.comm -> Species`, including the `Species.N` density raster. PASS requires a completed model, at least one species, positive terminal population and positive occupied support.

### B3 — Madingley ecosystem execution
MadingleyR 1.0.6 / C++ 2.02 initializes a small terrestrial spatial window and executes one simulated year. PASS requires non-empty heterotroph cohort and autotroph stock state before and after the run. These states validate ecosystem-provider functionality; they never define ARCANA species identity.

### B4 — RangeShiftR range dynamics
RangeShiftR 3.0.1 executes a short artificial-landscape simulation with explicit output intervals and one replicate. The dedicated RangeShiftR `Occupancy` output is a multi-replicate product and therefore requires at least two replicates; on the governed Linux runtime the two-replicate path produced a native segmentation fault after a successful first replicate. R4.1 does **not** reinterpret that product. Instead it requests the engine-native `ReturnPopDataFrame=TRUE` output for one replicate and derives instantaneous occupied cells transparently as the count of cells/patches with `totalAbundance > 0` at each year. Free initialisation uses `FreeType=1`, i.e. all suitable cells, avoiding an arbitrary `NrCells` choice. PASS requires positive initial and terminal abundance/instantaneous occupancy. This metric is explicitly labelled `single_replicate_positive_abundance_cells` and must not be equated downstream with RangeShiftR's cross-replicate Occupancy output.

### B5 — CDMetaPOP bundled 3.08 example
The pinned source commit `3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118` is copied to an isolated runtime working area and its generic bundled `RunVars.csv`/`PopVars.csv` example is used as the source authority. The pinned source unconditionally reads `implement_disease`, while the generic pinned `PopVars.csv` predates that column. R4.1 therefore applies a documented input-schema compatibility shim **only to a benchmark copy**, adding `implement_disease=N`; `N` is an explicitly valid v3.08 value and keeps disease disabled. Because the upstream generic `PopVars.csv` contains four deliberately different parameter rows, the controlled microbenchmark freezes exactly the **first pinned generic row** into `PopVars_R41.csv`; otherwise later rows exercise additional population-model semantics unrelated to this 5-generation smoke test. The source tree and upstream example files remain unmodified. PASS requires exactly one benchmark PopVars row, the complete pinned generic parameter chain, positive configured runtime, successful process completion and materialized output CSV evidence.

### B6 — SLiM tree-sequence gene-flow pipeline
SLiM 5.2 executes two diploid populations with symmetric migration for fifty generations while recording tree-sequence ancestry. The resulting `.trees` file is opened with the pinned tskit stack. PASS requires non-empty nodes, edges and individuals. Mutation count may legally be zero in a finite short stochastic run and is therefore recorded but not forced positive.

## Semantic normalization rules

### Population
There is no literal cross-engine equality of population counts. ARCANA comparisons use persistence probability, relative abundance change, normalized occupancy and replicate distributions. In particular, a NEMO individual count is not an ARCANA macrofaunal effective-abundance unit.

### Time
Years, generations and engine timesteps are not silently equated. Every historical adapter must provide an explicit generation/timestep mapping before R4.2 execution.

### Space
Cross-engine spatial comparison requires explicit cell area and an eligible-habitat denominator. Preferred comparison quantities are occupied fraction, centroid displacement, connectivity and support persistence.

### Genetics
Input parameters with similar names are not assumed ontologically identical. Comparison is made on realized allele-frequency change, realized exchange, variance response, ancestry and distributional effect sizes.

### Ecosystem
Madingley functional cohorts/stocks inform biomass and trophic opportunity. They cannot create, rename or extinguish ARCANA species directly.

### Uncertainty
The six R4.1 runs are semantic/executable gates. Historical scientific claims require replicate distributions downstream.

## Domain-specific authority — no majority vote

R4.1 freezes an explicit primary/secondary engine map for all 15 R4.0 comparison domains. `vote=false` for every domain. Discordant evidence must be interpreted by domain semantics, model assumptions, resolution and sensitivity—not by counting engines.

Examples:

- biomass / trophic opportunity: Madingley primary;
- range shift: RangeShiftR primary;
- ancestry: SLiM primary, Geonomics secondary;
- gene flow/admixture: NEMO, SLiM and CDMetaPOP have complementary primary roles;
- trait response: SLiM and Geonomics primary; no unvalidated NEMO selection mapping is introduced.

The exact matrix is machine-frozen in `configs/world1_r41_semantic_calibration_v0_6D1_R4_1.json`.

## Historical window gate

R4.1 preserves the exact seven R4.0 windows and their earliest replay boundaries. Window selection is pre-result and unchanged. If and only if:

1. R4.0 parent seal is exact and intact;
2. the R4.0 frozen matrix hash is unchanged;
3. all six runtime identities remain exact;
4. all six controlled benchmarks PASS;
5. all 15 domains have a non-voting authority definition;
6. canonical state remains untouched;

then R4.1 emits `AUTHORIZED_FOR_R42` and seals the permission to execute the historical revalidation windows in **v0.6D1-R4.2**.

R4.1 still makes **no scientific agreement claim** about World 1.

## Final sealed status

`PASS_R41_MULTI_ENGINE_SEMANTIC_CALIBRATION_CONTROLLED_MICROBENCHMARKS_AND_HISTORICAL_REVALIDATION_GATE_SEALED`

This status seals the semantics and controlled execution gate only. It does not seal any new biological history.
