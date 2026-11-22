# ARCANA R6 — FAIR MAGEMin / Perple_X fully no-sudo Conda installation

**Date:** 2026-11-22. **Purpose:** adapt the existing FAIR upstream-thermodynamic-execution pilot to a shared HPC workstation on which the user has **no sudo** and `julia` is not installed.  
**Decision:** `CONDA_ONLY_ISOLATED_THERMO_TOOLCHAIN__ORIGINAL_FAIR_RUNTIME_IMMUTABLE`  
**IMPORTANT:** the original preflight 35/640 has passed on **exact source** `393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2`, the real external programs **have not yet run**; the existing gate `scripts/r6_thermo_provider_run_official_fair.sh` is bound to that exact source SHA by the immutable preflight manifest.

## 1. Technical feasibility and scope

Conda-forge provides Linux-64 `julia=1.10.4`. The pinned `MAGEMin_C.jl v2.4.5` requires Julia 1.10 compatibility; Julia Pkg is a **second user-space package system inside an isolated Conda environment**, not a system install. Store `JULIA_DEPOT_PATH`, `Project.toml`, `Manifest.toml`, clone and Perple_X release files **under the new Conda environment prefix**. Do not modify `arcana-r6-linux` or the original R6 evidence, do not use `sudo` / `apt` / `snap` or global `~/.julia`.

The Perple_X official v7.3.3 release is a directly executable Linux tarball, not necessarily itself a Conda package: its installation **inside the user-owned Conda prefix** is user-space and satisfies this environment isolation requirement. If shared HPC policy forbids manually provided binaries even inside Conda, stop and ask the administrator; no bypass or unauthorized system change.

## 2. Create a new Conda env without disturbing FAIR R6

```bash
# From any initialized Conda shell. No sudo.
conda create -n arcana-thermo --override-channels -c conda-forge \
  julia=1.10.4 git curl libgfortran5 -y
conda activate arcana-thermo
which julia
julia --version  # expect 1.10.4
export THERMO_PREFIX="$CONDA_PREFIX"
test -x "$THERMO_PREFIX/bin/julia"
```

If Conda fails while solving, record the actual full error. Do **not** unpin Julia or alter the tested R6 conda environment without qualification. `conda list -n arcana-thermo` records the resolved dependency versions; freeze via `conda list -n arcana-thermo --explicit` after success.

## 3. Install the exact pinned MAGEMin Julia provider inside this Conda prefix

```bash
# Still in arcana-thermo
export JULIA_BIN="$THERMO_PREFIX/bin/julia"
export JULIA_PROJECT="$THERMO_PREFIX/arcana_magemin_julia"
export JULIA_DEPOT_PATH="$THERMO_PREFIX/julia_depot"
mkdir -p "$JULIA_PROJECT" "$JULIA_DEPOT_PATH"

"$JULIA_BIN" --project="$JULIA_PROJECT" -e '
using Pkg
Pkg.add(PackageSpec(
    url="https://github.com/ComputationalThermodynamics/MAGEMin_C.jl",
    rev="f4fd5ce3670b73693d046e65585e2b79d45c8e3a"))
Pkg.instantiate()
Pkg.status()
'

test -f "$JULIA_PROJECT/Manifest.toml"
"$JULIA_BIN" --project="$JULIA_PROJECT" -e 'using MAGEMin_C; println("MAGEMIN_PACKAGE_IMPORT_OK")'
sha256sum "$JULIA_PROJECT/Project.toml" "$JULIA_PROJECT/Manifest.toml"
```

`Pkg.add(PackageSpec(url=...,rev=...))` pins GitHub commit `f4fd5ce3670b73693d046e65585e2b79d45c8e3a`; the Julia Manifest pins the dependency graph. Julia package download requires outbound access; if blocked, report the registry/artifact URL and error instead of faking installation. The MAGEMin C backend is obtained through its `MAGEMin_jll` dependency.

**Note:** `JULIA_DEPOT_PATH` **must be exported again when returning to `arcana-r6-linux`** so the external Julia executable sees the same installed package/artifact depot. Launching Julia from another Conda env without that variable would otherwise look in a different depot and could falsely report the package missing.

## 4. Install pinned Perple_X Linux source + binary inside the Conda prefix

```bash
# Still in arcana-thermo
export PERPLEX_SOURCE="$THERMO_PREFIX/opt/Perple_X_source_v7.3.3"
export PERPLEX_INSTALL="$THERMO_PREFIX/opt/Perple_X_v7.3.3"
export PERPLEX_RELEASE_ARCHIVE="$THERMO_PREFIX/opt/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz"
mkdir -p "$THERMO_PREFIX/opt"

git clone --depth 1 --branch v7.3.3 \
  https://github.com/jadconnolly/Perple_X.git "$PERPLEX_SOURCE"
test "$(git -C "$PERPLEX_SOURCE" rev-parse HEAD)" = \
  "950d882bb6a9325a627109aa7154f7b526aa3087"

curl --fail --location --retry 3 \
  --output "$PERPLEX_RELEASE_ARCHIVE" \
  https://github.com/jadconnolly/Perple_X/releases/download/v7.3.3/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz

printf '%s  %s\n' \
  'ace6f81064c25709b401c3c49bc88410badad95fd7a876831c120eeed45f28e7' \
  "$PERPLEX_RELEASE_ARCHIVE" | sha256sum -c -

mkdir -p "$PERPLEX_INSTALL"
tar -xzf "$PERPLEX_RELEASE_ARCHIVE" -C "$PERPLEX_INSTALL"
find "$PERPLEX_INSTALL" -type f -name meemum

# Only when find returned exactly one executable:
export PERPLEX_MEEMUM="$(find "$PERPLEX_INSTALL" -type f -name meemum -print -quit)"
test -n "$PERPLEX_MEEMUM" && test -x "$PERPLEX_MEEMUM"
ldd "$PERPLEX_MEEMUM"
```

`ldd` must show no `not found` dependencies. If `libgfortran.so.5` or `libquadmath.so.0` cannot be resolved, inspect `$THERMO_PREFIX/lib/`, `ldd` and RPATH first. A process-local `LD_LIBRARY_PATH="$THERMO_PREFIX/lib:..."` *may* be necessary, but test it narrowly and do not globally inject it into the established `arcana-r6-linux` Python execution. The existing Perple_X runner independently extracts `meemum` bytes from the **SHA-verified** release archive and rejects an unrelated executable.

## 5. Return to FAIR's original Python env and run the original-source gate

```bash
# Variables remain in this shell after conda activation. If this is a new
# terminal/session, regenerate THERMO_PREFIX from the named env first.
conda activate arcana-r6-linux

export JULIA_BIN="$THERMO_PREFIX/bin/julia"
export JULIA_PROJECT="$THERMO_PREFIX/arcana_magemin_julia"
export JULIA_DEPOT_PATH="$THERMO_PREFIX/julia_depot"
export PERPLEX_SOURCE="$THERMO_PREFIX/opt/Perple_X_source_v7.3.3"
export PERPLEX_RELEASE_ARCHIVE="$THERMO_PREFIX/opt/Perple_X_v7.3.3_Linux_64_gfortran.tar.gz"
export PERPLEX_MEEMUM="$(find "$THERMO_PREFIX/opt/Perple_X_v7.3.3" -type f -name meemum -print -quit)"

cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git switch --detach 393ee8c1bf245758cfa2b1ca7864a7bd3a98d8c2
git status --short
"$JULIA_BIN" --version
"$JULIA_BIN" --project="$JULIA_PROJECT" -e 'using MAGEMin_C; println("MAGEMIN_PACKAGE_IMPORT_OK")'

# Runs REAL MAGEMin and Perple_X official source fixtures:
bash scripts/r6_thermo_provider_run_official_fair.sh
```

The preflight evidence already exists and its manifest contains `code_head_git_sha=393ee8c1...`; it will fail if you instead run the external script against the later integrated R6 HEAD. **Do not repeat** `scripts/r6_thermo_provider_pilot_fair_preflight.sh`: its NEW01 write-once outputs are already present and intentionally reject overwrite.

When the scientific executable test passes, it writes:

```text
/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/
  R6_THERMO_EXTERNAL_OFFICIAL_NEW01/
    MAGEMIN_JULIA_Manifest.toml
    MAGEMIN_OFFICIAL.toml
    MAGEMIN_STDOUT.log
    PERPLEX_BL691_MEEMUM/
    MANIFEST.json
```

**CAUTION:** the runner creates the output directory *before* invoking the engines; if any command fails, preserve the incomplete output as a failed attempt. Do not `rm -rf` or overwrite it simply to retry. A NEW02 run requires a separately versioned gate/disposition.

## 6. More demanding tests, only after real source fixture PASS

The user's permission to do heavier tests is recognized. Stage 2: ≥5 independent repeat runs, mass conservation and output stability. Stage 3: a **25-point P–T** grid only for a **verified common complete Earth chemistry** and controlled H2O/redox perturbations, with database/phase crosswalk. Initial MAGEMin `ig` examples and Perple_X `hp62ver.dat` reference are **different compositions, P/T, databases** and must not be ranked against each other. Details: `docs/arcana/R6_THERMO_PROVIDER_SCIENTIFIC_STRESS_PLAN_20261122.md`.

```text
NO_SUDO_OR_SYSTEM_PACKAGE_INSTALL = true
ORIGINAL_ARCANA_CONDA_ENV_MODIFIED = false
PINNED_EARTH_FIXTURE_INSTALLATION = PENDING_USER_FAIR_EXECUTION
PRE_EXISTING_SOFTWARE_FAIR_35_640 = PASS
MAGEMIN_EXTERNAL_EXECUTED = NOT_YET
PERPLEX_EXTERNAL_EXECUTED = NOT_YET
CROSS_PROVIDER_SCIENCE = NOT_AUTHORIZED
D_024 = ACTIVE
physical_T1 = null
WORLD_HISTORY_PRODUCTION_AUTHORIZED = false
```
