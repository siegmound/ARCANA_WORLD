# v0.6D1-R3.7I — Production Promotion Seal & Canonical Segregation-Aware Runtime

## Purpose
R3.7I is the final governance layer for promoting the R3.7 segregation-aware genetic state into the World-1 production runtime. It does **not** infer new physics and it cannot self-promote from smoke evidence. Promotion requires the complete R3.7H LOW/CENTER/HIGH 210→150 Ma closed-loop evidence.

## Fail-closed evidence gate
The promotion reviewer must observe exactly three R3.7H branch records and the R3.7H aggregate summary. Every branch must contain 480 biology steps, pass its closed-loop gate, remain finite, and have zero q=0.08 clipping contacts. The aggregate R3.7H `governed_closed_loop_pass` must be true.

Population, species, component and event-history differences across LOW/CENTER/HIGH are reported for review. R3.7I does not fit a new tolerance to those outputs and does not modify K merely to force agreement.

## Promoted runtime semantics
After a valid promotion seal exists, World-1 production variance semantics become:
- gene-flow persistent variance: R3.7 segregation-aware within-deme VA;
- coalescence persistent variance: R3.7A segregation-aware barycentric pooling;
- directional selection: unchanged R3.4 operator, now consuming the repaired within-deme VA in closed loop;
- nonflow variance: unchanged D3.3A mutation supply, selection depletion, drift and nonlinear homeostasis;
- fission, extinction, RI/speciation, demography, migration geometry and paleogeography: unchanged parent authority.

The legacy whole-trait second-moment variance pooling is retired as **production variance authority** for World 1. It may remain as a diagnostic/mean-transport closure oracle.

## K semantics
`K_CENTER = 38.470` may be sealed only as the nominal reduced-order coordinate reference used to map realized trait displacement into the adaptive coordinate. It is **not** promoted as a physical World-1 constant. `K_LOW = 37.614` and `K_HIGH = 41.002` remain release-validation uncertainty sentinels.

Therefore the seal distinguishes:
- `nominal_reduced_order_k_reference_authorized = true`;
- `scalar_k_physical_constant_authorized = false`.

## No parameter retuning
R3.7I does not authorize changes to:
- `mu = 0.002 / Myr`;
- `b = 0.9876543209876544 / Myr / q`;
- q ceiling = 0.08;
- migration/exchange cap;
- selection law;
- RI/speciation thresholds;
- paleogeography or lifecycle triggers.

## Explicit promotion approval
Even valid R3.7H evidence produces only a review PASS unless the promotion command is run with explicit approval. Only then is `PRODUCTION_PROMOTION_SEAL_v0_6D1_R3_7I.json` materialized. The canonical R3.7I runtime refuses to execute when that seal is absent or invalid.
