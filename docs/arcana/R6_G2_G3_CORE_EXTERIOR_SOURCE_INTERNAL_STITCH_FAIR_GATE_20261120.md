# R6 — G2 core + G3 exterior: full source-indexed *internal* weak-form coupling

**Date:** 2026-11-20. **Status:** NEW SOURCE CODE, FAIR PENDING. **NO global physical residual or solve** while source core external/basal/GPE data are absent.

## Why this is a substantive new integration

The preceding FAIR `72168a5e...` checked 19/19 new and 96/96 related regression tests for G2 candidate constitutive stress/tangent integrated over G3 **exterior** P1 facets with explicit G3 exterior line+basal tractions and one-owner GPE. However the original source has an **8-triangle core with one core-only parent node** not in the exterior Schur mechanical DOFs. For a true source-original coupled internal operator, G2 core and G3 exterior must be assembled into **one global parent East/North DOF list**. A passed exterior test alone does not constitute full source-domain integration.

Now added:
- `g2_g3_source_core_exterior_stitch.py`: genuine G2 material-candidate full core 8 triangle potential/gradient/tangent evaluation using existing PRE vertex quadrature + spherical P1 B. Exact one-owner original source shared DOF injection for G2 core and G3 exterior, internal total (F_{int}=S_c^TF_c+S_e^TF_e), tangent (K=S_c^TK_cS_c+S_e^TK_eS_e), potential and virtual-power sum.
- `g2_g3_core_exterior_source_runner.py`: reads SHA-pinned FAIR CONTINUATION_A, MULTISCALE_INTERFACE, G2 nodal PRE, and G3 external force inventory; authentic FEG 81 or 289 parent nodes; **core 8 original source triangle IDs** as exact complement of 120 or 504 exterior triangle IDs; core exactly 8 shared interface parent nodes + 1 original core-only parent; G3 exterior 80/288 mechanical parent nodes. Demands explicit 81/289 source-node material candidates and velocities and **all** existing G3 exterior cut/basal/GPE fields; no inference or zero defaults.
- `G2_G3_EXPLICIT_FULL_PARENT_ENGINEERING_INPUT_TEMPLATE_V1.json`: all missing source physical inputs remain `null`; not runnable without explicit engineering candidate source document.
- `tests/test_r6_g2_g3_source_core_exterior_stitch.py` + `tests/test_r6_g2_g3_core_exterior_source_runner.py`: synthetic real G2 constitutive core fan, original parent-node force/tangent mapping, cross-coupling terms, virtual power and strict refusal of falsified source coverage or physical promotion. **FAIR PENDING**.

## Core source partition

| Extent | Original source parent nodes | G2 original core facets/nodes | G3 original exterior facets/nodes | Shared source interface EN DOF |
| --- | ---: | ---: | ---: | ---: |
| 8×8 | 81 | 8 / 9 | 120 / 80 | 16 |
| 16×16 | 289 | 8 / 9 | 504 / 288 | 16 |

No duplicate original parent ID or fault node is invented. Original 16×16 source triple parent 34587 is not automatically a duplicate slip DOF. All original FEG source triangles are represented in combined **internal** tangent once: 128 for 8×8 or 512 for 16×16. The 8 shared parent nodes are represented once globally, summing both original source facet internal contributions. Source center is added once.

## What can and cannot be computed

The source G3 force inventory covers only its **120/504 exterior basal facets**, not the **8 original core facets**. The previous source G3 hydrostatic GPE external vector belongs to exterior mechanical nodes only. A full-domain physically closed external load vector **cannot be formed** by silently assigning zero loads to the core. The new result therefore explicitly reports:

- full original-source **candidate internal** nodal force/tangent and internal energy over 81/289 parent nodes;
- **known exterior** external+GPE force accumulated on parent nodes;
- `known_PARTIAL_residual_N_NOT_EQUILIBRIUM` (a purely partial bookkeeping difference), `full_domain_physical_residual_AVAILABLE=false`, `core_external_and_basal_GPE_physics_qualified=false`;
- total *known-channel* work partition and internal work, while preventing the report from claiming force balance, nonlinear convergence or contact physics;
- no calibrated source G2 materials, no basement normal support or measured mantle/outer-cut traction providers, no 3D physical signed gap, no fault slip law, no physical solve or T1.

The spherical faceted element is not automatically ShellSet's covariant nonlinear continuum. The selected smooth harmonic Drucker–Prager cap is not a return-mapped fault law. Source PRE codes are not geological mineralogy, and uploaded canon section 53/57 concern material-response architecture/ambient reference properties rather than original 210 Ma crust/mantle identity.

## FAIR validation protocol

Clean checkout at the new exact commit; activate conda `arcana-r6-linux`, `PYTHONPATH=src:.`, `PYTHONDONTWRITEBYTECODE=1` and `OPENBLAS_NUM_THREADS=OMP_NUM_THREADS=MKL_NUM_THREADS=1`. Run these two targeted suites first, then the original two G2/G3 coupled suites + G2 source bridge, G2 viscoplastic and G3 spherical/force/GPE regressions. **Do not execute the source connected runner on the null template**: a full explicit 81/289-parent candidate and all G3 forcing would first need provenance/engineering decision, and any output remains noncanonical source engineering only.

### Final scientific requirement before a true global mechanical solve

Complete source-authorized core external/basal load integration, identify original ARCANA material mineralogy/hydration and lab law coverage, physical mantle and cut traction/vertical support and single GPE owner, and choose real 2D fault-slip law **or** justified 3D closed solid contact formulation. Then verify gauge/rank, force/torque/virtual work, P/T/rate envelope, spatial refinement and solver compatibility under explicit authorial approval.

`D-024=ACTIVE` • `physical_T1=null` • `mechanical_solve_authorized=false` • no canon/HistoryStore mutation.
