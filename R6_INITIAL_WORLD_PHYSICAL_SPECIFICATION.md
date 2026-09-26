# R6 Initial World Physical Specification

**Status:** Frozen as a new authorial design contract; no world state has been generated.
**Inspected baseline:** `main` / `origin/main` at `592b1651b405363373590092e133bd25569d99a5`.

## Decision and provenance boundary

R6 starts at **210 Ma** as a new canonical design decision, not as a recovered fact about the missing formal Simulation1 bootstrap. The recovery adjudication found an early v0.1 HYBRID-1 prototype with schematic Pangea geometry at 210 Ma, but no authenticated link from that prototype to Simulation1 or to the A1 payload producer/consumer. A1 is a mixed reference bundle on a 2° grid; it is not an initializer. Its land mask/plate codes do not provide topography, plate-motion physics, or a complete physical state. The old HYBRID-1 seed and hard-coded geometry are not inherited.

The design consequently describes an **Earth-scale, rocky, ocean-bearing analogue with a Pangaea-inspired supercontinent**, not a literal reconstruction of Earth at 210 Ma. Values generated from the new contract must be labeled authorial synthetic initial conditions, with uncertainty and provenance. No R5 state or runtime is required.

## Frozen baseline choices

| Choice | R6 design | Boundary |
|---|---|---|
| Global t0 | 210 Ma | New R6 design, not historical Sim1 proof |
| Planet | Spherical Earth-scale rocky world; radius 6,371,000 m; nominal surface gravity 9.82 m/s²; sidereal day 86,164.1 s; fixed nominal tilt 23.4°; 1 AU circular reference orbit | Earth-analogue design constants, not 210 Ma Earth reconstructions; variable forcing remains unbound |
| Base geography grid | 1° regular lon/lat, 180×360 = 64,800 cells; lat centers −89.5°…+89.5° ascending; lon centers −179.5°…+179.5° ascending and periodic | New R6 canonical grid; spherical area varies by latitude; no source upsampling |
| Land/ocean | Land area fraction 0.25–0.35; ocean complement 0.65–0.75 | Authorial morphology envelope, not inferred from A1 |
| Supercontinent | Dominant connected component holds 0.80–0.95 of land; crosses equator; area-weighted centroid latitude within ±15°; at least 120° longitude and 60° latitude span | “Pangaea-inspired” topology, not empirical fit |
| Plate/craton design | 12–18 plates and 4–8 continental cratonic blocks as generator parameter ranges | Must pass an implementation benchmark; no t0 motion vector is assigned without a governed law |
| Sea datum | Authorial equipotential reference z=0 m | Ocean volume/eustatic sea level are not bound; mask does not imply bathymetry |
| Seed | New named SHA-256-derived R6 seed lineage and independent named PCG64 streams | Not copied from HYBRID-1; exact runtime version captured at later execution |
| Evolution | Forward, process-led from 210 Ma | No temporal interpolation, backcasting, endpoint fitting, or arbitrary persistence |

The radius, gravity, rotation and tilt are rounded Earth-analogue reference values; NASA’s Earth fact sheet and Earth facts are contextual references, not authority for an R6 paleo-planet. NASA’s Milankovitch discussion specifically describes tilt as time-varying, so the fixed 23.4° here is a nominal design constant and must not be described as 210 Ma Earth obliquity. Sources: [NASA/NSSDC Earth Fact Sheet](https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html), [NASA Earth Facts](https://science.nasa.gov/earth/facts/), [NASA Milankovitch Cycles](https://science.nasa.gov/science-research/earth-science/milankovitch-orbital-cycles-and-their-role-in-earths-climate/).

## Physical field semantics

The initial-world materializer may create the land/ocean mask, categorical crust/plate/province fields, and uncertainty-bearing land elevation as a **designed synthetic t0 state**. Numeric land elevations are bounded to 0–8,000 m relative to the datum and must use a versioned, multiscale hypsometric/tectonic morphology method. These values are not recovered observations. Plate identities and boundary classes do not imply plate velocities; plate motion stays `UNKNOWN` until the R6 kinematic/geodynamic law is separately bound. Oceanic mask cells do not receive invented bathymetric depths. Bathymetry, ocean volume, and eustatic history remain UNKNOWN pending an authorized ocean-basin model/source.

No lithology, regolith, soil, physical parent material, or P7Q reopening is included. No climate, hydrology, Deep, vegetation, fauna, marine ecology, human population, or resource state is materialized at t0 by this contract. Climate forcing and atmospheric composition require separate authority. Hydrology must wait for a valid compatible terrain/climate/water boundary and its R6 adapter. `DEEP_HISTORY` remains first-class in R6 architecture, but its 210 Ma initializer and fundamental laws are not recovered: v0.5 calibration is only reference/calibration evidence, and the v0.6D bridge still lists missing D1/D2 runtime/state and related production inputs. Deep is UNKNOWN, not zero.

## Causal/evolution policy

The first post-t0 consumer is the **R6 physical-world evolution adapter** for tectonic/geodynamic state and terrain evolution. It is not registered or authorized yet. It must obtain physical laws, plate-motion/forcing authority, compatible runtime, and required Deep/other coupled inputs before a scientific run. Climate and hydrology follow only through their own bound adapters and an explicitly versioned coupling/timestep contract. A1 and R1–R3 frames may serve as declared comparison/reference evidence only; they are not endpoints to force-match. A governed endpoint can validate a matching field/support at its time but cannot authorize interpolation or retroactive adjustment.

R6’s frozen architecture requires causal state, authority and uncertainty to remain explicit; authority anchors are not checkpoints or instructions to interpolate. UNKNOWN propagates without zero-fill, inference-by-absence, or convenient defaults.

## What is still unresolved

`NEEDS_EXTERNAL_SCIENTIFIC_BINDING`: plate-motion/geodynamic laws and dated forcings; bathymetry/ocean basin if a consumer requires it; Deep laws and initial state; age-specific solar/orbital/atmospheric forcing and climate authority; ocean volume/sea-level coupling; applicable dated land/shoreline/event authority.

`NEEDS_IMPLEMENTATION_BENCHMARK`: spherical plate mosaic and supercontinent generator; elevation hypsometry/relief spectra; drainage readiness; spherical grid seam/pole/connectivity and area invariants; deterministic runtime and memory on the target workstation.

`NEEDS_PROVIDER`: none selected. Evaluate providers only when a specific consumer need remains unsupported by canonical ARCANA evidence, using the repository’s scientific-engine suitability order.

## Non-authorization

This document and its paired contracts specify a design only. They do not execute a generator, physical evolution, Deep, climate, hydrology, provider, or any later biological/resource stage. They do not update `ARCANA_WORLD_CURRENT_STATE.md`, the authority register, or execution indexes. No staging, commit, or push is authorized.
