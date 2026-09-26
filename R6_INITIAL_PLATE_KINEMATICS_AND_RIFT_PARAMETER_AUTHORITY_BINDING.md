# R6 initial plate kinematics and rift parameter authority binding

**Research date:** 2026-09-24\
**Baseline:** `main` / `origin/main` = `592b1651b405363373590092e133bd25569d99a5`\
**Decision:** `T0_VECTOR_PARTITION_AND_EVENT_ELIGIBILITY_BINDING_REQUIRED_BEFORE_REPLAY`\
**Verdict:** `EARTH_PRIORS_BOUNDED__INITIAL_MOTION_AND_RIFT_CENSUS_REMAIN_UNBOUND`

This is literature and authority binding only. No plate motion, event, trajectory or scientific output was generated. R6 remains a synthetic Earth-scale world at 210 Ma; Earth observations are priors, not its geography or path.

## Findings by the exact 12 requirement IDs

| ID | Disposition | Binding result and remaining gap |
|---|---|---|
| P01 initial plate kinematics | `BOUNDED_PRIOR` | Zahirovic et al. report Mesozoic–Cenozoic continental RMS typically about 3 cm/yr, with excursions about 5–6 cm/yr; plate rates also depend on continental/cratonic fraction, subducting perimeter and reference frame. This is a broad plausibility comparator, **not** a per-plate speed distribution or an assigned vector. Plate-specific rotation, direction and canonical realization remain unbound. [Primary study](https://doi.org/10.1016/j.epsl.2015.02.037) |
| P02 segment validity | `BOUNDED_PRIOR` | Use the earliest of a governed event, topology transition, law-validity bound or displacement/error bound to end a segment; do not impose a fixed global duration. Noise-reduced Earth reconstructions suggest genuine changes are not resolved below a few Myr, which is a caution, not an R6 minimum/maximum. [Study](https://doi.org/10.1038/ncomms2051) |
| P03 motion-change law | `BLOCKED` | Piecewise finite-rotation segments are representation, not causation. No justified rule or parameters were found for changing R6 motion between segments; random walk is rejected. |
| P04 t0 vector partition | `BOUND` | Contract specifies spherical polygons as exact unions of existing 1° cell support, preserving parent-cell membership and coarse uncertainty. No snapping, smoothing or sub-cell inference. Can be generated from t0 **as a representation**, not as greater geological truth; materialization and topology validation still need implementation. |
| P05 weak zones | `EXPLICIT_UNKNOWN_ALLOWED` | Literature supports inherited weakness as a factor in rift localization, but no strength/class threshold transfers to this synthetic mosaic. Existing design labels are not mechanical weakness. Keep weakness UNKNOWN; do not trigger a rift from it. [Review](https://doi.org/10.1038/s43017-023-00391-3) |
| P06 extensional forcing | `BOUND` | Define opening rate on an authorized boundary segment as `max(0, (vB − vA) · nAB)`, with `nAB` the local normal from A to B. Units: m/yr; support: boundary segments; source: derived from authorized kinematics and geometry. This is not stress or a rift threshold; no current value is computable. |
| P07 rift eligibility | `EXPLICIT_UNKNOWN_ALLOWED` | Three-valued predicate over supported weakness, positive opening and governed persistence. If evidence is incomplete, eligibility is UNKNOWN—not coerced to true or false. No numeric threshold bound. |
| P08 initiation trigger | `BLOCKED` | No universal transferable accumulated-extension/strain/time threshold or event hazard was found for R6. A pure stochastic timestamp is not acceptable. |
| P09 split/lineage realization | `BLOCKED` | No supported global rule for event geometry, child lineage, topology, fragment scale or new crust/domain state. It cannot be deferred because t0 eligibility is not known. |
| P10 event census | `BLOCKED` | The census schema is deterministic and non-generative, but is not executable without vector partition, adjacency/boundary semantics, kinematics, weakness and driver state. Current rift status is `UNKNOWN_NOT_EVALUATED`. |
| P11 numerical stepping | `BLOCKED` | Largest valid step should satisfy motion/displacement, solver error, topology and event-localization constraints; rejected steps subdivide and retry. No numeric tolerance can be selected before solver precision, feature support and process scales are bound. |
| P12 uncertainty/canonical realization | `EXPLICIT_UNKNOWN_ALLOWED` | Preserve supported ranges or UNKNOWN; invent no Gaussian/uniform distributions. Precommit any later canonical draw/selection and make it outcome-blind. No values or realization selected now. |

The Earth speed result is aggregate RMS context: the source also finds continental fraction and subduction perimeter materially affect plate speeds, so it cannot honestly supply independent initial R6 vectors. The NNR literature treats the frame as a convention with disputed physical interpretation; R6 binds it only as a synthetic gauge, defined by removing the least-squares common rigid rotation from area-weighted surface velocities—not as mantle truth or torque balance. [NNR reference](https://doi.org/10.1029/91GL01532) [NUVEL-1A calibration](https://doi.org/10.1029/94GL02118)

The rift review describes inherited-weakness exploitation, evolving force balance and both successful and failed rifts; its roughly tenfold divergence increase is a reported behavior after weakening in successful rifts, **not** a generic initiation threshold to transfer. Regional East African observations likewise show inherited structure interacting with far-field extension and punctuated/diachronic development, not a global scalar trigger. [Review](https://doi.org/10.1038/s43017-023-00391-3) [Regional synthesis](https://doi.org/10.1016/j.earscirev.2009.06.005)

pyGPlates documentation defines finite rotation as an Euler pole plus angular distance and a relative reconstruction hierarchy. That binds representation semantics only; it supplies no motion parameters or laws. [Official finite-rotation API](https://www.gplates.org/docs/pygplates/generated/pygplates.finiterotation) [GPlates methods paper](https://doi.org/10.1029/2018GC007584)

## Readiness result

Counts across the exactly 12 requirements: **BOUND 2; BOUNDED_PRIOR 2; EXPLICIT_UNKNOWN_ALLOWED 3; BLOCKED 5**; none are classified `FIRST_INTERVAL_NOT_REQUIRED` or `DEFERRED_UNTIL_EVENT` because no event census can prove the relevant transition inactive. The reference gauge is specified, but initial motion is not. A legal first `dt` cannot be determined. Rift eligibility is unknown and not evaluated. Therefore the first interval is **not executable** and full 210 Myr evolution remains unauthorized.

Climate is not required for initial plate kinematics; numeric bathymetry is not required for that narrow purpose and remains UNKNOWN; Deep is not required and no coupling was introduced. A1 was not used as authority. Canonical t0 was not changed.

**Exact next task:** `R6_T0_VECTOR_PARTITION_AND_FIRST_INTERVAL_EVENT_ELIGIBILITY_BINDING` — materialize/validate the support-preserving cell-union topology and bind the missing initial-motion/event-census inputs. Do not start replay until that census resolves the rift gate and the motion/step law is executable.

No execution contract was created.
