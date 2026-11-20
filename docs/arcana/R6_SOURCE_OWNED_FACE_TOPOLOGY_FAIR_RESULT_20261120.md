# ARCANA R6 — FAIR original plate-owned triangle-face topology audit: diagnostic PASS

**Date:** 2026-11-20. **Source checkout:** `d758a542fa207b6ad3a2f777e8d8151b869d75e2` on FAIR Linux, conda `arcana-r6-linux`.

The first FAIR test on `4150cab6...` showed **73 PASS / 1 FAIL** due solely to the synthetic test's stale expected **plate q** triangle area (`1.0` instead of `1_000_000.0 m²`). That assertion alone was corrected in `d758a542fa207b6ad3a2f777e8d8151b869d75e2` (no scientific geometry driver modification).

**Final operator terminal result:** `74 passed in 0.72s`, `PYTEST_EXIT_CODE=0`. Source driver `DRIVER_EXIT_CODE=0` with schema `ARCANA_R6_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_MANIFEST_V1`, status `PASS_SOURCE_OWNED_TRIANGLE_FACE_TOPOLOGY_AUDIT__CLOSED_SOLID_CONTACT_UNPROVEN`. Terminal-reported report SHA256 (via manifest): `3e42e1321cfb72f73bd72c82c32030969c908ec112ef5fb1255b9d7a767e4d07`.

The **actual FAIR REPORT.json and MANIFEST.json have NOT been independently retrieved**, and **the reported SHA has not yet been rechecked against raw REPORT bytes**. The terminal only showed the manifest, not numerical per-region face winding, co-normal or SO(3) diagnostics. Do not fabricate those values or assert them from a passing status. The FAIR log is `/tmp/arcana_r6_face_nYWfb3.log`.

## Scientific interpretation

The driver completed the original source-edge two-owner-triangle inventory, source-prior replay and SO(3) checks without a failing assertion. This is **evidence of the implemented engineering topology/geometry checks passing**, not evidence of geologically valid closed-solid boundary/nonpenetration.

All physical authority remains explicit NO-GO: `physical_T1=null`; no canonical promotion. Previous original-edge 8×8 and 16×16 contact-feature admissibility yielded **0 eligible signed edge-line witnesses** at all four checkpoints. The 2D P1 source sheet/facet geometry cannot *by itself* justify a closed oriented rock volume; local facet areas and windings are not a substitute. The runtime's closed-solid status is a declared scientific limitation, not a numerical proof that no alternate grounded 3D solid provider could exist.

## Next required read-only FAIR summary

SHA-verify the actual new `G2_SOURCE_OWNED_FACE_TOPOLOGY_NEW_01/REPORT.json` against its manifest and the expected `3e42...` digest. For 8×8 and 16×16 at T0,100,500,1000 extract `source_edges`, `source_faces_at_original_boundary`, radial winding counts p/q, inward co-normal angle/alignment distributions (including near-zero/positive/negative counts), per-edge source IDs with orientation anomalies, SO(3) maxima and physical-volume/qualified-contact counts. Verify authentic triple source node `34587` stays present only in 16×16.

Only afterward decide the next **3D side-of-plate / solid boundary source-provider authority gate**. Do NOT invent thickness-extruded faces, lateral side surfaces, normal orientation, collision sign, G3 tractions or 3D KKT. `D-024=ACTIVE` remains.
