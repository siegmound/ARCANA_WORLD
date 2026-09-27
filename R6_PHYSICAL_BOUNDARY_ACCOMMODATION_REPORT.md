# R6 Physical Boundary Accommodation Authority Adjudication

**Decision:** `R6_BOUNDARY_ACCOMMODATION_NOT_ESTABLISHED__RESEARCH_REQUIRED`

Parent: `r6/physical-domain-t0-binding` at `f327a317bc8650df3abcfe5a5e9924eebafbe427`; parent decision `R6_PHYSICAL_DOMAIN_T0_BOUND__FIRST_INTERVAL_BLOCKED`.

## Canonical T0

- State: `r6state_1d36fb90cd23443407ce6c63611a65b74c5a9157bd89b1c6cec449d9b927f2d9` at 210.0 Ma.
- Parent / vector / kinematics SHA-256: `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c` / `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab` / `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`.
- Inventory: 12 plates, 64,800 parent faces, 1,983 edges, 30 plate pairs, 20 degree-3 junctions.
- Support: `COARSE_SUPPORT_ON_FINE_GRID`. Payloads and the bound T0 state remain unchanged.

## Boundary graph and sections

Reconstructed 30 deterministic same-pair branches and 30 canonical junction-to-junction sections. All 1,983 source edges are covered once; branch IDs are repeatable.
Each section boundary is a canonical degree-three junction. Parent-grid edges are retained as support subdivisions, not promoted into finer physical resolution.

## Pure-plate anchors

Validated anchors: **0** of 60 section-side slots. All 60 remain unresolved: plate ownership is known, but governed deformation-zone/exclusion semantics do not establish that a candidate support lies outside the deforming region.

## Relative motion: level 1 only

The existing Euler-vector and spherical local-frame census resolves normal and tangential demand for 1,983/1,983 boundary edges; unresolved: 0.
Kinematic demand counts: `CONVERGENT_KINEMATIC_DEMAND` 1091, `DIVERGENT_KINEMATIC_DEMAND` 892.
Existing combined normal/tangential classifications: `MIXED_CLOSING_SHEAR` 1091, `MIXED_OPENING_SHEAR` 892. These describe motion only; they do not identify tectonic processes.

## Physical accommodation: level 2

**NOT_ESTABLISHED**. Positive accommodated sections: 0; sections with an authority gap: 30. Existing authority reports `NO_PHYSICALLY_DEFENSIBLE_POSITIVE_ACCOMMODATION_FOUND`.
Repository T0 authority provides plate Euler kinematics and relative-motion demand, but no constitutive/mechanical state or governed rule mapping demand to boundary material motion/deformation. It supplies no force/stress balance, rheological strength, yield criterion, boundary width semantics, or junction residual allocation.

## Junctions and patch operator

Junction outcome counts: JUNCTION_COMPATIBLE=0, JUNCTION_UNDERDETERMINED=0, JUNCTION_INCOMPATIBLE=0, JUNCTION_AUTHORITY_GAP=20. No junction accommodation residual is calculated because no physical constraints or allocation law are authorized.
Patch operator: `OVERLAP_DERIVED_PATCH_BOUNDARY_DIRICHLET_INCOMPATIBLE`; replacement established: **False**. Diagnostic width trials are not canonical `W_model`.
The prior operator has persistent nonzero Dirichlet corner mismatches at some diagnostic widths; the 100 km run also reports a port-extraction implementation failure. Other junctions remain numerically unresolved or their domains fail. The validation never materialized a patch. Thus the evidence shows both an implementation defect and unresolved corner constraints; it does not establish physical incompatibility.
Current blocker: `JUNCTION_PATCH_REDEFINITION_FROM_CANONICAL_BRANCH_CROSS_SECTIONS_AND_PURE_PLATE_ANCHORS`.

## Research gate and readiness

External targeted scientific research is required: **True**.
Smallest question: What ARCANA-authorized mechanical/constitutive rule maps canonical instantaneous plate-side relative motion and boundary state to physical boundary accommodation, and what simultaneous closure condition does that rule impose at a degree-three junction, without an unsupported width or rheological parameter?
Instantaneous T0 well-posed: **False**. First-interval contract design authorized: **False**.

## Invariants

```text
canonical_payload_changed = false
t0_state_mutated = false
dt_selected = false
t1_created = false
W_model_selected = false
forward_evolution = false
first_interval_authorized = false
```

No finite evolution, future state, boundary law, or patch replacement was created.
