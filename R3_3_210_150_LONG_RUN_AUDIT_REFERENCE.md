# v0.6D1-R3.3 — 210→150 Ma Long-Run Audit

Status: `FAIL_FOR_CONTINUATION__DEME_COALESCENCE_WORKS_BUT_LONG_HORIZON_VA_CAP_ATTRACTOR_PERSISTS`

## Endpoint

- Population: `1940.114981733686`
- A1 150 Ma reference: `1940.594970703125`
- Relative population error: about `-0.02473%`
- Species: `135`
- Components: `460`
- Events: `340` deme fissions, `13` deme coalescences, `15` speciations, `0` ordinary extinctions, `432` support-loss remaps.

The deme ledger closes exactly:

`133 + 340 - 13 = 460`.

R3.3 therefore fixes the missing bidirectional deme lifecycle. It does **not** yet establish long-horizon fragmentation homeostasis.

## Normalized additive variance

Using the D3.3A trait scales and `q = VA / scale^2`:

- max q: `0.05`
- reservoirs above hard ceiling: `0`
- reservoirs at >=99% ceiling: `183 / 1380 = 13.2609%`
- thermal: `27.1739%`
- aridity: `12.6087%`
- body mass: `0%`
- median q: `0.0447990`

This remains incompatible with the D3.3A long-horizon calibration, whose final >=99%-ceiling fraction was 0% and whose maximum transient climate cap-contact was about 1.60%.

The root-lineage fission count remains correlated with cap contact (`r ≈ 0.547`), so the structured/admixture regime is the dominant new stressor.

## Coalescence effect

R3.3 reduces component accumulation and improves the micro-deme tail:

- `<0.001`: 6 components
- `<0.01`: 8
- `<0.05`: 97, carrying only `2.2064` WorldSim population units
- `<0.1`: 123

Of the 13 coalescences, 7 are numerical-dust-scale and 6 are population-significant (>0.1 units). The last coalescence occurs at 158.5 Ma.

However, compared with R3.2:

- all 15 speciation identities and ages are unchanged;
- 339/340 fissions are identical;
- the remaining fission differs only by 0.5 Myr.

Thus coalescence is physically useful but is not the mechanism that resolves the VA cap-attractor.

## Speciation

All 15 births pass the existing governed gates. Their minimum trait-distance margin above the `1.0` threshold is about `+0.01023`; 4/15 are within `+0.05`, and 9/15 within `+0.10`.

Because the VA dynamics are still cap-limited, these births remain diagnostic rather than canonical.

## Decision

The 150 Ma state is **not authorized for 150→90 Ma continuation**.

Do not add more deme-merger heuristics. R3.3 already proves the merge lifecycle works. The next stage should hold the spatial/deme machinery fixed and determine whether the D3.3A hard ceiling lacks headroom under the much more structured rebased history, or whether the homeostatic turnover must be recalibrated under sustained admixture.

Recommended next stage:

`v0.6D1-R3.4 — Long-Horizon Admixture-Variance Headroom Audit & Homeostasis Calibration`

R3.4 should first perform ceiling/headroom sensitivity without changing the authorized model, then alter a calibration coefficient only if the unclipped dynamics demonstrate that the current `q=0.05` ceiling is acting as an artificial authority.
