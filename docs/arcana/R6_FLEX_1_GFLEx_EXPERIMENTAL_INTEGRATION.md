# R6-FLEX-1 — gFlex experimental integration

**Scope:** optional external elastic-flexure adapter, genuine small gFlex
benchmarks, and a synthetic surface-routing handoff. This is engineering
evidence only; no physical ARCANA vertical response has been qualified.

## Result

- `GFLEX_NUMERICAL_BENCHMARK_PASS` — gFlex 1.3.0 F1D finite-difference solver
  executed on the synthetic 1-D load and agreed with an independently derived
  infinite-plate strip-load reference at the center to relative error
  `4.089376791612743e-4` (0.0409%).
- `GFLEX_ADAPTER_CONTRACT_READY` — the optional adapter and its tests bind load,
  mesh IDs, SI parameters, BCs, time key, provenance, solver version, and mesh,
  configuration, and result digests. It imports gFlex/NumPy lazily and rejects
  an unpinned gFlex version.
- `R6_SURFACE_FLEXURE_INTERFACE_DEMONSTRATED` — the actual gFlex F2D result was
  applied as the *difference* between two total-deflection fields to the
  existing regional evolution surface/routing code. The test grid is entirely
  synthetic; no R6 geographic elevation field was read or inferred. This tag
  means software-path demonstration only, not a real R6 surface integration.
- `PARTIAL__R6_GEOGRAPHIC_VERTICAL_RESPONSE_UNKNOWN` — no R6 load history,
  effective elastic thickness, lateral elastic plate mesh, suitable boundary
  domain, or validated mapping to the 3x3 synthetic basin was supplied.

## Repository inputs and authority

`regional_geological_evolution.py` provides a per-cell bookkeeping load
diagnostic from mass change, area, and gravity, explicitly not an isostatic or
lithostatic stress law. `geological_surface_microdomain.py` and
`hydrology_surface_coupling.py` contain the existing cover/surface and water
operators. `material_rheology_provider.py` supplies benchmark constitutive
values for a reduced mechanical model; it does not supply an ARCANA lithospheric
elastic thickness `Te` or flexural rigidity. The unified microdomain does not
currently consume a flexural solution.

The R6 material profiles provide role, density, heat capacity, conductivity,
radiogenic heating, temperature and material coordinates for their declared
supports. Those fields do not determine `E`, `nu`, `Te`, mantle-infill density
contrast, a 2-D load support, or flexural boundary conditions. The prior
regional 3x3 topography is synthetic. The C028/C029 T0 mapping is not used here
as a plate mesh or time-dependent load source. No lithology was inferred from
crust/mantle roles. Deep inventories and operators were not called or changed.

## Solver provenance and compatibility

The isolated Windows environment was created at the operator-authorized
temporary path `C:\Users\jose_\AppData\Local\Temp\arcana-r6-flex1-gflex-20261026`;
the repository and shared Python installation were not modified by package
installation. Runtime: Python 3.12.10, NumPy 2.5.4, SciPy 1.18.1, gFlex 1.3.0,
Windows 11. gFlex's stable PyPI release 1.3.0 declares Python >=3.10 and the
NumPy/SciPy/Matplotlib dependencies; the PyPI page identifies GPL-3.0-only and
reports a publishing attestation tied to upstream commit
`0841489b3a4211f2c91f76a9797a5c294fbec2e7`. The wheel SHA256 published by PyPI
is `7fd7f85d50634b78a355ba238e037ebe6b28a34a1b720be2c37e5c31056089ab`; that
wheel digest was not independently recalculated from the local pip cache.
No upstream source was copied into this repository.

Sources: [official PyPI release metadata](https://pypi.org/project/gflex/1.3.0/),
[upstream gFlex repository and license](https://github.com/awickert/gFlex), and
[upstream documentation](https://gflex.readthedocs.io/).

The adapter uses gFlex 1.3.0's actual `F1D`/`F2D` API and its legacy
capitalized instance fields (`Method`, `Solver`, `Te`, `BC_W`/`BC_E`, etc.). The
2.0.0 beta API shown by current documentation is not assumed interchangeable.
The external dependency is GPL-3.0-only; downstream distribution of a product
that combines/links it should receive a licensing review.

## 1-D benchmark

An actual gFlex `F1D`, finite-difference, direct sparse solve used 601 samples,
2,000 m spacing, a centered 11-sample uniform 1 MPa load, and clamped
displacement/slope boundaries. All constitutive parameters are synthetic:
`E=70 GPa`, `nu=0.25`, `Te=20 km`, `rho_m=3300 kg m-3`, `rho_fill=0`, and
`g=9.81 m s-2`. The half-domain is 600 km (about 12 derived 1-D flexural
parameters); its boundary is far from the center load for this benchmark.

| Quantity | Observed |
| --- | ---: |
| Derived `alpha_1D` | 49,799.8618 m |
| Analytic center deflection, infinite plate strip-load Green function | -6.72384709 m |
| gFlex center deflection | -6.72659672 m |
| Relative center error | 0.0409% |
| Max residual for exact 2x load scaling | 0 m |
| Center absolute response at `Te=30 km` | 4.99414257 m |
| Max pointwise difference, west edge changed to free-end BC | 0.000148416 m |

With gFlex's convention, negative `w` is downward. The increased `Te` reduced
the center deflection. Boundary-condition sensitivity was tested on the stated
finite domain; it does not establish a correct boundary choice for ARCANA.
Finite-difference, sign, finiteness and analytic checks passed. gFlex computes
instantaneous elastic equilibrium: the `time_s` field identifies load snapshots
and is not a time integrator.

## Synthetic 2-D surface handoff

The interface test matched the core of a 75x75 gFlex grid to the 3x3 synthetic
regional grid using 1 km square cells (1,000,000 m2 each), matching cell IDs and
row/column order. A 36-cell / 36 km synthetic halo surrounds the core. All four
outer boundaries are clamped. A prescribed synthetic surface mass sheet
`1.0e12 kg` over one 1 km2 cell gives `q=Δm*g/A=9.81e6 Pa`; it is an external
benchmark load and is not deposited in or removed from the regional sediment
stocks. The second snapshot doubles that load. No sediment, water or Deep stock
is converted to energy.

The 3x3 topography is deliberately almost flat and synthetic. The total
deflection from each solve is converted into an increment (`w_new-w_old`),
applied once to surface and bedrock, and recorded in the region's cumulative
vertical-flexure displacement so the existing geometry diagnostic closes. A
one-year regional step with zero precipitation then consumes the recalculated
drainage targets. The route map changed from
`{"0":-1,"1":0,"2":1,"3":0,"4":1,"5":8,"6":3,"7":8,"8":null}` to
`{"0":3,"1":4,"2":1,"3":4,"4":-1,"5":-1,"6":3,"7":4,"8":null}`.
This is a sensitivity/interface result, not a geological event.

The core geometry and resolution are explicitly equal to the synthetic
regional cells, but the 36 km halo is only about one 2-D flexural parameter for
these benchmark properties; fixed-boundary influence, particularly forebulge
suppression, remains significant. Consequently, the F2D result is **not** a
regional flexural prediction and must not be remapped onto R6 geography. The
regional step exercises drainage recomputation only; precipitation is zero and
there is no water flux. The Deep state is not present in this interface test.

## Final evidence bundle

`outputs/r6_flex1_gflex_20261026_05/` is the final run tied to the exact source
file hashes embedded in `RESULT.json` and repository HEAD `ddef4263...` before
this implementation. This rerun also includes the adapter cleanup guard around
gFlex initialization. It contains `RESULT.json` (659,682 bytes), its SHA256
sidecar (78 bytes), and `MANIFEST.json` (351 bytes), total 660,111 bytes.
Manifest SHA256: `7b6435f2880ed3f9b7c98d7ea1b9066726611774803e8ca1c5f1955d26526ceb`.
Result SHA256: `36e6a86973fb2dcc36b4d54a1f4ccde8ed8ba837ddbb5ed686f7a27a13d7de48`;
sidecar SHA256: `bb897de79296fbd75c655c6fb9b0248ec033aed9724324b90849289408e99d21`.
The two listed member hashes and byte counts were independently recalculated
locally and match; the manifest does not self-hash.

Runner elapsed time was 8.0950 s, including Python allocation tracing, JSON
construction, four 1-D cases, two 2-D solves, and result sealing. Individual
gFlex solves took 1.97–3.30 ms (1-D cases) and 61.20/64.35 ms (2-D loads). The
OS-reported process-lifetime peak working set was 148,623,360 bytes (includes
the interpreter and prior process allocations, not a measured experiment
delta). `tracemalloc` peak was 48,270,223 bytes and excludes NumPy/SciPy native
allocations. These are small local benchmark measurements, not resource
qualification.

Earlier same-task output directories are preserved: `_01` was left empty after
the solver calls completed but Windows RSS collection failed before result
sealing; `_02`, `_03`, and `_04` contain earlier/intermediate outputs. They are
not substitutes for the final `_05` bundle. Test temporary directories are
also left untouched under `outputs/`.

## Validation

Using the isolated runtime on Windows:

- gFlex numerical adapter tests plus regional, surface, hydrology, rheology and
  unified-microdomain regressions: **41 passed**.
- `py_compile` on the adapter, regional module, runner and test: PASS.
- `git diff --check`, UTF-8/LF and manifest/member/sidecar review: performed at
  final consolidation.

No Fair/Linux test, ASPECT run, long simulation, ShellSet/Solver, MPI, provider
evolution, WORLD_HISTORY access, or canonical publication occurred.

## Adapter contract and unresolved ARCANA inputs

The optional adapter contract accepts: solver/version; 1-D or 2-D mesh shape,
spacing and unique spatial IDs; load stress in Pa; `g`, mantle and fill density,
`E`, `nu`, `Te`, boundary conditions; snapshot time key; and caller-supplied
provenance. It returns signed deflection in metres, mesh/configuration/result
SHA256 identities and measured solver time. Load from a mass change is
`Δq=Δm*g/A`; positive stress is downward, negative mass change unloads. The
caller remains responsible for material identity, load authority, mesh
validity, and validating all source hashes.

Before use with R6, the project still needs a time-indexed surface load derived
from actual material/water histories, supported 2-D or 1-D geometry and
resolution, load/area mapping, an R6-supported `E`, `nu`, and `Te`/rigidity
model, mantle/fill density choices, defensible boundaries/padding, and a
temporal update rule for changing loads. `Te` cannot be inferred from lithosphere
depth or the existing creep law. This adapter does not replace hydrology,
thermal, tectonic, or Deep modules and is not yet called by the unified
multiphysics orchestrator.

All existing execution, SI1 mechanics, scientific, and canonical gates remain
closed, including `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
