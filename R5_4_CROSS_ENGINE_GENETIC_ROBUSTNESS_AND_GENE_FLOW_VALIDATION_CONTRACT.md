# ARCANA WorldSim v0.6D1-R5.4 — Cross-engine genetic robustness and gene-flow validation

## Scientific question
Given the twelve robust R5.1 cradle families and their ARCANA/J14-supported downstream network structure, does a second, genetically explicit metapopulation engine show stable, interpretable drift/gene-flow behavior across the same fixed diagnostic census challenges used to stratify R5.3?

R5.4 is a **scientific candidate stage**, not a sealing stage.

## Engine utility adjudication
NEMO 2.4.2 is useful here because R5.3 already exercised demographic persistence and bottlenecks in CDMetaPOP, while NEMO provides an independent forward-time, genetically explicit metapopulation implementation with allele-frequency output and explicit dispersal. R5.4 therefore targets genetic robustness rather than repeating CDMetaPOP demographic viability.

CDMetaPOP values do **not** parameterize NEMO. The R5.3 sensitivity table is joined only after NEMO execution for descriptive side-by-side reporting.

## Fixed challenge
- 12 robust families.
- 3 standardized fixed-N census profiles: 60, 30, 12 individuals per NEMO patch.
- 2 variants: `FLOW` and `MATCHED_NO_FLOW`.
- 2 independent seeds: 540401 and 540402.
- 16 diallelic marker loci, deterministic alternating initial p=0.25/0.75.
- mutation 0; no selection; recombination 0.5.
- 40 breed/disperse transitions represented by `generations=41` because NEMO generation 1 is initialization.
- `FLOW` uses a symmetric doubly-stochastic distance-weighted network with total off-diagonal flow mass 0.05; `MATCHED_NO_FLOW` is identity.
- 144 streams total.

These counts, generations and marker loci are standardized engine-native diagnostics. They are not literal historical population sizes, literal ARCANA years, or a canonical genome.

## Spatial authority
The network is reconstructed directly from R5.1 q99 cores plus J14 downstream occupancy using the already governed R5.3 selection rule. R5.2 RangeShiftR geometry and R5.3 CDMetaPOP numeric outputs are not promoted into NEMO input authority.

## Inference
Primary evidence is paired `FLOW - MATCHED_NO_FLOW` behavior for:
- expected heterozygosity retention;
- fixed patch×locus fraction;
- among-patch allele-frequency variance;
- global allele-frequency drift.

R5.3 CDMetaPOP He/allele-retention ranges are carried beside these records only as heterogeneous descriptive evidence. No agreement score, weighted score, majority vote, forced equality, calibration or automatic scientific PASS/FAIL is authorized.

## Runtime provenance
The scientific run requires the governed Conda environment to contain exactly one `nemo` package at version `2.4.2`, resolves the explicit `nemo2.4.2` executable, and records its fresh SHA-256. A renamed or differently-versioned fallback executable is not accepted.

## Closure policy
R5.4 remains CANDIDATE. A larger later milestone may jointly seal the R5.3/R5.4/contact-history block; R5.4 does not create a micro-seal.
