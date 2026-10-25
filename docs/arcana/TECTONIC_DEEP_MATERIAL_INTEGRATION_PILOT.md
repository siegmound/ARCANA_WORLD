# Geological material → Deep integration pilot

## Implemented and run

The pilot now maps the preserved ENG10K `ReducedState` directly into two
experimental sample volumes, retains a mapping record for the initial state
and each of three post-kernel states, and reuses the existing conservative
Deep transport update. Support, trajectory, sequence, source state digest,
node index, control-volume bounds, material role, and numerical-state
coordinates remain separate fields. Stable cell IDs use the support,
trajectory, and node; successive state snapshots receive distinct sequences
and state hashes.

Input: support `R6G1D-R091-C029`, trajectory
`DIRECT-f0.001-R6G1D-R091-C029`, sequence 0, state payload SHA256
`2507efbde9b9e98dccfc9e4cd7bb0eac59a7307b8adcc91955e7a5feb10914ec`.
The source archive SHA256 is `7dda60c8fa1f535d9e257eb2d04fdfde4643a92765eca8631bd766058240d8cb`.

| Node | R6 material role (not lithology) | z (m) | ρ (kg/m³) | cp (J/kg K) | k (W/m K) | Radiogenic rate (W/m³) | T (K) |
|---:|---|---:|---:|---:|---:|---:|---:|
| 23 | `CONTINENTAL_CRUST_REFERENCE` | 26,833.33 | 2,800 | 1,000 | 2.5 | 8×10⁻⁷ | 1,026.6151 |
| 25 | `LITHOSPHERIC_MANTLE_REFERENCE` | 29,083.33 | 3,300 | 1,200 | 3.3 | 2×10⁻⁸ | 1,068.7926 |

The mapped thermal diagnostic brackets the 28,000 m Moho with nodes 23 and
25 and uses piecewise thermal resistance through crust and mantle. At the
first post-kernel sample it is `-5,897.65 W` in the declared positive-downward
convention, hence directed upward. Radiogenic power integrated over the two
selected nodal control volumes is approximately `103.746 W` and `2.408 W`;
these remain ordinary thermal diagnostics and are not Deep source terms.
The selected dual volumes leave the intervening node's control volume outside
the two Deep samples; the mapping is a sparse experiment, not a continuous
geological partition.

## Separate synthetic closure and results

The role-indexed modal table is explicit synthetic data:

| Role | coupling g | detuning | loss |
|---|---:|---:|---:|
| crust reference | 0.6 | 0.3 | 0.05 |
| lithospheric mantle reference | 0.8 | 0.2 | 0.08 |

These values do not come from R6 material properties. They are not a
lithology assignment or a calibrated geological law. Deep starting stocks
`[100, 20] J` and accessibility inputs are likewise synthetic. Ordinary
conductivity and radiogenic heating are never converted into Deep energy.

Five three-step cases ran. Baseline final Deep stocks were
`[87.707372, 32.292628] J`, with net internal transport `12.292628 J` and
zero whole-system energy residual. The lower/higher mobility cases ended at
`[98.296764, 21.703236] J` / `[74.437765, 45.562235] J`. Changing the
synthetic role-modal table ended at `[99.358087, 20.641913] J`. An explicit
`+0.15` structural accessibility perturbation changed the accessible
inventory diagnostic but left stored stocks identical to baseline. All
five cases retained zero balance residual; no material-to-Deep conversion,
geological DFEU source, or solar source was enabled.

Changing the mapped crust conductivity in a regression changes the thermal
flux diagnostic while leaving Deep transport unchanged, demonstrating that
the code does not alias `k` to Deep mobility. The kernel's deformation keeps
the discrete node role IDs attached to their nodes while coordinates move;
the persisted mappings show the Moho and coordinates at each sample. These
are checks of the current R6 data path and synthetic closure only.

## Verification and limits

Focused suites: `18 passed`; `py_compile` passed. Five cases took `0.1336 s`
in total, Python `tracemalloc` peaked at `242,880 bytes` (not process RSS), and
the result JSON is `166,576 bytes`. Result:
`outputs/r6_experimental_multiphysics/MATERIAL_DEEP_INTEGRATION_20261025_02/RESULT.json`,
SHA256 `c345ba8884a9205ef892bbdb3e8ce67010456360a8ecd8952f5d76c1354a4181`.

No geological inventory in DFEU, mineralogy/lithology map, mineral modal
coupling data, Deep spectral occupancy/equilibrium, calibrated transport or
loss coefficients, measured `zeta`/`A_X`, geologic pump/source rates, or
location-specific solar flux are bound here. To produce the canon's spatial
concentration/accessibility, those fields need independently identified
geological and Deep-mode data, plus a validated constitutive relation linking
composition, phase, pressure, temperature, strain/crystal structure and mode
overlap/leakage to transport and accessibility. This pilot does not infer
those quantities from crust/mantle roles.
