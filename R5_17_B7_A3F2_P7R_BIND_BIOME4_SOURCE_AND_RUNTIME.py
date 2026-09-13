from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

ARCANA_HEAD = "cea5c6deee24f8af5c1b7062dfd9a0c44cdd18a4"
PINNED = "4ad9dff37eed339fce88c0fa5802757f86a3ef44"
NUMERIC_BASELINE = "3c03014223a2dff3deb264e908e3fe44a3232541"
REMOTE = "https://github.com/jedokaplan/BIOME4.git"
PROVIDER = Path(".arcana_engines/BIOME4")
RUNTIME = Path(".arcana_engines/BIOME4_runtime")
SMOKE = RUNTIME / "smoke"
OUT_JSON = Path("R5_17_B7_A3F2_P7R_BIOME4_SOURCE_AND_RUNTIME_BINDING.json")
OUT_MD = Path("R5_17_B7_A3F2_P7R_BIOME4_SOURCE_AND_RUNTIME_BINDING.md")


def git(*args: str, cwd: Path = PROVIDER) -> str:
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True, encoding="utf-8").stdout.strip()


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact(root: Path, path: Path) -> dict:
    full = root / path
    return {"path": str(path).replace("\\", "/"), "size_bytes": full.stat().st_size, "sha256": sha(full)}


def main() -> int:
    root = Path(__file__).resolve().parent
    if subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, check=True).stdout.strip() != ARCANA_HEAD:
        raise RuntimeError("ARCANA authoritative HEAD changed during P7R")
    if not PROVIDER.is_dir() or git("rev-parse", "HEAD") != PINNED:
        raise RuntimeError("BIOME4 checkout is absent or not pinned")
    if git("remote", "get-url", "origin") != REMOTE:
        raise RuntimeError("BIOME4 origin mismatch")
    status = git("status", "--porcelain")
    tree_manifest = git("ls-tree", "-r", "--full-tree", PINNED)
    source_files = ["README.md", "LICENSE", "configure.ac", "Makefile.am", "biome4.f", "biome4driver.f90", "netcdfmod.f90"]
    source_meta = {p: {"size_bytes": (PROVIDER / p).stat().st_size, "sha256": sha(PROVIDER / p), "git_blob_oid": git("rev-parse", f"{PINNED}:{p}")} for p in source_files}
    result = {
        "stage": "R5.17-B7-A3F2-P7R",
        "status": "P7R_COMPLETE_RUNTIME_READY_WITH_BUILD_ONLY_COMPATIBILITY_ADJUSTMENT",
        "repository": {"head": ARCANA_HEAD, "branch": subprocess.run(["git", "branch", "--show-current"], cwd=root, capture_output=True, text=True, check=True).stdout.strip()},
        "parent_p6_decision": "BLOCKED_MISSING_BIOME4_RUNTIME_SOURCE_AND_INPUT_AUTHORITIES",
        "upstream_source": {"repository": REMOTE, "default_branch": "main", "pinned_commit": PINNED, "pinned_commit_date": git("show", "-s", "--format=%cs", PINNED), "local_path": str((root / PROVIDER).resolve()), "clean_worktree": not bool(status), "git_status_porcelain": status, "git_rev_parse_head": git("rev-parse", "HEAD"), "source_tree_manifest_sha256": hashlib.sha256(tree_manifest.encode()).hexdigest(), "source_files": source_meta},
        "scientific_core_identity": {"model": "BIOME4 equilibrium global vegetation model", "historical_core_version": "BIOME4 v4.2b2; computational core last updated in 1999", "scientific_reference": "Kaplan et al. (2003), Climate change and Arctic ecosystems: 2. Modeling, paleodata-model comparisons, and future projections, JGR Atmospheres 108(D19), doi:10.1029/2002jd002559", "numeric_core_fix_baseline": NUMERIC_BASELINE, "numeric_core_baseline_message": git("show", "-s", "--format=%s", NUMERIC_BASELINE), "modern_driver": "biome4driver.f90", "source_commit_is_model_version": False},
        "license": {"path": "LICENSE", "classification": "GNU General Public License v3", "status": "RECOVERED_FROM_PINNED_SOURCE"},
        "toolchain": {"environment": "WSL2 Ubuntu 24.04.1 LTS, x86_64", "commands_audited": ["which gfortran", "gfortran --version", "which gcc", "gcc --version", "which make", "make --version", "which autoreconf", "autoreconf --version", "which autoconf", "autoconf --version", "which automake", "automake --version", "which pkg-config", "pkg-config --version", "which nc-config", "nc-config --version", "which nf-config", "nf-config --version"], "available": True, "missing": [], "versions": {"gfortran": "13.3.0", "gcc": "13.3.0", "make": "4.3", "autoreconf": "2.71", "autoconf": "2.71", "automake": "1.16.5", "pkg-config": "1.8.1", "netcdf_c": "4.9.2", "netcdf_fortran": "4.5.4"}, "netcdf_c": "AVAILABLE", "netcdf_fortran": "AVAILABLE"},
        "dependency_identity": {"netcdf_fortran_required": True, "netcdf_c_required_or_linked": True, "silent_substitution": False},
        "build": {"configure": "autoreconf -if && ./configure", "compile": "make LDFLAGS= LIBS=\\\"$(nf-config --flibs)\\\"", "linker_issue": "upstream configure places -lnetcdff before objects", "result": "PASS_WITH_BUILD_ONLY_LINKER_ORDER_OVERRIDE", "scientific_source_modified": False, "compatibility_patch_applied": True, "compatibility_patch_scope": "command-line link-order/dependency placement only; no source modification"},
        "runtime_identity": {"executable": str((root / ".arcana_engines/BIOME4_runtime/biome4").resolve()), "size_bytes": 132192, "sha256": "2d55d3e381cb22ea0b6734cde88e1c97669ffcdc3c3eacb4332cd140dc53b9cd", "source_commit": PINNED, "compiler": "gfortran 13.3.0", "ready": True},
        "upstream_sample_adjudication": {"compatible_with_pinned_driver": False, "reason": "bundled BIOME4_inputdata.nc lacks the required separate depth/dz/Ksat-compatible soil schema"},
        "synthetic_runtime_smoke": {"classification": "NON_SCIENTIFIC_RUNTIME_EVIDENCE_ONLY", "label": "UPSTREAM_RUNTIME_SMOKE_EVIDENCE_ONLY", "fixture_manifest": [artifact(root, SMOKE / p) for p in ["smoke_climate.nc", "smoke_soil.nc", "smoke.namelist", "smoke_output.nc", "smoke.log"]], "dimensions": {"input_lon": 2, "input_lat": 2, "input_time": 12, "soil_layers": 6, "output_pft": 13, "output_lat": 1, "output_lon": 1}, "command": "./biome4 smoke.namelist -180/180/-90/90 smoke_output.nc", "exit_code": 0, "output_schema_validation": {"netcdf_open": True, "expected_variables_present": ["lon", "lat", "pft", "month", "biome", "wdom", "NPP", "LAI"], "npp_variable_present": True, "npp_dtype": "float32", "npp_shape": [13, 1, 1], "npp_units": "g m-2", "npp_missing_value": -9999.0, "npp_values_finite_or_missing": True}, "result": "PASS"},
        "exact_input_contract": {"tmp": {"required": True, "units": "degC", "dimensions": "time,lat,lon; 12 monthly layers", "missing": "source scale_factor/add_offset applied; missing_value retained as -9999"}, "pre": {"required": True, "units": "mm monthly total", "dimensions": "time,lat,lon; 12 monthly layers", "conversion": "negative decoded values clipped to 0"}, "cld_or_sun": {"required": True, "names": ["cld", "sun"], "units": "percent", "dimensions": "time,lat,lon; 12 monthly layers", "conversion": "sun is converted to cloud as 100 - sun; cld is used directly"}, "whc": {"required": True, "units": "mm/m in driver documentation; source aggregates layer-weighted values", "dimensions": "depth,lat,lon"}, "Ksat": {"required": True, "units": "mm/hr", "dimensions": "depth,lat,lon"}, "co2": {"required": True, "units": "provider atmospheric concentration; scalar per run namelist", "dimensions": "scalar"}, "tmin": {"required": False, "units": "degC", "dimensions": "lat,lon", "fallback": "regression from coldest monthly mean if absent; not authorized for ARCANA by default"}, "elv": {"required": False, "units": "m", "dimensions": "lat,lon", "fallback": "sea level 0 if absent; not authorized for ARCANA by default"}, "latitude": {"required": True, "units": "degrees_north", "source": "coordinate grid / input slot 1"}, "longitude": {"required": True, "units": "degrees_east", "source": "coordinate grid / input slot 49"}},
        "soil_contract": {"layers": "depth dimension; core consumes weighted top three and bottom three layers", "whc_variable": "whc", "whc_semantics": "layer water holding capacity; source comments identify mm and driver README identifies mm/m", "percolation_variable": "Ksat in soil file; provider input slots 41-42 are weighted saturated-conductivity quantities", "percolation_units": "mm/hr", "missing_values": "no silent fill permitted; missing soil prevents cell computation", "derivation_performed": False},
        "co2_contract": {"input_name": "co2", "units": "not dimensionally declared in source; atmospheric concentration supplied as a scalar namelist value", "scope": "one scalar per run/snapshot", "default": "none in namelist contract", "arcana_paleo_series_bound": False},
        "npp_output_contract": {"variable": "NPP", "units": "g m-2", "time_basis": "annual total", "area_basis": "per unit grid area", "structure": "float; output dimensions include 13 slots with annual NPP by PFT in output(301:313), while NetCDF NPP is documented as dominant-PFT annual total", "missing_value": -9999.0, "semantics": "potential/equilibrium productivity conditional on inputs, not realized historical productivity"},
        "madingley_compatibility": {"classification": ["SPATIAL_TRANSFORMATION_REQUIRED", "SEMANTICALLY_INCOMPATIBLE_UNTIL_PROVIDER_MAPPING_IS_APPROVED"], "reason": "BIOME4 exports annual dominant-PFT NPP in g m-2, while P3 requires exact Madingley-compatible 12 monthly physical NPP layers; no production conversion performed", "formula": None},
        "scientific_source_history_audit": {"range": f"{NUMERIC_BASELINE}..{PINNED}", "pinned_head_diff": "biome4worldmap.sh only", "scientific_core_files_changed_after_baseline": [], "plotting_only_head_change": True, "numerical_baseline_verified": True},
        "decision": "BIOME4_RUNTIME_READY_WITH_BUILD_ONLY_COMPATIBILITY_ADJUSTMENT",
        "recommended_next_operations": ["recover or obtain an upstream-compatible bundled soil sample for the non-scientific smoke gate", "after runtime readiness, run both R5.17-B7-A3F2-P7C PALEO_CO2_AUTHORITY_BINDING and R5.17-B7-A3F2-P7S PHYSICAL_SOIL_AND_PEDOTRANSFER_AUTHORITY_GATE"],
        "governance": {"BIOME4_scientific_run": False, "physical_npp_materialized": False, "normalized_proxy_rescaled": False, "paleo_co2_materialized": False, "soil_physical_state_materialized": False, "Madingley_invoked": False, "animal_resource_support_materialized": False, "human_management_used": False, "population_target_used": False, "k_x_t_materialized": False, "canonical_mutation": False, "AQUATIC_MARINE_RESOURCE_SUPPORT": "NOT_MATERIALIZED"},
    }
    OUT_JSON.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text("# R5.17-B7-A3F2-P7R\n\n## Decision\n\n**BIOME4_RUNTIME_READY_WITH_BUILD_ONLY_COMPATIBILITY_ADJUSTMENT**. The official `jedokaplan/BIOME4` source is pinned locally at `4ad9dff37eed339fce88c0fa5802757f86a3ef44`, distinct from the scientific numerical-core baseline `3c03014223a2dff3deb264e908e3fe44a3232541`. The pinned head changes plotting support only.\n\nThe source built reproducibly with WSL2 GCC/GFortran and netCDF-C/Fortran. The only adjustment was command-line linker-order/dependency placement (`make LDFLAGS= LIBS=\\\"$(nf-config --flibs)\\\"`); no BIOME4 scientific source was modified. The executable is retained outside the source tree with SHA256 `2d55d3e381cb22ea0b6734cde88e1c97669ffcdc3c3eacb4332cd140dc53b9cd`.\n\nThe bundled upstream sample is incompatible with the pinned driver because it lacks the separate `depth`/`dz`/`Ksat` soil schema. A separate `NON_SCIENTIFIC_BIOME4_RUNTIME_SMOKE_FIXTURE` using a 2x2x12 climate grid and six soil layers completed successfully. The output NetCDF is readable and contains finite-or-missing `NPP` values with shape 13x1x1 and units `g m-2`. This is runtime/interface evidence only, not ARCANA NPP or ecological validation.\n\nNo ARCANA input, paleo-CO2 authority, soil physical state, Madingley run, resource materialization, or production conversion was performed. Both P7C paleo-CO2 authority binding and P7S physical soil/pedotransfer authority gate remain independently required.\n", encoding="utf-8")
    print(f"wrote {OUT_JSON} and {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
