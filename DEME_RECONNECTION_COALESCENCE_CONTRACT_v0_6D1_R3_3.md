# v0.6D1-R3.3 — Persistent Deme Reconnection / Coalescence Contract

Status: **CANDIDATE — PASS LOCAL CLOSURE; 210→150 Ma production rerun pending**

## Purpose
R3.3 closes the demographic lifecycle left asymmetric by R3/R3.1/R3.2. Persistent-vicariance fission remains a demographic event, not speciation. A fragment may now be reabsorbed only after persistent secondary contact while it is still the **same current species**.

## Reuse-first implementation
No external population-genetics simulator is inserted. The runtime already represents population-genetic state through component means, additive variances, RI and isolation clocks; `msprime/tskit` would require a sequence/genealogy ontology not present in WorldSim. R3.3 therefore reuses:

- D3.2B barrier-coupled migration and contact/gene-flow source unchanged;
- D3.3A exact first/second-moment gene-flow mixing and Riccati VA homeostasis;
- D3.0C RI/isolation/effective-exchange thresholds;
- SciPy `sparse.csgraph.connected_components` for transitive coalescence groups.

## Coalescence gate
A pair can accumulate reconnection persistence only if all are true:

1. `current_species_i == current_species_j`;
2. effective exchange pressure is **greater** than the existing D3.0C speciation ceiling `0.25`;
3. intrinsic RI is below the existing D3.0C species-level RI threshold `0.65`;
4. isolation clock has eroded below the existing D3.0C minimum effective isolation horizon `50,000 generations`.

There is no merge probability and no `merge_rate/Myr`.

The reconnection check cadence is locked to the D3.2B fission cadence: **0.5 Myr**. The reconnection persistence horizon is locked to the D3.2B persistent-vicariance horizon: **2 Myr**. These are reuse locks, not new calibrations.

## Species irreversibility
Geographic reconnection is not de-speciation. Components belonging to different `current_species` are never coalesced, even if they overlap or exchange pressure later becomes large. A daughter species can therefore contact its parent without being silently deleted.

## Exact pooling
For a coalesced group with masses `N_i`, means `mu_i`, and within-deme variances `V_i`:

- population raster = exact sum of member rasters;
- pooled mean = `sum(N_i mu_i)/sum(N_i)`;
- pooled second moment = `sum[N_i (V_i + mu_i^2)]/sum(N_i)`;
- pooled variance = pooled second moment minus pooled mean squared.

The event records conservation errors for population, first moment and second moment. No clipping is allowed to fake moment conservation. If the exact pooled variance would violate the already-authorized hard normalized VA ceiling `q=0.05`, the merge is not materialized yet.

## Pair-state history
External RI and isolation-clock states are population-weighted onto the retained component identity. Internal pair states disappear because the bookkeeping demes no longer exist. Founder and vicariance persistence involving absorbed IDs are reset; the merged component must earn any later fission/speciation persistence again.

## Validation
210→206 Ma:
- 120 species;
- 15 fissions;
- 3 coalescences;
- 145 components = 133 + 15 − 3;
- 0 speciations/extinctions;
- no VA cap saturation.

210→205 Ma:
- 120 species;
- 18 fissions;
- 4 coalescences;
- 147 components = 133 + 18 − 4;
- 0 speciations/extinctions;
- no VA cap saturation.

## Scope boundary
R3.3 does **not** yet promote 150 Ma. The long 210→150 Ma H0 replay must be rerun locally with R3.3 and audited for component homeostasis, VA cap-contact, speciation robustness and ordinary extinction before continuation to 90 Ma is authorized.
