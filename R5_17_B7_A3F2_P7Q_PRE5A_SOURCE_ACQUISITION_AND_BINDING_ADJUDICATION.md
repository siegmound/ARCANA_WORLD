# R5.17-B7-A3F2-P7Q-PRE5-A

## Exact source acquisition manifest and version-binding gate

PRE5-A binds metadata only for GUM v1.0, GLiM v1.0, ORNL DAAC 1304/Pelletier and optional SoilGrids 2.0. Scientific payloads remain `NOT_ACQUIRED`; no provider runtime, simulation, reprojection or materialization occurred.

GUM is locked to DOI `10.1594/PANGAEA.884822` and its official 1.3 GB archive is excluded from this stage. GLiM is locked to DOI `10.1594/PANGAEA.788537`. Pelletier is locked to publication DOI `10.1002/2015MS000526` and dataset DOI `10.3334/ORNLDAAC/1304`; the catalog reports about 900.795 MB. SoilGrids remains optional modern endpoint calibration, 250 m, six depth intervals, CC-BY 4.0; ISRIC currently reports REST API unavailability and points to stable alternatives.

The future PRE5-B sample is deterministic and coverage-oriented, limited to 100 MB total. Raw payloads and caches are Git-excluded. Residual/bedrock classification, texture transformation, profile initialization and missing cryosphere/wind/volcanism drivers remain blockers. P7Q remains suspended.

**Decision:** `AUTHORIZE_P7Q_PRE5B_BOUNDED_SOURCE_SAMPLE_ACQUISITION_GATE`  
**Verdict:** `PASS_P7Q_PRE5A_SOURCE_ACQUISITION_AND_BINDING_ADJUDICATED`
