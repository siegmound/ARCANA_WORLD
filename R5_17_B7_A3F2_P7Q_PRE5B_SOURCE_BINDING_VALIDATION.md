# R5.17-B7-A3F2-P7Q-PRE5-B

## Real source acquisition and source-binding validation

GLiM v1.0 and GUM v1.0 were acquired from official PANGAEA endpoints into a sibling cache outside Git. GLiM is 38,670 bytes with SHA256 `43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e`. GUM is 1,436,982,491 bytes with SHA256 `6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63`.

The real payload checks passed: archive inspection, format/schema parsing, CRS, extent/resolution and nodata. GUM exposes 911,551 DBF records and a WGS84 shapefile; its 0.5-degree grid uses `-9999`. GLiM exposes a 720×360 0.5-degree ASCII grid and class table. GUM polygon absence and nodata remain UNKNOWN/OUTSIDE_SOURCE_COVERAGE and never become bedrock.

Pelletier/ORNL 1304 was intentionally not acquired because the two real providers were sufficient for the bounded binding proof. SoilGrids remains optional and was skipped. No ARCANA parent-state records, arrays, temporal rules, soil, texture or simulation were created.

Pipeline maturity is `L1_SOURCE_BOUND_PARTIAL`. Residual/bedrock classifier, texture transform, profile contract, cryosphere, wind and volcanism remain unresolved.

**Decision:** `AUTHORIZE_P7Q_PRE5C_STATIC_SOURCE_BINDING_PROTOTYPE_WITH_PARTIAL_PROVIDER_COVERAGE`  
**Verdict:** `PASS_P7Q_PRE5B_REAL_SOURCE_ACQUISITION_AND_BINDING_VALIDATED`
