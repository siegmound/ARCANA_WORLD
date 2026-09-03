# v0.6D1-R3.7D — Directional-Selection Evidence Closure & Adaptive Shadow Runtime Binding

## Scope
R3.7D closes the repaired R3.7C-R1 NEMO directional-selection evidence and defines a non-canonical adaptive-selection shadow binding. It does **not** change `mu`, `b`, `q*`, the VA ceiling, migration, RI/speciation, paleogeography, climate, or the production R3.5 runtime.

## Evidence authority
The accepted parent evidence is the full R3.7C-R1 oracle: 16/16 chains complete, 16/16 selection-efficacy gates PASS, 80 NEMO 2.4.2 executions expected/completed.

## Inference correction
The parent diagnostic used

`K = (Delta z)^2 / (2 * (S_selected - S_neutral))`.

Because `S` is quadratic in allele-frequency contrast, `S_selected-S_neutral` contains a neutral/adaptive cross term. It is not the squared distance of the matched adaptive displacement and can yield apparent `K > L`.

R3.7D therefore constructs the matched adaptive allele-frequency contrast first:

`Delta p_adapt = contrast(p_selected) - contrast(p_neutral)`

then

`S_adapt = 2 * sum_l a_l^2 * Delta p_adapt,l^2`

and

`K_selection = (Delta z_adapt)^2 / (2 S_adapt)`.

This is the geometry consumed by the R3.7A adaptive coordinate and obeys the Cauchy bound `K_selection <= L`.

## Result
Across all 16 chains geometric `K_selection` is finite and <=64, but strongly finite-N sensitive. At N=2000 the eight observations are tightly grouped (~37.61–41.00; median ~38.47; CV ~2.85%). At N=500 the estimator is much noisier/lower. Since ARCANA WorldSim population units are not literal NEMO individuals, no direct N mapping is authorized.

The R3.7A standing-divergence QTL participation scale (~46.65–63.5; median ~59.62) is retained as a different semantic quantity. R3.7D therefore rejects one universal scalar K for both standing divergence and incremental adaptive response.

## Shadow binding
Only the N=2000 dynamic-selection envelope is authorized for **shadow sensitivity**:
- low: evidence minimum;
- center: evidence median;
- high: evidence maximum.

The ARCANA selection operator remains authoritative for `Delta z`; R3.7D only maps that already-authorized response into the adaptive latent coordinate. All outputs are non-canonical.

## Governance
- scalar production `K_eff`: NOT AUTHORIZED
- direct WorldSim-N to NEMO-N mapping: NOT AUTHORIZED
- high-N K envelope: SHADOW ONLY
- production runtime replacement: NOT AUTHORIZED
- canonical write: DENIED
