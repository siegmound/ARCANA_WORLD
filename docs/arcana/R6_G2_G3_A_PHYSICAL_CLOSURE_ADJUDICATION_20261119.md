# ARCANA R6 — G2/G3 A physical-closure adjudication after FAIR force inventory

**Date:** 2026-11-19. **Scope:** 210 Ma T0 source plate 5:8:11, G3 outer continuum A **already author-ratified for noncanonical EXPLORE only**. **Decision:** `G2_G3_A_SOURCE_AND_ENGINEERING_ASSEMBLY_PASS__PHYSICAL_PARAMETERS_UNRATIFIED`. No solver authorization, no physical T1, D-024 unchanged.

## 1. New actual FAIR result and provenance
FAIR operator reported the terminal on the isolated branch at `239f9d1a04e79fb816110306de5ba50ec26eb25b`:
```text
tests/test_r6_g3_force_budget.py                         9 passed in 0.13s
PASS_G3_A_FORCE_SOURCE_INVENTORY__LOAD_PHYSICS_UNRESOLVED
8x8:  32 outer-cut edges, 120 exterior basal triangles, plates [5,8], zero 3+-plate junctions
16x16: 64 outer-cut edges, 504 exterior basal triangles, plates [5,8,11], one 3+-plate junction
mechanical_solve_authorized=false
solver_runs=0
physical_T1=null
```
FAIR evidence folder: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_FORCE_REQUIREMENTS_NEW_01`. **Only the operator's terminal is available to this commit**; no independent direct reading of the FAIR output or SHA verification was performed here. Original evidence folders remain untouched.

## 2. What has truly been achieved

| Subsystem | Authenticated source/engineering status | Physical status |
|---|---|---|
| T0 100/1000Y global rigid kinematics | FAIR PASS, numerical prefix/restart exact | Contact accommodation NOT solved |
| G3 5:8 2x2/4x4, 8x8 and 16x16 geometry | FAIR PASS, SHA-linked source mesh and PRE | Domain-size convergence NOT shown |
| Plate 5:8:11 topology | source graph: 18 (5:8), 7 (5:11), 11 (8:11) edges on 16x16; authentic triple parent node **34587** | No fault opening/traction assigned |
| 8x8 and 16x16 spherical-facet metric | FAIR PASS, maximum relative triangle area discrepancy 7.5588e-05 / 7.6049e-05; rigid SO(3) strain ~4.09e-29/s | not covariant ShellSet tensor parity |
| PRE-to-element | 81/289 real nodes, 120/504 source exterior triangles; 0 source `material_configuration_code` mixed triangles | **not** evidence for single real mineralogy, water state or faulting |
| G2 2-layer nonlinear candidate | FAIR 11/11 **synthetic** tests: potential/gradient/tangent, independent crust/mantle exponents | full-column brittle/ductile, water and real rock identity NOT qualified |
| G3 traction/basal weak form | FAIR 9/9 **synthetic** tests; source needs 32/64 cut tractions and 120/504 per-triangle basal entries | values/source-provider/normal basal and GPE closure MISSING |
| Physics solver | no physically assembled `K/f` with source-supported material | `solver_runs=0`, `T1=null` |

Crucially, the latest force inventory is an **exhaustive required-input list**, not a computed regional driving-force field or equilibrium. An explicit synthetic zero traction is not a physical free boundary. Neither a plausible numerical residual nor geometry PASS substitutes for authorized material/boundary states.

## 3. Scientific assessment: G2 constitutive material

**Present source PRE metadata** (51 fields/node) contains crust/mantle thickness and densities, calibrated thermal polynomials, material configuration codes, plus present/absent flags. It does **not by itself supply** a rock-specific dislocation creep prefactor/exponent, real lithology identity calibrated to a laboratory law, water fugacity/hydration profile, pore pressure/Biot, fracture/fault fabric or full friction/ductile cap. Do not reinterpret finite zero encoding as dry rock or zero pore pressure. Zero mixed configuration-code triangles is not mineralogical or fluid homogeneity.

**Candidate literature with strict experimental scope:**
- Gleason & Tullis (1995), *A flow law for dislocation creep of quartz aggregates determined with the molten salt cell*, DOI `10.1016/0040-1951(95)00011-B`. Natural quartzite around **0.15 wt% water**, pressure around **1.5 GPa**, **900–1100°C** in the reported experiment; `n≈4` is a **laboratory proxy, not globally valid cold upper-crust rheology**. The hydrated rock sample must not be labeled universally dry: https://www.sciencedirect.com/science/article/pii/004019519500011B ; details also https://doi.org/10.1002/2016JB013798 .
- Hirth, Teyssier & Dunlap (2001), DOI `10.1007/s005310000152`, compare laboratory quartz flow laws and naturally deformed rocks, finding water fugacity an important term: https://experts.umn.edu/en/publications/an-evaluation-of-quartzite-flow-laws-based-on-comparisons-between/ . Never infer ARCANA `fH2O` from quartzite's experimental water content.
- Brace & Kohlstedt (1980), DOI `10.1029/JB085iB11p06248`: laboratory lithospheric strength envelopes require brittle friction tied to effective stress and fluid pressure and ductile creep, and their relevance depends on conditions: https://earthref.org/ERR/34201/ .
- ASPECT material model documentation explicitly notes the experimental-to-solver stress-invariant and fugacity-prefactor convention transformations: https://aspect-documentation.readthedocs.io/en/latest/user/cookbooks/cookbooks/continental_extension/doc/continental_extension.html .

**One material decision cannot be replaced by a `common_eCreep` average.** Original SHELLS uses one LR exponent for crust and mantle in `Diamnd`, `Mohr`, and `OneBar` (including `glue`). GT95 n~4 and olivine n~3.5 are *not* exactly identical. The separate G2/G3 experimental potential supports two slopes algebraically but is not equivalent to a complete ShellSet nonlinear/frictional solver, nor a calibrated mineralogical material.

## 4. Scientific assessment: G3 A force sources and GPE

- Bird (1999), DOI `10.1016/S0098-3004(98)00142-3`, models horizontally 2D velocity while integrating 3D lithospheric density and strength, including brittle/ductile transitions: https://www.sciencedirect.com/science/article/abs/pii/S0098300498001423 .
- Bird et al. (2008), DOI `10.1029/2007JB005460`, distinguish plate-driving stresses, mantle basal shear, and contributions of lithospheric stress and force torques; basal drag can be modeled relative to deep mantle flow or other provider. This **does not supply ARCANA basal values**: https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007jb005460 .
- Regional force balance includes gravitational potential energy (GPE), boundary interactions, and basal stresses as distinct mechanisms: https://academic.oup.com/gji/article/169/3/866/2130409 . The canonical PRE 51-field list supplies densities/thickness/thermal fields but does **not alone establish** validated topographic/elevation and reference asthenosphere pressure needed for a complete regional GPE gradient. These could exist elsewhere in authoritative sources and must be explicitly bound if so; absence from PRE is not a claim of absence from all ARCANA.
- The actual G3 force vector must distinguish an external-cut traction line integral (N/m), a basal tangential traction area integral (N/m²), the lithospheric GPE/pressure contribution, and the basal normal closure. A physical double-count audit must show one exact owner of each contribution in the selected solver weak form; the test marker `SYNTHETIC_NO_GPE` is never a substitute for that audit.
- Plate11 and triple node34587 remain one displacement/velocity state per source node in continuous G3 A: Euler vectors are far-field *kinematic priors*, not separate imposed DOFs; any tectonic interface slip requires an explicit fault law and source support.

## 5. Minimal physically meaningful next unit — paired science & implementation

**Do not run another geometry/metadata microgate, benchmark rigid-year extension, or make a 'PASS' report for null physical inputs.** The next substantial integration must couple the following, in a **single bounded noncanonical design**:

**G2 material scenario (authorial decision not yet taken).** Select reference crust lithology and mantle lithology, plus any 5:8:11 regional heterogeneity, with source-calibrated power law `A,n,E,V`, stress convention, P/T/rate domain, water fugacity field/branch, effective-pressure law/Biot, brittle fault/ductile transitions, and a qualified PRE-to-element mixture rule. Mark conditions outside laboratory scope as extrapolation requiring explicit acceptance, not valid results. A dry/reference branch and a water-sensitive *sensitivity branch* can both be maintained, but neither may be silently promoted to ARCANA physical truth.

**G3 boundary/basal scenario (authorial decision not yet taken).** Source the extent at which far-field plate priors are applied, a continuum-consistent north/south state and non-duplicated west/east constraints, explicit physically justified basal normal support, basal tangential law and deep mantle reference flow, and a single GPE force owner. Diagnose rank/gauge, force, torque and virtual-work conservation with the *same* law and mesh; do not use arbitrary force cancellation.

**Solver compatibility decision.** Either (a) preserve original SHELLS with a **calibrated common creep exponent + documented approximation error** and complete friction, or (b) explicitly authorize a separately versioned EXPLORE two-exponent solver with full nonlinear constitutive and fault/OneBar/kinematic equivalence testing, rather than swapping one variable. The present engineering potential is suitable for *unit tests*, not for declaring physical convergence.

**Only after the coupled scenario is scientifically defensible** should a single 8x8 reference (plates 5:8) and 16x16 sensitivity (5:8:11) be used for mechanical parameter/domain sensitivity. No automatic solve, no T1, no G4 or HistoryStore world event.

### Unchanged decision boundaries

```text
G3_A_ARCHITECTURE_AUTHOR_RATIFIED=true
G2_SOURCE_PRE_TO_ELEMENTS=FAIR_PASS
G3_SOURCE_FORCE_INVENTORY=FAIR_PASS
G2_FULL_CONSTITUTIVE_LAW_RATIFIED=false
G3_REAL_LOAD_AND_GPE_OWNER_RATIFIED=false
G3_BASAL_NORMAL_AND_TANGENTIAL_PHYSICS_RATIFIED=false
SHELLS_TWO_EXPONENT_PHYSICAL_SOLVER_PARITY=false
MECHANICAL_SOLVE_AUTHORIZED=false
SOLVER_RUNS=0
PHYSICAL_T1=null
D_024=BLOCKING
```
