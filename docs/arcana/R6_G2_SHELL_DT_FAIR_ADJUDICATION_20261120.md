# ARCANA R6 — Bounded original shell dt comparison: FAIR verified, event timing not robust

**Date:** 2026-11-20. **Exact tested source:** `4c1afe2a14cef0899412fe017e6821425f6ae413`. Original FAIR operator: `17/17` targeted unit tests, `135/135` combined suites in 0.87 s, `DRIVER_EXIT_CODE=0`, status `PASS_SOURCE_SHELL_ORIGINAL_DT_COMPARISON_INVENTORY__PHYSICAL_CONTACT_OPEN`. Manifest `REPORT.json` SHA256 `d89664fd0cf5adf7ee7d1ed6920d410d3887e44d8a45d12f41f680cf69611fec`, independently compared with `sha256sum` on actual FAIR report by operator; no raw FAIR byte copy retrieved into assistant environment. `physical_T1=null`, `D-024=ACTIVE`, no canonical promotion.

## What really converges at common checkpoint times

The original 16×16 FEG/PRE plate 5:8:11 source (36 authentic paired original R6BND material edge IDs; 39 source links, triple 34587) was compared at **41 source common checkpoints** over dt 1, 0.5, 0.25, for **1476 original edge-time pairs**. Results:

| Old T0 manufactured KKT time-step comparison | Max absolute source matched material shell midpoint gap difference |
| --- | ---: |
| dt 1 vs 0.5 model-year | `0.0015894768067912235m` |
| dt 0.5 vs 0.25 model-year | `0.0007949563024012285m` |
| ratio of successive differences | `0.5001370885090526` |

Differences CONTRACT at common clocks in a manner *consistent with approximate first-order numerical convergence*, but three steps **do not certify** asymptotic order or calibrated geological accuracy. Both original source local-substep restart consistency errors were `0.0m` on the code's reported metric.

## What did NOT become stable: sign-switch times

The prior dt=1 1-year source shell sign brackets are **not robust when changing dt**. The new experiment probes **inside only those earlier dt1 1-year windows**, and evaluates whether both endpoint signs remain opposed.

| Original source R6BND edge | dt1 1y bracket | dt0.5 sampled bracket inside prior window | dt0.25 sampled bracket inside prior window |
| --- | --- | --- | --- |
| `R6BND-T0-1569360d5844c75db0d3` | 642–643 | outside old window / sign drift | outside old window / sign drift |
| `R6BND-T0-16d7dc72630ecb414c04` | 892–893 | 892.5–893 | outside old window / sign drift |
| `R6BND-T0-4d168aac7492e7c418de` | 477–478 | outside old window / sign drift | outside old window / sign drift |
| `R6BND-T0-f679f4c97f1e7445d8d9` | 197–198 | 197.5–198 | outside old window / sign drift |

Thus dt0.5 retains 2/4 events *inside the previous annual windows*, while dt0.25 retains 0/4 there. **This does NOT show that the physical events disappear, nor that the shell opening function is discontinuous**. It shows that the previous 1-year intervals cannot be promoted as timestep-independent events, and further source *time location* was not measured by this bounded gate. Even a smooth convergence of `g` at fixed time can shift zero locations by more than 1 model-year when the local rate is small. Do not infer exact crossing times.

## Scientific adjudication

`PASS_ENGINEERING_ONLY_DT_COMPARISON_INVENTORY__FAIL_CLOSED_ON_SOURCE_EVENT_TIME_QUALIFICATION`.

Stop further numerical microrefinement of the same **manufactured T0-KKT shell midpoint proxy**. Its source geometry is 2D plate-owned P1 triangles with consistent winding and co-normals, not a closed 3D rock volume. The existing diagnostics explicitly mark `source_owned_closed_solid_volume_proven=false`, `physical_signed_surface_contact_gap_available=false`, and 0 physical solid contacts. The PRE source supplies 51 fields and genuine thickness/density/layer boundaries as passive T0 records, **not** source-authorized contact side faces or physical traction laws. No sidewall may be synthesized from thickness scalars without explicit science and governance.

**Next scientific unit, not another geometry PASS loop:** the earlier evidence-qualified G2/G3 coupled physical-closure decision in `docs/arcana/R6_G2_G3_A_PHYSICAL_CLOSURE_ADJUDICATION_20261119.md` and `docs/arcana/R6_G2_G3_EMPIRICAL_CALIBRATION_FAIR_PASS_20261120.md`. Build a **single source-authority decision package** that ties together:
1. source rock layer/mineral identification and laboratory parameter range/uncertainty (`A,n,E,V` plus hydration, pore/effective pressure, brittle/ductile),
2. real regional G3 cut traction, basal normal/tangential loads, deep mantle reference motion and single GPE owner,
3. explicit physical choice between a calibrated thin-shell fault/boundary law and an actual validated closed-solid plate geometry/interface, including topology, oriented boundary side, gap convention and actual rock strength/traction,
4. owner/provider provenance, explicit authorial experiment scope and solver choice with no double-count and without silently changing original SHELLS common creep exponent.

If any required provider remains absent, return `SOURCE_AUTHORITY_GAP`, NOT synthetic zero forces or a new canonical physical T1. Until explicit coupled source+physics closure, G2 full rheology remains unratified, G3 loading/vertical support unqualified, original physical contact KKT not executable; `D-024=ACTIVE`, `physical_T1=null`, 0 new physical solver runs, no HistoryStore/canon mutation.

**WorldSim objective preserved:** a history-generation engine must ultimately produce searchable geologic and environmental history (resources, tectonics, biota and selective temporal/spatial re-resolution) with source provenance, rather than mistaking precision in a surrogate source-shell gap for validated geologic history.
