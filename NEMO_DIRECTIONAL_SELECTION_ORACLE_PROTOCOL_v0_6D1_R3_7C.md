# v0.6D1-R3.7C — NEMO Directional-Selection Oracle Protocol

## Purpose
R3.7B closed the neutral `(VA_within, S)` lifecycle against real NEMO B2 evidence, but B2 had selection disabled. R3.7C therefore isolates the missing question: how much latent polygenic segregation displacement accompanies an observed heritable directional trait response under explicit quantitative-genetic selection?

## Engine binding
The oracle is pinned to NEMO 2.4.2 and uses the public NEMO selection interface verified against the 2.4.2 source/manual:

- LCE: `viability_selection`
- trait: `quant`
- model: `gaussian`
- fitness interpretation: `relative_local`
- dimensionality: `selection_trait_dimension 1`
- selection strength: `selection_variance`
- patch-local optima: `selection_local_optima`

Reference URLs:
- https://nemo2.sourceforge.io/
- https://github.com/ecoevocode/nemo-release/blob/master/src/LCEselection.cc
- NEMO/NEMO-age user-manual selection sections describing Gaussian selection and patch-specific optima.

## Matched-fork design
For each `(N, replicate, trait-axis)` one common 4-deme QTL architecture is generated with mean trait 0 and `VA=0.045` in every deme. The same architecture is reused across both tested selection strengths.

### Phase 0 — COMMON_BURNIN
- 200 transitions
- connected four-deme chain
- migration rate 0.03 per linked edge per generation
- no selection
- no mutation
- free recombination (`r=0.5`)

The final `.qfreq` state is the exact fork point for all branches.

### Phase 1A — FRAGMENTED_DIVERGENT_SELECTION
- 300 transitions
- split into two connected pairs: `{0,1}` and `{2,3}`
- Gaussian viability selection
- local optima `[-0.6,-0.6,+0.6,+0.6]`
- `selection_variance` in `{1.0, 4.0}`

### Phase 1B — FRAGMENTED_MATCHED_NEUTRAL
Identical fork state, exchange geometry, population size and engine seed, but no `viability_selection` event.

### Phase 2 — RECONNECTED_RELAXED
Each selected/control branch is independently reconnected for 400 transitions with selection disabled. This tests whether adaptive excess segregation potential transforms under ordinary migration/recombination/drift rather than being protected by continuing divergent selection.

## Primary observables
For left group `L={0,1}` and right group `R={2,3}`:

`D_z = mean(z_R) - mean(z_L)`

`S_cross = mean(S_ij), i in L, j in R`

Matched-neutral subtraction defines:

`Delta z_adapt = D_z(selected) - D_z(neutral)`

`Delta S_adapt = S_cross(selected) - S_cross(neutral)`

The dynamic participation estimate is:

`K_eff = (Delta z_adapt)^2 / (2 Delta S_adapt)`

when `Delta S_adapt > 0` and the trait response is aligned with the divergent optima.

## Why two selection strengths
`selection_variance=1` and `4` test whether a scalar `K_eff` is stable as the Gaussian fitness surface changes strength. The values are oracle protocol settings, not World-1 physical constants.

## Phase-boundary limitation
The chain passes allele frequencies via `.qfreq`. Genotype phase and LD are reset at each boundary. Therefore the authoritative observables are allele-frequency-derived `z`, genic `VA`, and `S`; cross-boundary LD persistence is not claimed.

## Governance
Evidence completion does not automatically authorize a production `K_eff` value. R3.7C must first determine whether the inferred participation number is sufficiently stable across N, axis, replicate and selection strength, or whether a state-dependent rule is required.
