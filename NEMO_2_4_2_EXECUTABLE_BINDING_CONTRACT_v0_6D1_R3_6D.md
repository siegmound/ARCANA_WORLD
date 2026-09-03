# NEMO 2.4.2 executable binding contract — v0.6D1-R3.6D

## Purpose

Bind the independent NEMO reference to **actual NEMO 2.4.2 syntax and lifecycle semantics** without changing ARCANA WorldSim scientific state.

R3.6D is an evidence stage. NEMO is never a canonical-state writer.

## Version authority

Required executable basename:

`nemo2.4.2`

The runner fails closed if that executable is unavailable. The installation helper uses the upstream-recommended conda channels `conda-forge` and `ecoevo`.

## Quantitative trait mapping

ARCANA R3.6B represents one locus as

`A_l = a_l (g_l - 1)`, `g_l in {0,1,2}`,

so genotype contributions are `{-a_l, 0, +a_l}`.

NEMO additive quantitative traits sum two allelic values. Therefore R3.6D renders the symmetric diallelic alleles as:

`{-a_l/2, +a_l/2}`.

This is an exact algebraic mapping of the R3.6B genotype contribution, not a fitted correction.

Initial allele frequencies use upstream `quanti_init_freq`; locus effects use `quanti_allele_value`.

## Population mapping

The reference uses hermaphroditic random mating (`mating_system 6`) and represents the requested literal NEMO individual count with:

- `patch_nbfem = N` per patch;
- `patch_nbmal = 0`.

It does **not** use `patch_capacity`, which would split carrying capacity between the two NEMO sex containers.

ARCANA WorldSim population units are not asserted to equal literal individuals. Population-size sensitivity is therefore mandatory.

## Life cycle

Authorized primary NEMO life cycle:

1. `quanti_init`
2. `breed_disperse`
3. `save_stats`
4. `save_files`

with:

- `mating_system 6`;
- `mating_isWrightFisher`.

Current NEMO source implements `breed_disperse` as backward/gametic parent-source migration and performs Wright-Fisher parent/offspring replacement internally.

## Migration semantics gate

R3.6C produces a cadence-normalized per-generation transition matrix. `breed_disperse` validates backward matrices by **column** sums.

R3.6D therefore accepts only the authorized symmetric B0/B1/C3 reference matrices, for which:

- `D = D^T`;
- every row sums to one;
- every column sums to one.

Non-symmetric matrices are rejected. R3.6D never silently transposes or projects a matrix into another biological operator.

This NEMO backward/gametic process is treated as an independent genetics reference; it is not declared ontologically identical to ARCANA deme exchange.

## Primary biological protocol

The first executable reference isolates:

`admixture + recombination + finite-N drift`.

Locked:

- NEMO mutation rate = 0;
- no NEMO selection operator;
- free recombination parameter = 0.5.

Rationale: ARCANA `mu` and `b` are moment/homeostasis parameters. Mapping them directly to NEMO locus mutation or Gaussian selection would introduce a new, unvalidated biological model.

## Governance

NEMO output may produce a `ScientificEvidenceBundle` only.

Forbidden in R3.6D:

- direct canonical write;
- automatic `mu`/`b` change;
- automatic ceiling change;
- NEMO-defined ARCANA speciation/extinction;
- automatic calibration promotion.
