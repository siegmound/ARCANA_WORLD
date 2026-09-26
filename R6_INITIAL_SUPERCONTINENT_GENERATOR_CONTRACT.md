# R6 Initial Supercontinent Generator Contract

**Status:** Design contract only; neither implementation nor generation is authorized here.
**Parent:** [R6 initial-world physical specification](R6_INITIAL_WORLD_PHYSICAL_SPECIFICATION.md).

## Decision

Use a **minimum custom ARCANA generator** solely for a new, designed physical-geography state at exactly 210 Ma. Existing ARCANA material does not supply this quantity: A1 is mixed reference data (not an initializer), while v0.1 HYBRID-1 is a hard-coded schematic prototype without a governed source/rotation model or Simulation1 identity. No external engine is selected or acquired. The scientific-engine suitability order is recorded in the JSON contract; another engine should be evaluated only if a later concrete requirement outgrows this bounded custom generator.

## Generator shape

The intended algorithm is a deterministic spherical plate mosaic with clustered continental cratonic blocks, a dominant connected supercontinent, explicitly represented designed sutures/orogenic/rift provinces, a multiscale irregular coastline, and bounded land relief. The frozen morphology envelope and grid are in the paired machine-readable contract. A sea-level threshold can satisfy the authorial land-area/connectivity envelope, but it is **not** a solution to ocean mass, eustasy, or paleosea level.

The generator must preserve categorical and continuous fields separately, carry support/authority/uncertainty/provenance for every field, and identify every numeric elevation as `AUTHORIAL_SYNTHETIC_INITIALIZATION`. Plate identities and boundary classes are not motion vectors: motion remains UNKNOWN pending a separately authorized kinematic/geodynamic law. Likewise ocean cells get no fabricated bathymetry. No A1/R1/R3 raster is resampled or used as a numeric target.

## Seed, runtime, and output

Use the new named R6 SHA-256 seed lineage specified in JSON, with independent named NumPy PCG64 streams. Record the exact runtime and library identity at materialization. The v0.1 seed 917231 is explicitly not inherited. Generate only a single 210 Ma initial state; no later frames, climate, hydrology, Deep, soil, biology, resource state, or trajectory are in scope.

Place large arrays outside ordinary Git, hash-register them, and promote only after complete validation to an immutable run identity. Never overwrite an existing materialization. Initial implementation benchmarks cover spherical geometry and seam/pole handling, morphology, area weights, elevation bounds/spectra, determinism, and the stated workstation memory/runtime envelope.

## Evolution boundary

The first post-t0 causal consumer is the R6 physical-world evolution adapter. It does not yet exist as a registered, law-bound, benchmarked executable. Forward tectonic/terrain evolution must not run until its process laws, forcing/event chronology, runtime, required Deep inputs and cross-domain coupling are separately bound. Hard endpoints may validate only matching support; they may not be interpolated, backcast, or forcibly fitted. This contract creates no PRE5/HRAB micro-gates and does not reopen P7Q.
