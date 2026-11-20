# ARCANA R6 — FAIR robustness / global sparse-scale PASS

**20 November 2026**, source tested: `d07ae8038a5ddbcb8b4601e7b54582dc2420818a`.
**Decision:** `PASS_REGIONAL_ENGINEERING_PARAMETER_ROBUSTNESS_AND_GLOBAL_SPARSE_GRAPH_PROBE__PHYSICS_OPEN`.

## FAIR operator evidence

FAIR fetched the exact tested commit, using SciPy 1.18.1. The user-supplied terminal output reports:

```text
.................... [100%]
20 passed in 0.67s
status = PASS_REGIONAL_ENGINEERING_PARAMETER_ROBUSTNESS_AND_GLOBAL_SPARSE_GRAPH_PROBE__PHYSICS_OPEN
uniform_viscosity_invariance_max_m = 6.252776074688882e-13
exact_subyear_order = [0.9993294386688701, 0.9996643894463283]
global_sparse.source_plate_local_views = 66435
global_sparse.EN_dofs = 132870
global_sparse.dense_EN_matrix_gib = 131.53580501675606
global_sparse.one_component_CSR_bytes = 5750236
global_sparse.graph_nnz = 457041
global_sparse.cg_iterations = 14
global_sparse.cg_relative_residual = 2.1357722144717512e-10
physical_solver_runs = 0
physical_T1 = null
```

The original FAIR report is at
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/G1_G2_ROBUSTNESS_GLOBAL_SPARSE_NEW_01/ROBUSTNESS_GLOBAL_REPORT.json`.
The **full report and its SHA manifest have not been independently fetched
into the authoring environment**. Thus the terminal gives names of all eight
regional scenarios but not their individual numeric displacement/speed
differences. Those results must be extracted from the FAIR report before
making detailed cross-scenario scientific conclusions.

## Regional manufactured parameter robustness

Eight cases completed: baseline; common viscosity ×10; crust viscosity
×10; mantle viscosity ×10; `tau=100/400y` (baseline 200y); synthetic
driving dashpot multiplier `0.25/1.0` (baseline 0.5).

The common-factor viscosity ×10 scenario differed from baseline at most
`6.252776074688882e-13 m`, as expected because this **constructed**
model scales internal K and synthetic C together. This establishes a
**structural non-identifiability** of absolute common viscosity in this
model. It is not a result about the true ARCANA mineral viscosity.

An independent *exactly solvable two-mode kernel*, not the original
regional material geometry, yields measured backward-Euler convergence
orders `0.9993294386688701` and `0.9996643894463283` from
successive steps of `1,0.5,0.25y`. Strong support for the
implementation's first-order temporal accuracy in the manufactured
constant-drive problem; this is **not yet a region-wide sub-year
timestep convergence result**.

## Global numerical scale

Original planetary inventory: 64,442 source parent nodes, 128,880
source triangles, 12 plates. The sparse graph preserves 66,435
plate-local material views at shared contact source locations;
this implies 132,870 *potential* EN displacement DOFs.

A dense 132,870-square `float64` matrix alone requires ~131.536 GiB,
before storage, factorization, and vectors. The **one scalar component**
CSR sparse graph recorded `5,750,236 bytes` of array storage and
457,041 graph nonzeros. This is not a memory measurement of the full
global mechanical solver, nor the complete simulation RSS.

Conjugate gradient solved one manufactured **SPD graph problem**
`(I + 0.05 L)x = b` in **14 iterations**, with
relative residual `2.1357722144717512e-10`.
This proves the source-bound global topology can be represented
and a **well-conditioned graph surrogate** solved sparsely.
It does NOT prove that a real P1 G2 spherical viscoplastic tangent
converges in 14 iterations, or that global physical 1000-year
coupled simulation fits in the same memory.

The original weighted-welded multiplete G1 Euler interface remains
a synthetic contact treatment; the global sparse graph instead keeps
plate-local views disconnected at shared source nodes. These are
different mathematical contact conventions and **cannot be claimed
equivalent**.

## Next scientific engineering gate

1. Read the actual detailed FAIR scenario outcomes at both horizons:
   displacement, feedback speed, force/energy error and area Jacobian.
2. Build **true sparse P1** (or matrix-free) tangent on global genuine
   12-plate source, with identical constitutive conventions and
   local-element calculations to the regional solver. Establish
   regional sparse-vs-dense tangent action, virtual-work, force and
   dimension parity before using it globally.
3. Expose plate-contact boundary semantics explicitly: independent
   plate-local nodes, welded constraints or experimental slip/open
   laws. Do not silently average incompatible Euler Dirichlet values.
4. Check static globally manufactured linear response, solver iteration
   counts, RAM, residual, energy and frame invariance. Require
   fixed-geographic-extent mesh refinement before claiming spatial
   convergence.
5. Only afterward run **manufactured** 100/1000-year global
   time integration with restart, timestep and cost controls.

Not yet qualified: true G2 rock/mineralogy/water/poroelasticity,
G3 lateral/basal normal and shear forcing, G4 layer transport,
events, geological surface/resource evolution. No actual
`physical_T1`, no changes to HistoryStore; D-024 remains ACTIVE.

**Do not interpret this as a PASS of global G2 FEM or global physical
1000-year evolution.**
