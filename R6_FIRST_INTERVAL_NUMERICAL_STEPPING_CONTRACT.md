# R6 first-interval numerical stepping binding

**Decision:** `TOPOLOGY_CONTACT_GUARD_UNBOUND`
**Verdict:** `PASS_EXACT_ROTATION_FIXTURE__BLOCKED_SHARED_BOUNDARY_TRANSITION`

This binds the exact constant-Euler point/feature rotation primitive, but it does **not** authorize a positive world-state step. The t0 payload is a complete set of 64,800 closed faces grouped into 12 plates. Adjacent plate interfaces already have both opening and convergent relative motion. The contracts define neither a shared-boundary motion/resolution rule nor how a complete partition handles divergence, convergence, gaps, overlap, and contact without inventing oceanic or collision outcomes. A smaller `dt` does not supply those semantics.

The conditional rift model horizon remains 27,123.405 years for fixed t0 Euler rates. It is not itself a legal timestep. The 1,983 constructed boundary segments range from 28.8 km to 111.2 km (median 104.5 km); these describe the 1-degree support and are not subgrid geological boundary resolution. No arbitrary displacement fraction or angular cap is selected.

## Numerical representation

For constant Euler vector `Omega`, each point/feature coordinate can be evaluated by exact finite rotation `R(dt)=exp([Omega]x dt)` (quaternion form in the internal R6 primitive). This removes an ODE integration-stability restriction for that isolated transform. It does not solve plate-topology reconstruction. PyGPlates is not installed in the inspected runtime and has not been bound/validated for R6; the internal primitive is suitable for fixture-level math only until a topology backend and normalized behavior are bound. The official GPlates project describes pyGPlates as its plate-reconstruction functionality; that role is broader than the fixture kernel and does not itself authorize R6 semantics ([GPlates project](https://github.com/GPlates/GPlates)).

## Limit adjudication

| Limit | Status | Consequence |
|---|---|---|
| Rift event horizon | Conditional 27,123.405 years | Fixed t0 Euler only; upper bound, not selected `dt` |
| Motion segment validity | First subthreshold step only; no numeric duration | Cannot extrapolate past that step |
| Angular rotation cap | No point-rotation stability cap; topology cap unbound | Do not invent a cap |
| Linear displacement cap | Unbound | No authorized topology/feature fraction |
| Topology/contact guard | **Blocked** | No positive complete-partition transition proven |
| Event localization tolerance | Production tolerance unbound | Analytic fixture math only |
| Output/checkpoint spacing | Not an integration limit | Separate checkpoint and history snapshot |

Therefore `dt_first = null`, P11 remains blocked, the execution contract is not created, and steps/Myr are not reported as if a step had been selected. Ten unit/fixture test cases exercise exact rotation, spherical norm/reversal, triangle edge geometry and orientation, semigroup agreement, input rejection, and same-runtime synthetic checkpoint/replay. They do not rotate canonical t0 or validate a world transition.

After a future accepted step, the runtime must validate complete spherical topology, recompute boundaries and drivers, update only authorized progress, recompute event guards, then choose a new step. Any gap, overlap, crossing, unlocalized event, or invalid face is reject/stop; silent topology repair is forbidden. If later authorized, emit a restart checkpoint and a distinct queryable snapshot; rematerialize the derived 1-degree raster only after topology is valid. Land/crust identity may be carried; no new oceanic crust, uplift, or bathymetry is implied.

Runtime/performance notes are estimates only: O(12 transforms + 64,800 faces), input partition 5,681,184 bytes; actual runtime, peak memory, and checkpoint size have not been benchmarked. No forward physical evolution ran.
