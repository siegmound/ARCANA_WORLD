# v0.6D1-R1 — World 1 210 Ma Canonical Biological Rebaseline & Paired H0/HX Replay Initialization

## Status

`PASS_210MA_CANONICAL_REBASELINE_AND_PAIRED_H0_HX_INITIALIZATION_CANDIDATE`

This stage is a **new deterministic rebaseline**, not a byte reconstruction of the lost D1/D2 historical state.

## 1. Authority hierarchy

- `v0.3.18 AUTHORIAL GOVERNANCE SEALED` remains the authorial governance authority.
- World 1 physical/spatial and A1 fauna state remain inherited environmental authorities.
- The surviving D1 metadata provide the exact 120 ancestral species identity/trait surface.
- D3.3A provides the final long-horizon additive-variance homeostasis calibration.
- Deep v0.5 provides the 210 Ma physical free-energy field.
- Photo-Deep 5% additive on E/th is inherited from the accepted v0.5.1 candidate.
- R0 remains historical-recovery evidence only; R1 does not claim lost-history identity.

## 2. Why rebaseline

The executable 210→66 Ma D1/D2 runtime and RAW population trajectory were not recovered. The surviving runpack does, however, contain:

1. the exact 120 D1 species metadata;
2. the A1 210 Ma guild-level population and carrying-capacity rasters;
3. World 1 land, plate, temperature, aridity and forage fields at 210 Ma;
4. the final Deep physical field at 210 Ma.

R1 therefore creates a new canonical **species-level resolution of the surviving A1 state** while exactly preserving all A1 guild-level population/capacity values.

## 3. Species allocation kernel

For D1 species `i` in guild `g` and cell `c`, define a non-negative score

\[
S_{i,c}=H_{i,c}\,R_{i,c}\,P_{i,c}.
\]

`H` is the product of the D1 thermal and aridity Gaussian niche responses:

\[
H_{i,c}=\exp\left[-\frac12\left(z_T^2+z_A^2\right)\right].
\]

`R` is a compact Gaussian around the D1 range centre:

\[
R_{i,c}=\exp\left[-\frac12(d_{i,c}/r_i)^2\right],
\quad d_{i,c}\le3.25r_i,
\]

and zero outside that support. The distance conversion uses a `6371.0088 km` **D1 metadata compatibility metric**, not a newly sealed World 1 planetary-radius constant.

`P` is a deterministic spatial patch modulation constructed only from the existing D1 patch amplitude, wave numbers and phases. It is bounded below by `0.05`.

No random draw is used in the allocation.

## 4. Exact A1 conservation

Within each guild and cell:

\[
f_{i,c}=\frac{S_{i,c}}{\sum_{j\in g}S_{j,c}}.
\]

Then

\[
N_{i,c}=f_{i,c}N^{A1}_{g,c},
\qquad
K_{i,c}=f_{i,c}K^{A1}_{g,c}.
\]

Therefore, by construction,

\[
\sum_{i\in g}N_{i,c}=N^{A1}_{g,c},
\qquad
\sum_{i\in g}K_{i,c}=K^{A1}_{g,c}.
\]

Using the **same fraction for N and K** avoids introducing an arbitrary initial within-guild difference in local `N/K`.

No equal species abundance is assumed and no old D2 species raster is reconstructed.

## 5. D1 identity constraints

Exactly 120 initial effective species are retained, with guild counts:

- guild 1: 24;
- guild 2: 16;
- guild 3: 20;
- guild 4: 24;
- guild 5: 24;
- guild 6: 12.

`HSG_025` is **not** an initial species; it may only re-emerge later through an independently authorized evolutionary event.

No species is pre-labelled Deep-adapted.

## 6. Deep hereditary state at 210 Ma

All latent means begin neutral:

\[
\mathbf Z_X(210\,Ma)=0.
\]

Standing additive variance is not chosen arbitrarily. The final D3.3A zero-selection Riccati homeostasis has

\[
\frac{dq}{dt}=\mu-bq^2,
\]

with

\[
\mu=0.002/Myr,\qquad b=0.9876543209876544/Myr/q.
\]

Hence

\[
q^*=\sqrt{\mu/b}=0.045.
\]

R1 therefore initializes

\[
V^X_{A,i,k}=0.045
\]

for every ancestral species and all ten Deep latent dimensions.

Acclimatization, remodeling, recoverable load and injury all start at zero.

This avoids both a directional adaptation prior and an artificial early-time creation of standing Deep variance.

## 7. Physical Deep state

The v0.5 210 Ma Deep field is retained. Photo-Deep is additive and physical in **both** counterfactual branches:

\[
u^\odot_E=0.05u_E,
\qquad
u^\odot_{th}=0.05u_{th},
\]

with

\[
u^\odot_p=u^\odot_I=u^\odot_N=0.
\]

The initial ordinary biological population is fully in the negligible Deep-exposure regime even with this 5% contribution. Thus HX does not begin with a forced Deep-selected lineage.

## 8. Paired H0/HX initialization

There is one common-state artifact with one semantic fingerprint. Both branches reference it.

### H0

`deep_biological_coupling_enabled = false`

### HX

`deep_biological_coupling_enabled = true`

Everything else is identical at the branch point, including:

- species IDs;
- population raster;
- carrying capacity;
- ordinary traits;
- environment;
- physical Deep field;
- photo-Deep field;
- latent means and variances;
- physiological state;
- RNG base seed `917231`.

The only authorized manifest differences are:

1. `branch_id`;
2. `counterfactual_role`;
3. `deep_biological_coupling_enabled`.

## 9. Paired stochastic policy

The shared base seed is necessary but not sufficient after H0 and HX diverge. R2+ must use **event-keyed common random numbers**, keyed by stable causal identifiers such as event type, lineage ID, absolute time/cadence and spatial key. Sequential draw-order coupling is forbidden because a Deep-induced extra event in HX would otherwise desynchronize every later random draw.

## 10. Numerical closure

Materialized R1 values:

- 120 species;
- global population: `1823.1595076876783` WorldSim units;
- global carrying capacity: `3086.040882769972`;
- max cell population closure error: `2.220446049250313e-16`;
- max cell capacity closure error: `2.7755575615628914e-16`;
- non-land population cells: `0`;
- `N > K` violations: `0`;
- initial population-weighted Deep load: `4.9411409914759124e-05`;
- population in negligible Deep regime: `100%`;
- tolerance exceeded: `0%`;
- injury: `0%`.

## 11. Sensitivity of D1 range compatibility metric

Changing the compatibility radius by ±5% changes species global totals only modestly while exact A1 conservation remains guaranteed:

- median relative species-total change: ~0.9–1.0%;
- 90th percentile: ~2.1–2.3%;
- maximum: <4.2%.

Thus the rebaseline is not fragile to this compatibility parameter.

## 12. Explicit non-claims

R1 does **not** claim:

- byte identity with lost D1/D2;
- recovery of the old 210 Ma species raster;
- recovery of old D2 events;
- that `HSG_003 → HSG_025` must recur;
- that the old 31 CHA-1 survivors must recur;
- that the new rebaseline is already authorially sealed.

Old D2/D2.2 outputs become **validation oracles/envelopes**, not forced targets.

## 13. Next stage

`v0.6D1-R2 — Rebased Natural-Control Deep-Time Runtime & 210→180 Ma Pilot`

R2 must evolve the new 120-species raster under Deep biology OFF first, using modern causal operators and preserving RAW-FIRST output, absolute cadence, checkpoint/restart and event-keyed RNG. Only after H0-R2 passes plausibility/convergence may the paired HX pilot be run from the exact same R1 common state.
