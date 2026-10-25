# Tectonic–Deep canon-guided pilot

## Result

Implemented and ran a short, six-case sensitivity pilot using the preserved
ENG10K C029 thermal state as an initial condition. It advances the existing
`pure_shear_thermal_step` for three one-year steps per case and evolves a
separate two-cell Deep inventory. No Deep energy is inferred from or added
from thermal energy. The existing one-to-one thermal transfer and synthetic
transport pilots remain unchanged as historical baselines.

Decision: `CANON_GUIDED_ENGINEERING_PILOT_PASS__MACROSCOPIC_DEEP_LAWS_UNQUALIFIED`.

## Canon constraints used

The supplied v0.3.73 archive was read in place; no archive contents were
extracted into or written over repository files. Relevant statements are:

- Chapter 12: Deep resources are spatially and modally distributed; accessible
  free energy is the positive excess above equilibrium weighted by access;
  transport, source, material-to-Deep power and sinks are distinct terms.
- Chapter 13 (candidate, not sealed): material operators, geologic structure,
  pressure and temperature can alter Deep mode spectrum, overlap, gaps and
  leakage. It does not provide this pilot with calibrated macroscopic rates.
- Chapter 17: ordinary thermal diffusion is `k/(rho cp)`. The pilot does not
  reuse this coefficient as Deep mobility.
- Chapter 21: materials modify mode coupling/storage behavior but create no
  Deep energy; recharge requires a real source. The canon provides a
  single-mode coupling equation, not a calibrated two-cell geological law.
- Chapter 25: source attribution and cross-domain energy closure are required;
  changing accessibility is not energy transfer.

The archive and chapter byte identities are recorded in the machine result.
The chapters are canon inputs, not executable instructions; only their
scientific constraints were applied.

## Implementation and assumptions

Added `deep_geological_physics_pilot.py`, a small standalone closure alongside
the existing tectonic–Deep baseline. It separates `GeologyState`, synthetic
`ModalMaterial`, and `DeepCell` stock/accessibility/source/loss fields. The
dimensionless modal response `g²/(g² + detuning² + loss)` and the line law
`dt * mobility * min(response) * (E0-E1)` are explicit synthetic closures,
not canon equations or fitted rates. The update requires its transport
fraction to be at most 0.5, transfers equal and opposite energy, applies
explicit sources/losses, and fails closed for negative/non-finite states.

Geologic inventory in DFEU, physical modal parameters, and measured solar
forcing remain UNKNOWN. Initial Deep joule stocks and geologic source are
synthetic test inputs. The 5% solar candidate stays inactive unless a caller
supplies a clearly explicit synthetic flux; it is not actual irradiance.
Structural strain changes only the `zeta` accessibility diagnostic. Neither
`A_X` nor `zeta` is used as an energy source. Ordinary thermal conductivity is
reported but not used for Deep transport. No thermal-to-Deep 1:1 conversion
operates in this pilot.

## Measured short-run results

Run input archive SHA256:
`7dda60c8fa1f535d9e257eb2d04fdfde4643a92765eca8631bd766058240d8cb`.
The two mapped material samples were C029 zero-based nodes 24 and 25. Initial
Deep inventories were prescribed as `[100, 20] J`; base accessibility values
were `[0.4, 0.7]`. The 3-year tectonic path changed width by `0.344011586 m`;
the sampled endpoint temperatures were unchanged at displayed precision. Each
thermal step used one kernel substep.

| Case | Final Deep inventory (J, cell 0 / 1) | Cumulative net transport 0→1 (J) | Source (J) | Loss (J) | Synthetic e-fold time (years) |
|---|---:|---:|---:|---:|---:|
| Baseline | 87.707372 / 32.292628 | 12.292628 | 0 | 0 | 8.681 |
| Lower modal response at cell 1 | 99.583055 / 20.416945 | 0.416945 | 0 | 0 | 286.806 |
| Lower `zeta` at cell 1 | 87.707372 / 32.292628 | 12.292628 | 0 | 0 | 8.681 |
| Mobility 0.01/year | 98.296764 / 21.703236 | 1.703236 | 0 | 0 | 69.444 |
| Isolated, mobility 0/year | 100 / 20 | 0 | 0 | 0 | not applicable (zero coefficient) |
| Mobility 0.20/year | 74.437765 / 45.562235 | 25.562235 | 0 | 0 | 3.472 |
| Explicit geology source | 172.287347 / 42.385453 | 22.385453 | 94.672800 | 0 | 8.681 |
| Explicit geological loss | 82.693294 / 31.681171 | 11.681171 | 0 | 5.625535 | 8.681 |

All reported whole-system balance residuals were zero to `2.9e-14 J` and all
inventories remained finite and nonnegative. The source-only and loss-only
cases are separated; the e-fold times are calculated from the synthetic
linear two-cell transport closure, not observed natural relaxation times. The
accessibility-only case left
the stored energy exactly unchanged while changing accessible free-inventory
diagnostics from `[35.082950, 22.604840] J` to `[35.082950, 3.229263] J`.
The lower modal-response case slowed transport under the declared synthetic
law. The structural/thermal path changed `zeta` only through the explicitly
synthetic strain mapping (baseline cell values ended at `0.4000000124` and
`0.7000000217`); that tiny change is not a geological inference. The full
thermal state had an L-infinity temperature change of `0.0002191481 K` and
width change of `0.344011586 m`. These outcomes demonstrate sensitivity and bookkeeping of the selected
equations; they do not identify real geological concentrations, timescales,
or physical transitions.

Total elapsed time for eight cases was `0.05872 s`; Python `tracemalloc` peak was
`73,148 bytes` (not process RSS); the result JSON is `79,132 bytes`. The JSON
and its SHA256 are in
`outputs/r6_experimental_multiphysics/CANON_GUIDED_DEEP_PILOT_20261025_05/RESULT.json`
(`f81c4091cc0fd2941faface064f5ecc96d22b01e82195cc55d7d99858ccea430`).

## Verification and limits

Six new synthetic tests plus the existing seven tectonic–Deep baseline tests
passed: `13 passed`. The run is a two-cell engineering fixture on one archived
thermal initial state. It does not qualify Deep DFEU, modal parameters,
transport, geological source terms, solar input, geographic interpretation,
or coupled feedback. No long historical run, global simulation, Solver, MPI,
WORLD_HISTORY access, ledger update, commit, or push was performed.

The useful next integration is a real geology/material provider that binds
cell identities, composition/phase/strain and provenance to the existing
thermal state. Until such data and a calibrated material-to-mode closure exist,
the pilot's modal coefficients and Deep stocks must remain synthetic inputs.
