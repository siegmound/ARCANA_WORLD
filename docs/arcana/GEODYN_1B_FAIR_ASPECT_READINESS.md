# GEODYN-1B — FAIR ASPECT runtime readiness package

Date: 2026-10-26
Branch: `r6/multiphysics-integration-20261026`
Preparation baseline: `48234eccc8b456a3a562ce956c87a96d2bc37603`
GEODYN-1A parent review: `docs/arcana/GEODYN_1A_FORWARD_DRIVER_PREPARATION.md`.

## Purpose and scope

This package enables an operator to determine, read-only, whether FAIR already provides an ASPECT runtime suitable for the **independent synthetic Blankenbach 1a benchmark**. It does not run ASPECT, install software, compile dependencies/plugins, access ARCANA providers, or authorize numerical work. The script prints observations to stdout; capture its output manually to a new external evidence directory after deciding the location. It creates no files and does not recursively search the filesystem; it reads only known `/proc`, `/sys/fs/cgroup`, home-filesystem and system package-index locations.

Script: `scripts/r6_geodyn1b_fair_runtime_preflight.sh`.

Expected operator command after the code is transferred to FAIR:

```bash
bash scripts/r6_geodyn1b_fair_runtime_preflight.sh
```

Use a fresh directory outside the repository, for example:
`$HOME/ARCANA_WORLD_EVIDENCE/R6/GEODYN_1B_ASPECT_READINESS/<UTC>_readiness/`.
The operator may save stdout and stderr there, preserving the preflight exit code and hashing the script/log. Never re-use a prior evidence directory. The script itself is strictly read-only; it is safe to direct output to the terminal.

## What the preflight observes

The script prints host OS/kernel/architecture; ASPECT path, version-query output, executable SHA256 and selected linked libraries; loaded/available relevant modules if the module command is already initialized; MPI launch/compiler tools, C/C++/Fortran compilers, make, CMake, Ninja and pkg-config versions; pkg-config and linker-cache visibility of deal.II, Trilinos, p4est, MPI and HDF5; explicit ASPECT/deal.II/Trilinos/p4est/CMake/source variables; and a bounded source-tree identity/status if `ASPECT_SOURCE_DIR` is already supplied.

It also records current-shell CPU count, RAM/swap, filesystem bytes/inodes for `$HOME`, `quota -s` availability, `ulimit`, visible scheduler allocation variables, and the current shell’s cgroup membership and readable limits along at most 12 known ancestors. It does not search for installations, query arbitrary directories, load modules, change environment, or infer a future job allocation from host totals. Cgroup values describe the current shell/session; a future scheduler job must be checked independently.

The preflight output must be preserved as operator-reported evidence until the original output is imported and independently hashed elsewhere. Absence of a command or unreadable limit is recorded as unavailable/UNKNOWN, not treated as unlimited.

## Version-matched Blankenbach 1a plan

The ASPECT 3.1.0 release is the current stable release identified in GEODYN-1A. The official 3.1.0 benchmark page identifies Blankenbach 1a as a 2D Cartesian case, provides reference statistics, states that its benchmark plugin must be built from the `plugin/` subfolder, and gives 72 reference timesteps at resolution level 3 ([ASPECT 3.1.0 benchmark documentation](https://aspect-documentation.readthedocs.io/en/stable/user/benchmarks/benchmarks/blankenbach/README.html)). The general documentation explains that such benchmark plugins are compiled as shared libraries and loaded by the case parameter file ([plugin benchmark workflow](https://aspect-documentation.readthedocs.io/en/stable/user/benchmarks/benchmark-run.html)).

Do not assume FAIR has 3.1.0. Apply this branch only after the read-only preflight reports a parseable version and a matching source tree:

1. Pin the exact ASPECT release/tag and full source revision. Require `ASPECT_SOURCE_DIR` or a separately acquired, hash-verified official source archive for that exact version. Do not combine the binary with a different release’s `.prm`, plugin, statistics script or reference data.
2. At the matching source revision, inspect and record the exact case-1a parameter file, level-3 resolution setting, termination criterion, postprocessors/statistics fields, plugin source/CMake files, and reference statistics. The stable 3.1.0 docs are a guide only; the checked-out release files control the run.
3. If that version’s case requires its plugin, compile it in a new isolated evidence/build directory using the **same ASPECT build configuration, deal.II, C++ compiler, MPI and ABI** as the installed binary. This is a build action and requires explicit authorization; do not alter a shared installation. If the exact version’s benchmark does not require compilation, record the source-level evidence for that fact.
4. Run only official Blankenbach case 1a with level-3 settings from the matching release, one MPI rank, using the release’s prescribed input and statistic-processing path. Do not shorten or modify the benchmark and still call it the official case. If a bounded partial run is authorized instead, classify it as a smoke test, not benchmark completion.
5. Use a new external evidence directory containing source/tag identity, binary path/hash/version, build and dependency versions, toolchain/MPI identity, exact `.prm` and plugin source/build hashes, command, environment, stdout/stderr, exit code, complete output manifest/hashes and parsed metric results. Preserve failed and partial outputs.

If the preflight detects a version other than 3.1.0, use **only** its matching official source/docs and benchmark files, first confirming the case, plugin requirement, level controls, statistics and reference values. If no matching source/reference package is present, runtime readiness remains blocked; do not substitute 3.1.0 benchmark inputs. Presence of an executable alone is not readiness.

## Acceptance and recorded metrics

For a complete benchmark run, independently parse the official output and record:

- natural exit and exit code; complete manifest membership/lengths/SHA256;
- each actual timestep and final model time, any failed/retried nonlinear/Stokes solve, convergence residuals and finite-value checks;
- Nusselt number and RMS velocity for the prescribed case, compared with the **version-matched official reference statistics** using that benchmark’s own published comparison method; report raw values and relative errors, do not invent a tolerance;
- level-3 result plus at least one neighboring refinement level if resources/authorization permit, to measure discretization trend rather than infer convergence from one mesh;
- stability of temperature, velocity, energy/source/surface-flux balance and sensitivity only to parameters varied by the benchmark;
- restart/continuation from an ASPECT checkpoint against continuous execution with identical release/configuration/rank count, reporting numerical differences;
- elapsed wall time, peak sampled RSS (label the sampling interval and process coverage), available scheduler/cgroup/job limits, output bytes, filesystem headroom and any polling gaps.

The official documentation says the case is advanced to steady state and notes that finer refinements may run a long time; 72 is a reference timestep count, **not** a duration/resource guarantee. No memory, runtime or storage budget is asserted from GEODYN-1A host observations.

## Local verification

The script passed `bash -n` using the pre-existing Git for Windows Bash. This verifies syntax only; the script has not been run against a Linux host, and no ASPECT runtime or Fair result is claimed. Documentation whitespace checks are recorded in the ledger update.

## Outcome branches

### ASPECT available and version/source match

Return the complete read-only evidence and classify `ASPECT_RUNTIME_PRESENT__BENCHMARK_BUILD_AND_RUN_NOT_AUTHORIZED`. Review exact binary/source/plugin compatibility and ask for a separate bounded authorization covering any plugin build and benchmark execution. Do not execute during this readiness phase.

### ASPECT absent or incompatible

Classify `ASPECT_RUNTIME_ABSENT_OR_VERSION_UNMATCHED__NO_INSTALL_PERFORMED`. First prefer an already-installed compatible FAIR runtime after operator/admin confirmation. Otherwise prepare an isolated, version-pinned user-space installation/build plan in a separate directory only after explicit approval of prerequisites, download source, disk/time resources and compilation; do not modify modules, shared software or environments here. If policy or resources prevent this, stop and keep ASPECT unqualified.

## Scientific and operational boundaries

Blankenbach coefficients, nondimensional scales and boundary conditions are solver-validation inputs only, not ARCANA material properties, Euler forcing, geological boundary conditions or initial state. No dry-olivine law is assigned to ARCANA. No ARCANA T0-to-T1 model, Fair job, ASPECT/ShellSet run, MPI benchmark, provider access or canonical publication occurred. All scientific gates remain unchanged, including `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.

## Official references

- [ASPECT 3.1.0 system prerequisites](https://aspect-documentation.readthedocs.io/en/v3.1.0/user/install/local-installation/system-prereqs.html)
- [ASPECT release list (3.1.0 stable)](https://github.com/geodynamics/aspect/releases)
- [ASPECT 3.1.0 Blankenbach benchmark](https://aspect-documentation.readthedocs.io/en/stable/user/benchmarks/benchmarks/blankenbach/README.html)
- [ASPECT 3.1.0 benchmark plugin workflow](https://aspect-documentation.readthedocs.io/en/stable/user/benchmarks/benchmark-run.html)
- [ASPECT 3.1.0 dependency/build requirements](https://github.com/geodynamics/aspect/releases)