# v0.6D1-R3.7G — Production-Binding Readiness & 210→150 Validation Contract

## Purpose
R3.7F reproduced the historical R3.5 q=0.08 clipping failure while the segregation-aware R3.7 shadow state remained below the existing ceiling for all three R3.7D K-envelope sentinels. R3.7G therefore moves from stress-window diagnosis to a governed **210→150 Ma validation replay**.

This stage does **not** yet replace the production runtime and does not write canonical genetic state.

## Validation window
- start: 210 Ma
- end: 150 Ma
- biology cadence: 125 kyr
- expected biology steps: 480

The interval is intentionally the same long-horizon window used by the earlier R3/R3.5 audits, so the legacy and repaired formulations are compared on the same historical target rather than on a newly selected favorable interval.

## K-envelope semantics
R3.7D high-N reference envelope:
- `K_LOW = 37.614` — low uncertainty sentinel
- `K_CENTER = 38.470` — nominal validation branch only
- `K_HIGH = 41.002` — high uncertainty sentinel

`K_CENTER` is **not** promoted to a World-1 constant. LOW/HIGH remain mandatory during the validation replay. No direct mapping between WorldSim population units and NEMO individual N is authorized.

## Pass gate
The governed 210→150 replay may pass only if:
1. exactly 480 biology steps are observed;
2. shadow instrumentation preserves bit-exact R3.5/R3.4 canonical arrays, identity lists and event history;
3. the legacy R3.5 clipping failure is reproduced;
4. every segregation-aware K branch remains below the existing q=0.08 ceiling with zero clipping contacts;
5. the nominal K_CENTER branch retains strictly positive headroom to the existing ceiling;
6. LOW/CENTER/HIGH do not diverge qualitatively in ceiling-contact state.

No new fitted tolerance is imposed on S, ancestry covariance, h, event counts or speciation. Their K-envelope spreads are reported quantitatively for review.

## Frozen authority
R3.7G does not change:
- D3.3A mutation supply `mu = 0.002 / Myr`;
- nonlinear variance depletion `b = 0.9876543209876544`;
- normalized VA ceiling `q = 0.08`;
- biology cadence 125 kyr / transport cadence 62.5 kyr;
- R3.4 migration, species-bound exchange and aggregate cap;
- R3.2C/R3.3 fission/coalescence and paleogeographic authority;
- speciation/RI gates;
- trait selection response.

## Governance
Until the full R3.7G run passes and is reviewed:
- `canonical_write_allowed = false`
- `production_runtime_replacement_authorized = false`
- `scalar_K_eff_production_authorized = false`
- `mu_b_or_ceiling_change_authorized = false`

A PASS authorizes only the next **production promotion review**, not automatic replacement of R3.5.
