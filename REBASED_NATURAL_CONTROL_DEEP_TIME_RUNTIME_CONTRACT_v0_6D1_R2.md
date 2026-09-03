# Rebased Natural-Control Deep-Time Runtime Contract — v0.6D1-R2

## Purpose

Evolve the common 210 Ma R1 state to 180 Ma with biological Deep coupling OFF, using modern D3-derived semantics rather than reconstructing the lost D2 solver.

## State authority

Initial state is exactly the R1 common state. H0 does not regenerate the 120 species or their 210 Ma spatial population. The environment uses the A1 210 and 180 Ma authoritative frames included in this package.

## Environment

Continuous climate/forage fields are linearly continued between the two A1 endpoint states. Land/plate topology is not smoothly interpolated. It remains at the 210 Ma support until a discrete conservative transition at the candidate midpoint 195 Ma, then uses the 180 Ma support. Population that would otherwise fall on lost land is conservatively remapped to nearest valid land.

## Biological operators

Active: species-level demographic targets, habitat/resource routing, spatial migration, ecological trait response, D3.3A-style long-horizon additive-variance homeostasis, intra-lineage gene-flow moment mixing, isolation clocks, intrinsic RI accumulation/erosion, and deterministic persistent ordinary-extinction gate.

Forbidden: global/random extinction rate, global/random speciation rate, teleological ecospace recovery, direct Deep speciation, directional mutation.

## Speciation authority

R2 computes the quantities required by the D3 gate (isolation, RI, trait distance, effective exchange and component support) but does not yet materialize daughter species. In the validated H0 210→180 Ma pilot this is non-operative because no pair is speciation-ready. Any extension beyond this pilot must add the governed birth actuator before a ready pair can be crossed.

## Cadence

The accepted pilot cadence is 250 kyr. It is not a raster-resolution seal. Absolute check intervals remain 500 kyr for ordinary extinction/speciation diagnostics.

## Topology sensitivity

Moving the discrete support switch from 195 Ma to 192.5 or 197.5 Ma leaves richness at 120 and changes abundance-weighted species totals by only ~0.29% and ~0.21%, respectively. Therefore 195 Ma is a candidate midpoint, not a hidden macroevolution driver.
