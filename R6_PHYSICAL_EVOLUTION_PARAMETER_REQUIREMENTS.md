# R6 physical evolution parameter requirements

No values are assigned here. This is the finite first-interval binding set, not permission to pick convenient defaults. Requirements P01–P12 are the current blockers; later-only items are gated until their processes become active.

| ID | First-interval requirement | Why required now | Must not assume |
|---|---|---|---|
| P01 | Per-plate initial angular velocity/finite rotation, units, sign, reference frame and uncertainty | T0 kinematics are explicitly UNKNOWN. | Zero, A1 path or random walk. |
| P02 | Motion-segment validity horizon and parameter-change rule | A motion segment cannot persist by implication. | Indefinite persistence. |
| P03 | Causal motion/rate-change law and bounded rate/acceleration update | Representation alone does not cause motion. | Unconstrained seeded drift. |
| P04 | Supported spherical vector/topological t0 partition mapped to current plate IDs | The current 1° plate raster is coarse support, not exact boundaries. | Cell edges are master boundaries. |
| P05 | Weak-zone/suture geometry and mechanical strength, or an explicit supported unknown disposition | Rifting may be eligible immediately. T0 province labels do not establish weakness. | A suture label equals a weak zone. |
| P06 | Initial extensional-forcing state, units, support, source and temporal law | Needed to determine eligibility and trigger. | Invented forcing or implicit Deep coupling. |
| P07 | Eligibility predicate with input semantics, threshold units and unknown handling | Separates where rifting can occur from whether it starts. | All sites eligible. |
| P08 | Driver-conditioned initiation/onset law, deterministic or governed hazard | Prevents arbitrary timing; event may occur in the first interval. | Random timestamp alone. |
| P09 | Event geometry → boundary/child lineage/topology realization rule | An eligible split must have valid, reproducible consequences. | Solver chooses split semantics. |
| P10 | Initial event-eligibility census contract derived from bound law and t0 support | Must prove no immediate event is possible or bind its transition. | Deferring active event laws without evidence. |
| P11 | Numerical step acceptance: maximum displacement, event/topology tolerances and restart behavior | Needed for bounded, non-teleporting deterministic integration. | Arbitrary fixed global timestep. |
| P12 | Uncertainty class, bounds/distributions where authorized, provenance and canonical-selection rule for P01–P11 | Reproducibility does not remove model uncertainty. | Unstated distributions or aesthetic selection. |

Recommended authority routes are per-quantity literature priors plus explicit model calibration, authorial constraints only where deliberately governed, or ensemble parameters only after their distributions and selection semantics are approved. Engine defaults are not authority without exact version-specific justification.

Later gates: rift propagation/maturation; new oceanic crust/basin semantics; convergence/collision/subduction; uplift/subsidence transfer; eustatic sea level; and landscape response (including climate/material drivers). These do not authorize deferring a law whose transition can occur immediately.

**Next bounded task:** `R6_INITIAL_PLATE_KINEMATICS_AND_RIFT_PARAMETER_AUTHORITY_BINDING`. Broad architecture research is not required again.
