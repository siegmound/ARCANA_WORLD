# R6 Initial World Multiscale Refinement Validation

- Decision: `LATENT_GEOMETRY_COMPATIBLE__MULTISCALE_TECHNICAL_REFINEMENT_VALIDATED`
- Verdict: `PASS_WITH_COARSE_SUPPORT_FIELDS_AND_PROCEDURAL_DETAIL_LIMITATIONS`
- Canonical payload SHA-256: `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`; byte-identical identity verified.
- 1° global grid unchanged; no dense global fine raster materialized.
- Fine land/coast and relief are deterministic procedural detail constrained to the canonical 1° parent state.
- Province/plate/crust/boundary remain `COARSE_SUPPORT_ON_FINE_GRID`; UNKNOWN domains remain UNKNOWN.
- Slope, local-minimum/basin-potential, coastal-cell and checkerboard diagnostics are technical only; no drainage network is created.
- No scientific forward simulation or empirical authority increase.

## Region diagnostics

| Type | Bounds (south, west, north, east) |
|---|---|
| coastline | [-73.0, -58.0, -69.0, -54.0] |
| continental_interior | [35.0, -82.0, 39.0, -78.0] |
| province_boundary | [-13.0, -76.0, -9.0, -72.0] |
| topographic_transition | [8.0, -52.0, 12.0, -48.0] |

## Resolution/performance

| Region | Resolution | Cells | Seconds | Peak tracked Python bytes | Fine-detail RMS (m) | Parent error (m) |
|---|---:|---:|---:|---:|---:|---:|
| coastline | 1.0° | 16 | 0.011405 | 115711 | 0.0000 | 0.00000000 |
| coastline | 0.25° | 256 | 2.181789 | 945837 | 3.9225 | 0.00001701 |
| coastline | 0.1° | 1600 | 3.834934 | 370826 | 3.8181 | 0.00000897 |
| continental_interior | 1.0° | 16 | 0.009896 | 108416 | 0.0000 | 0.00000000 |
| continental_interior | 0.25° | 256 | 1.759285 | 217538 | 3.7602 | 0.00001492 |
| continental_interior | 0.1° | 1600 | 3.326059 | 331550 | 3.8269 | 0.00000818 |
| province_boundary | 1.0° | 16 | 0.010138 | 105316 | 0.0000 | 0.00000000 |
| province_boundary | 0.25° | 256 | 1.748819 | 217590 | 3.9208 | 0.00003602 |
| province_boundary | 0.1° | 1600 | 3.298298 | 331602 | 3.8942 | 0.00001080 |
| topographic_transition | 1.0° | 16 | 0.010027 | 105316 | 0.0000 | 0.00000000 |
| topographic_transition | 0.25° | 256 | 1.751157 | 217694 | 4.1355 | 0.00003224 |
| topographic_transition | 0.1° | 1600 | 3.349100 | 331650 | 3.8687 | 0.00001571 |

## Tile/order and governance

- Independent tiles equal union: `True` at 0.25° and 0.1°.
- Repeat/order-independent hashes: `True`.
- Parent mean tolerance: `0.05` m.
- Causal evolution readiness: `false`; required plate-motion/geodynamic law and dated forcing remain unbound.
