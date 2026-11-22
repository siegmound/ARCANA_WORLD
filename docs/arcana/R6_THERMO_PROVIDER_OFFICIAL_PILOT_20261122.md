> **FAIR shared-HPC installation update (2026-11-22): NO SUDO / CONDA ONLY.**
> User's FAIR workstation has no `julia` command and no system package installation permission.
> Julia 1.10.4 is available as a conda-forge `linux-64` package; create separate
> `arcana-thermo` Conda env, install user-space MAGEMin_C.jl and Perple_X
> inside that environment prefix, then run the original FAIR gate from the
> **unchanged** `arcana-r6-linux` Python environment and exact tested SHA
> `393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2`. Do NOT attempt `sudo`,
> `apt` or `snap`. Exact documented procedure:
> [R6_THERMO_PROVIDER_FAIR_NO_SUDO_CONDA_RUNBOOK_20261122.md](R6_THERMO_PROVIDER_FAIR_NO_SUDO_CONDA_RUNBOOK_20261122.md).
> The preflight 35/640 has already passed; do NOT rerun the write-once NEW01 preflight.

# ARCANA R6 — First replaceable thermodynamics-provider pilot

**Date:** 2026-11-22. **Scope:** external Earth scientific-tool benchmark **stage 0 (official upstream fixtures)**.  
**Decision:** `UPSTREAM_PINNED_THERMO_PROVIDER_SMOKES_READY__CROSS_SOLVER_SCIENCE_PENDING`.  
**No real ARCANA source lithology:** `D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; no WorldHistory or HistoryStore changes.

## Scientific objective and what we do NOT claim

ARCANA is a science-tool orchestrator. No FAIR-certified solver is privileged if external code is more scientifically defensible, easier to maintain or more accurate. We must first **prove each external engine operates and reproduces its own official scientific fixture on FAIR** before attempting numerical cross-validation.

This stage separates **upstream verification** from **actual cross-tool comparability**:

1. MAGEMin_C.jl upstream Examples 1 and 2: standalone Earth's igneous thermodynamic database (`ig`) exercises. Quantities are P in **kbar**, T in **°C**, system chemistry as reported; output has a solver status, phase names, mass fractions and density.
2. Perple_X upstream **fast** `bl691_MEEMUM` unit test: 1050 **K**, 4000 **bar**, official BL478 example, `hp62ver.dat` and solution model from the exact official source tag. Extract P, T and all phase `wt %` from the `.prn` and compare against the original source-tagged `.prn`. This is a source numerical check, not identical to MAGEMin's igneous cases.
3. GeoParams.jl **v0.10.0** remains **not executed** during the phase-equilibria step: the 2026-10-27 release introduced corrections to Peierls, diffusion, dislocation and other creep parameters, changed water fugacity convention to Pa and the grain size handling; baseline must be pinned when subsequent reology comparison is designed.
4. **NO direct MAGEMin–Perple_X science ranking** from these fixtures: they use different bulk chemistry, different T and P and different thermodynamic/solution databases. Even the MAGEMin predefined KLB1 and the Perple_X `klb691` *name* do not prove equal chemistry, iron valence or model calibration. `pilot.comparable_pair` refuses to compare until explicit consistent P, T, oxide component basis and redox/water state, chemical system, thermodynamic model crosswalk and phase-name crosswalk are provided and independently checked.

No composition or result is taken as natural ARCANA rock, mantle, fluid, resource, Deep or spatial placement.

## Verified upstream pins (GitHub official API checked 2026-11-22)

| Provider | Version | Immutable commit | License metadata | Evidence |
|---|---|---|---|---|
| MAGEMin_C.jl | v2.4.5 | `f4fd5ce3670b73693d046e65585e2b79d45c8e3a` | GitHub repo GPL-3.0 | `Project.toml` Git blob `d75b3a13e95e217ddff656dce2a0e26cda6e0db3`; Julia 1.10 compatibility |
| Perple_X | v7.3.3 | `950d882bb6a9325a627109aa7154f7b526aa3087` | GitHub repo GPL-3.0 | Linux `Perple_X_v7.3.3_Linux_64_gfortran.tar.gz`, published SHA256 `ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7` |
| GeoParams.jl | v0.10.0 | `5be510f50614774a20eb98856c1ca7c197984a4a` | GitHub repo MIT | Annotated release tag SHA `95aee41f8d582363e9abf1b962f0ba01f5a22464` |

License metadata is **not** a complete legal review of thermodynamic datasets, separate data-file licenses, linked libraries or redistribution; check the actual release files/license terms before distribution.

Official references:

- https://github.com/ComputationalThermodynamics/MAGEMin_C.jl/tree/v2.4.5 (README examples 1/2, output fields `out.ph`, `out.ph_frac_wt`, `out.rho`, `out.status`).
- https://github.com/jadconnolly/Perple_X/tree/v7.3.3/test/bl691_MEEMUM ; `README_tests.txt` classifies this as the *fast* single-point reference compared to slower 10–20 minute phase-section tests.
- https://github.com/jadconnolly/Perple_X/releases/tag/v7.3.3 ; official Linux release archive/digest.
- https://github.com/JuliaGeodynamics/GeoParams.jl/releases/tag/v0.10.0 ; critical constitutive parameter changes.

## A. FAIR source/contract preflight — NO external execution

At the exact isolated branch SHA, on FAIR `arcana-r6-linux`, from clean repo root:

```bash
bash scripts/r6_thermo_provider_pilot_fair_preflight.sh
```

Expected **35 new targeted**, **640 selected** including the 35 (original R6 selected 605), plus JSON registry validation. New external **write-once** artifacts:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
    R6_THERMO_PROVIDER_PILOT_TARGET_35_NEW01.log
    R6_THERMO_PROVIDER_PILOT_SELECTED_640_NEW01.log
    R6_THERMO_PROVIDER_PILOT_PREFLIGHT_NEW01/
        PREFLIGHT.json
        MANIFEST.json
```

**IMPORTANT:** preflight prints `THERMO_EXTERNAL_MAGEMIN_EXECUTIONS=NOT_RUN` and `THERMO_EXTERNAL_PERPLEX_EXECUTIONS=NOT_RUN`. Passing 640 selected tests certifies the adapter/guards and old regression only, **not** the scientific engines.

## B. Isolated external engine installation, source and artifact pins

Do **not** install packages into the existing `arcana-r6-linux` conda environment or change existing T0 source files. On FAIR choose a separate directory, e.g.:

```bash
TOOLS=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6_TOOL_ENV
mkdir -p "$TOOLS"
```

Install **Julia 1.10 or newer** through an official Julia distribution (not assumed present; exact Julia version must appear in evidence). With the official Julia executable in PATH, create a separate project **outside the R6 source tree** and pin the upstream exact MAGEMin commit:

```bash
mkdir -p "$TOOLS/julia_magemin"
julia --project="$TOOLS/julia_magemin" -e '
using Pkg
Pkg.add(PackageSpec(url="https://github.com/ComputationalThermodynamics/MAGEMin_C.jl", rev="f4fd5ce3670b73693d046e65585e2b79d45c8e3a"))
Pkg.instantiate()
'
```

Save/retain both `Project.toml` and `Manifest.toml`, with SHA256 recorded. MAGEMin_C `v2.4.5` requires Julia 1.10 compatibility and its C library/JLL dependencies; do not assume correct installation merely because `julia --version` succeeds.

Obtain the Perple_X **exact v7.3.3** release binary and original source tag outside the R6 repo:

```bash
git clone --depth 1 --branch v7.3.3 https://github.com/jadconnolly/Perple_X.git "$TOOLS/Perple_X_source_v7.3.3"
[ "$(git -C "$TOOLS/Perple_X_source_v7.3.3" rev-parse HEAD)" = "950d882bb6a9325a627109aa7154f7b526aa3087" ] || exit 1
curl -fL --retry 3 -o "$TOOLS/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz" \
  https://github.com/jadconnolly/Perple_X/releases/download/v7.3.3/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz
printf '%s  %s\n' 'ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7' "$TOOLS/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz" | sha256sum -c -
mkdir -p "$TOOLS/Perple_X_v7.3.3"
tar -xzf "$TOOLS/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz" -C "$TOOLS/Perple_X_v7.3.3"
find "$TOOLS/Perple_X_v7.3.3" -type f -name meemum
```

Choose the returned absolute `meemum` path; **verify it is an installed binary from the pinned archive**. Repository license metadata is not a redistribution clearance for datafiles.

## C. Execute real official test engines only after A and B

Set paths to the verified isolated installations and run the separate **write-once** engine gate from the same exact clean checkout:

```bash
export JULIA_BIN="$(command -v julia)"
export JULIA_PROJECT="$TOOLS/julia_magemin"
export PERPLEX_SOURCE="$TOOLS/Perple_X_source_v7.3.3"
export PERPLEX_RELEASE_ARCHIVE="$TOOLS/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz"
export PERPLEX_MEEMUM="/absolute/path/from/find/meemum"
bash scripts/r6_thermo_provider_run_official_fair.sh
```

This writes `R6_THERMO_EXTERNAL_OFFICIAL_NEW01` with native MAGEMin `TOML`/stdout and Julia `Manifest`, Perple_X native `.prn` and run log, each input-file hash and tool-version/asset hashes, and an SHA256 audit manifest. MAGEMin's two samples run at **8 kbar/800°C** and **10 kbar/1100°C**; Perple_X's fast test is **4000 bar/1050 K**. Never normalize away the official custom-MAGEMin 99.75 wt.% as-reported sum or silently transform FeO/Fe2O3 or H2O.

If runtime is missing, fails to converge or differs from its official source reference: **preserve the failing NEW01 output and original logs**; do not relabel as PASS or promote. A retry requires a separate NEW02 path and a code/evidence disposition.

## D. True scientific cross-provider benchmark (next *after* C)

1. Select an independently sourced, fully described **terrestrial** bulk composition and assign its oxidation/redox/H2O state and uncertainties. No link to ARCANA crust parent yet.
2. Choose thermodynamic database and model/phase crosswalks covering that chemistry in both tools. Compare the **compatible component sets**, not merely database acronyms. Define one explicit P, T and fluid/redox state with documented units.
3. Execute both on the same case; publish raw phase masses, melt/fluid fractions, density, independent mass balance, uncertainty and computation time. Use a model-form difference audit if database models legitimately differ; differing results are not by themselves bugs.
4. Only then test a **noncanonical original T0 8×8 region hypothesis**. Original regional PRE overburden is Δσv, not automatically an admissible absolute thermodynamic pressure. No source mineral/phase/fault-side identity or fluid pressure is invented.
5. Evaluate GeoParams v0.10.0/ASPECT for mechanism-scoped T/P/rate/water reology after mineralogy, not before. Do not automatically connect strain-rate to Perple_X mineral percentages without independently supported material laws.

**Exit status at code publication:** 35 portable contract tests locally PASS, FAIR preflight **PENDING**, neither external engine installed or run in authoring runtime, exact benchmark outputs NOT YET AVAILABLE, and no physical T1 or canonical geological changes authorized.
