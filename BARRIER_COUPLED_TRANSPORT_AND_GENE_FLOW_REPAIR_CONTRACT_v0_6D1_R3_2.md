# v0.6D1-R3.2 — Barrier-Coupled Transport & Gene-Flow Repair Contract

## Purpose
Repair the R3/R3.1 mismatch in which D3.2C/D3.2B barrier permeability governed vicariance/fission but did not govern migration and pairwise contact/gene flow in the rebased runtime.

## Reuse-first authority
R3.2 reuses the surviving SEALED D3.2B `diversification_adequacy` implementation. The source hash is `9c2338cd8904bd6f9972c253be375384f6ec57193b4e3f5acf404f1ef2f344b2`. No custom vectorized migration implementation is retained.

The same reconstructed permeability field now enters:
1. D3.2B migration with permeability;
2. D3.2B permeability-masked pair/contact/gene-flow metrics;
3. D3.2B/D3.2C effective connectivity for persistent vicariance and deme fission.

The R3.1 D3.3A variance repair is retained: gene-flow moment mixing occurs before Riccati homeostasis, with `maximum_total_exchange_fraction_per_deme = 0.45`; homeostasis is the final within-step VA operator.

## Semantic locks
- `deme_fission != speciation`;
- no global speciation/extinction rate;
- no Deep biological coupling in H0;
- initial R1 fragmentation remains grandfathered/event-driven;
- no new threshold is introduced by R3.2.

## Short validation
210→206 Ma: 120 species, 148 components, 15 fissions, 0 births, 0 ordinary extinctions.
210→205 Ma: 120 species, 151 components, 18 fissions, 0 births, 0 ordinary extinctions. At 205 Ma normalized VA max is ~0.01575 and no reservoir is at ≥99% of the 0.05 hard ceiling.

## Scope
This stage validates the repair and prepares the long 210→150 Ma rerun. The 150 Ma checkpoint is not promoted until that local production rerun passes the same VA/fission/speciation audits.
