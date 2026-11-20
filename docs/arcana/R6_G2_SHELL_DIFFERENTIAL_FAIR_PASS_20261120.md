# R6 FAIR matched shell gap differential kinematics: 107/107 PASS, four sampled sign brackets

Date: 2026-11-20. Exact source commit: `8a7a116a1ba0f1a045146120ed3c68d23b70dfe6`. FAIR operator terminal shows `107 passed in 0.80s`, `PYTEST_EXIT_CODE=0`, `DRIVER_EXIT_CODE=0`, manifest schema `ARCANA_R6_SHELL_DIFFERENTIAL_KINEMATICS_MANIFEST_V1`, status `PASS_SOURCE_SHELL_DIFFERENTIAL_KINEMATICS_AND_TRIPLE_AUDIT__SOLID_CONTACT_OPEN`. Manifest records `REPORT.json` SHA256 `29ce93ffed7dae94be7cff16f92b3bb8a4f82020140a2adc0d6056270f38c1d5`. **The raw REPORT bytes have not yet been independently SHA-checked on FAIR after the run**; the reported digest is from its manifest.

The driver sampled 41 original-source model-time checkpoints at 25-year spacing (0..1000), preserving original 8×8 (12 original boundary edges, 13 links) and 16×16 (36 edges, 39 links, triple node 34587) FE ownership and prior shell signed-gap parity.

- 8×8: 12 initial T0-zero departures, 0 subsequent definite sign-switch brackets and 0 ambiguous brackets. Source checkpoint instantaneous `gdot` min/max (m/model-year): 100 [0.006760615, 0.157471112], 500 [0.006759671, 0.157471153], 1000 [0.006758491, 0.157471204].
- 16×16: 36 initial departures, 4 definite sampled sign-switch brackets, 0 ambiguous brackets; checkpoint `gdot` min/max: 100 [-0.011325095, 0.157465273], 500 [-0.008344282, 0.157436290], 1000 [-0.008110768, 0.157441412].

## Four authentic source R6BND original gap sign brackets

| Original source boundary | Model years | From → To |
| --- | --- | --- |
| `R6BND-T0-f679f4c97f1e7445d8d9` | 175–200 | NEGATIVE → POSITIVE |
| `R6BND-T0-4d168aac7492e7c418de` | 475–500 | POSITIVE → NEGATIVE |
| `R6BND-T0-1569360d5844c75db0d3` | 625–650 | NEGATIVE → POSITIVE |
| `R6BND-T0-16d7dc72630ecb414c04` | 875–900 | NEGATIVE → POSITIVE |

No individual zero-crossing event time is determined; intervals are sampling BRACKETS, not geological collision dates. Four events are not proven exhaustive in continuous time.

## Scientific conclusion

`PASS_ENGINEERING_ONLY_SOURCE_SHELL_DIFF_RATE_AND_TRIPLE_VECTOR_AUDIT`. Rates are directional derivatives of the source-owned material-midpoint 2D shell opening functional, evaluated using reconstructed **previous fixed-T0** unilateral KKT trajectory; not physical tractions and not a solver for that updated gap. Triple-node position and velocity closure is a vector algebra identity/check, **not** equilibrium of three bodies. Sign of g and sign of gdot describe different phenomena (opening versus opening rate). No natural rock 3D solid boundary closure/Signorini law proven.

Scientific next gate: **`R6_G2_SHELL_EVENT_TEMPORAL_RESOLUTION_AND_VELOCITY_COHERENCE`**, narrow and source-preserving. Independently re-integrate existing 1-model-year source T0-KKT history with checkpoint captures at all existing 25-year times and integer years inside only the four detected brackets, verify exact replay SHA and per-source IDs against prior report. Refine to **1-year sign brackets**, without interpolation being asserted an exact collision time; compare finite time trajectory g(t±1) with instantaneous gdot from full current point velocities, report discrepancy (account for discrete-time reconstruction and possible activation switches) rather than silently assuming equivalence. Verify triple parent 34587 again, and leave physical KKT prohibited.

`D-024=ACTIVE`, `physical_T1=null`, physical solver 0, no HistoryStore or canonical promotion.
