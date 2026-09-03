# Next-stage handoff after v0.6D1-R3.7A

## Closed in R3.7A
The R3.7 segregation-aware state now has explicit lifecycle semantics without inventing hidden genomics.

### Initialization
At the 210 Ma common state, authoritative same-current-species pairs initialize at `S=0`. Cross-species entries are non-authoritative placeholders. This is a minimum-information prior, not a claim of literal genomic identity.

### Drift
R3.7A reuses the existing D3.3A drift authority exactly. If a deme loses expected within-deme genic variance `L_i = VA_i(1-R_i)`, pairwise neutral segregation potential increases by `L_i + L_j`. Parent NEMO B0 evidence supports this mapping without a new drift coefficient.

### Selection
Directional trait response is mapped to an adaptive genetic coordinate by `dh = dz/sqrt(2 K_eff)`. `K_eff` is an effective participation number. The current 64-QTL reference gives ~46.65–63.50 but no World-1 production value is sealed.

### Deme lifecycle
- fission: exact clone at the split instant;
- coalescence: population-weighted genetic barycenter with exact R3.7 genic pooling;
- speciation: reproductive identity changes, numerical genetic state does not reset;
- remap: pure support remap leaves genetic state unchanged;
- extinction/removal: corresponding state is deleted.

## Pending external evidence
Run the NEMO 2.4.2 B2 chain:

```powershell
.\run_v0_6D1_R3_7A_nemo_b2_wsl.ps1 `
  -Replicates 2 `
  -PopulationSizes 500,2000 `
  -LociPerTrait 64 `
  -ParallelChains 4
```

Expected default workload: 8 independent chains × 3 sequential phases = 24 NEMO executions.

Phases:
1. CONNECTED_BURNIN — 250 generations;
2. FRAGMENTED — 400 generations;
3. RECONNECTED — 550 generations.

Expected final suite status:
`NEMO_B2_EVIDENCE_COMPLETE_REVIEW_REQUIRED`.

Upload/compress `local_runs/v0_6D1_R3_7A_B2` after completion.

## Next decision stage
After B2 evidence, create a closure/review stage (natural name: `v0.6D1-R3.7B — Segregation-Potential Lifecycle Evidence Closure & Short Runtime Binding`). Only that stage may decide whether a production `K_eff`/mapping is sufficiently supported and whether to bind R3.7 into a short World-1 replay.

Do not change `mu`, `b`, `q*`, the VA ceiling, speciation authority, barriers, fission/coalescence, or paleogeography while closing B2.
