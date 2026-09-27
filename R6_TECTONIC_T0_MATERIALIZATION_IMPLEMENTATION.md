# R6 B_PANGAEA_LIKE_LATE_TRIASSIC_v2 materialization

**Decision:** `R6_T0_B_PANGAEA_LIKE_V2_MATERIALIZED__SPECIALIST_RUNTIME_REMAINS`

The existing canonical geography passed the ratified macrostate check: the largest land component contains 89.9876% of land, crosses the equator over 98° of latitude, and the global ocean is one connected component. The previous mandatory-embayment blocker is superseded by v2.

The deterministic candidate field package is `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz` (SHA-256 `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e`). The realization manifest records each normalized field hash and canonical parent identity.

Crust-domain cell counts: `{"EXTENDED_CONTINENTAL": 1266, "NORMAL_CONTINENTAL": 4723, "NORMAL_OCEANIC": 50542, "OROGENIC_THICKENED": 401, "STABLE_CONTINENTAL": 7834, "TRANSITIONAL_MARGIN": 34}`.
Continental thermal area fractions: `{"COLD_STABLE": 0.5500702980512214, "HOT_EXTENDED": 0.10002050378164219, "NORMAL": 0.3499091981671366}`.
Ocean-age area-weighted median: 70 Ma; selected source branch `R6BR-DERIVED-50911691f2df2e592ca4`.
Ocean residual mean/RMS/cap: -1.4105804e-11 m / 500 m / 1200 m.

## Pending specialist output

- ocean thermal profile and age-derived heat flow
- ocean thermal lithosphere thickness
- thermal/isostatic ocean bathymetry component and complete ocean surface
- continental geotherm profiles and model-derived heat flow beyond ratified references
- chemical density anomaly
- cooling curvature

The age-derived cooling/isostatic model and OrbData5 are not selected/version-pinned. Total ocean elevation and ocean heat flow remain unknown. No PRE_ORBDATA FEG was written because its global elevation and heat-flow fields cannot be completed without those values. SHELLS_READY is also unavailable.

The runtime manifest is an incomplete candidate copied from the governed template; it does not authorize execution. Reference parameter configuration has only canonical radius/gravity values; rheology remains unselected. ShellSet mechanics and forward evolution were not run. No `dt` or t1 was created.
