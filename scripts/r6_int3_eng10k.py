#!/usr/bin/env python3
"""INT-3 ENG10K preflight and separately authorized noncanonical runner."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from arcana_worldsim.r6.functional_development import (  # noqa: E402
    initial_reduced_state, pure_shear_thermal_step,
)
from arcana_worldsim.r6.int0a_pipeline import prepare_pair_5_11  # noqa: E402
from arcana_worldsim.r6.int3_eng10k import (  # noqa: E402
    MAX_PROJECTED_OUTPUT_BYTES, R4_KERNEL_SHA256, R4_SUPPORT_IDS,
    RESOLUTION_FACTORS, SECONDS_PER_YEAR, Eng10kContractError,
    advance_with_bounded_samples, canonical_bytes, compare_reduced_states,
    load_r4_continuation_bundle, provider_component_bindings_match, sha256_bytes,
)

CONFIG_PATH = ROOT / "configs/r6_int3_eng10k/engineering_case.json"
R4_BUNDLE = ROOT / "outputs/r6_functional_development/INT0B_TF2B_5_11_R4_20261013_04"
OUTPUT_RELATIVE = Path("outputs/r6_functional_development/INT3_ENG10K_5_11_DIRECT_RESTART_20261014_01")
SUPERVISION_RELATIVE = Path("outputs/r6_functional_development/INT3_ENG10K_SUPERVISION_20261014_01")
EXPECTED_EXTERNAL_ROOT_SUFFIX = "_ARCANA_EXTERNAL_SOURCES"
EXPECTED_KERNEL_SHA256 = R4_KERNEL_SHA256
EXECUTION_DECISION = "CONDITIONAL_GO_INT3_ENG10K_NONCANONICAL_RUN"
CONFIG_SHA256 = "3f3d3dc6d6ad28a31fdb7f350eedfe971a63708ad0f0f63f2d97e49b4e474f3e"
EXECUTION_SOURCE_PATHS = (
    "configs/r6_int3_eng10k/engineering_case.json",
    "scripts/r6_int3_eng10k.py",
    "scripts/r6_int3_eng10k_supervisor.py",
    "src/arcana_worldsim/r6/int3_eng10k.py",
    "src/arcana_worldsim/r6/functional_development.py",
)


def _git(root: Path, *args: str) -> str:
    env = dict(os.environ)
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    result = subprocess.run(["git", "-C", str(root), *args], env=env,
                            capture_output=True, text=True, check=False, timeout=15)
    if result.returncode:
        raise Eng10kContractError(f"GIT_QUERY_FAILED:{' '.join(args)}")
    return result.stdout.strip()


def _text_hash(path: Path) -> str:
    data = path.read_bytes().decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()
    return hashlib.sha256(data).hexdigest()


def _verify_current_kernel() -> dict[str, str]:
    current = _text_hash(ROOT / "src/arcana_worldsim/r6/functional_development.py")
    env = dict(os.environ)
    env.pop("GIT_OBJECT_DIRECTORY", None)
    env.pop("GIT_ALTERNATE_OBJECT_DIRECTORIES", None)
    historical = subprocess.run(
        ["git", "-C", str(ROOT), "show",
         "91fc83d50ec15d8bb9b826926ac2f2dc859281e8:src/arcana_worldsim/r6/functional_development.py"],
        env=env, capture_output=True, check=False, timeout=15,
    )
    historical_hash = hashlib.sha256(historical.stdout.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n").encode()).hexdigest()
    if historical.returncode or current != EXPECTED_KERNEL_SHA256 or historical_hash != EXPECTED_KERNEL_SHA256:
        raise Eng10kContractError("HISTORICAL_KERNEL_IDENTITY_UNVERIFIED")
    return {"r4_historical_kernel_sha256": historical_hash,
            "current_kernel_sha256": current}


def _configuration() -> tuple[dict[str, object], bytes, str]:
    raw = CONFIG_PATH.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    if actual_sha != CONFIG_SHA256:
        raise Eng10kContractError("ENGINEERING_CONFIG_IDENTITY_MISMATCH")
    config = json.loads(raw)
    expected = {
        "schema": "ARCANA_R6_INT3_ENG10K_CASE_V1",
        "experiment_id": "R6-INT3-ENG10K-A",
        "scope": "NONCANONICAL_ENGINEERING_STRESS_TEST",
        "ordered_plate_pair": [5, 11], "r4_boundary_id": "R6BND-T0-3eb57747e6f0a3f3305f",
        "r4_support_ids": list(R4_SUPPORT_IDS), "initial_age_ma": 210.0,
        "elapsed_duration_years": 10000.0, "r4_checkpoint_elapsed_years": 1000.0,
        "restart_additional_duration_years": 9000.0,
        "frozen_euler_extension_m_per_year": 0.11467052868814648,
        "resolution_factors": list(RESOLUTION_FACTORS), "reference_resolution_factor": 0.0005,
        "diagnostic_resolution_factor": 0.0005, "canonical_publication": False,
    }
    for key, value in expected.items():
        if config.get(key) != value:
            raise Eng10kContractError(f"ENGINEERING_CONFIG_PIN_MISMATCH:{key}")
    return config, raw, actual_sha


def _preflight(output_relative: Path = OUTPUT_RELATIVE,
               supervision_relative: Path = SUPERVISION_RELATIVE,
               r4_bundle: Path = R4_BUNDLE, *, allow_existing_supervision: bool = False) -> dict[str, object]:
    if platform.python_version() != "3.12.10":
        raise Eng10kContractError("PYTHON_RUNTIME_IDENTITY_MISMATCH")
    import numpy as np
    if np.__version__ != "2.3.5":
        raise Eng10kContractError("NUMPY_RUNTIME_IDENTITY_MISMATCH")
    external_root = os.environ.get("ARCANA_EXTERNAL_ROOT")
    if (not external_root or not Path(external_root).is_dir()
            or not Path(external_root).name.endswith(EXPECTED_EXTERNAL_ROOT_SUFFIX)):
        raise Eng10kContractError("GOVERNED_EXTERNAL_ROOT_UNAVAILABLE_OR_UNEXPECTED")
    if any(os.environ.get(key) for key in ("GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES")):
        raise Eng10kContractError("INVALID_GIT_OBJECT_ENVIRONMENT")
    branch = _git(ROOT, "branch", "--show-current")
    head = _git(ROOT, "rev-parse", "HEAD")
    if branch != "r6/si1-bandwidth-f2av":
        raise Eng10kContractError("SOURCE_BRANCH_MISMATCH")
    changed = _git(ROOT, "status", "--porcelain=v1", "--", *EXECUTION_SOURCE_PATHS)
    if changed:
        raise Eng10kContractError("ENG10K_SOURCE_OR_CONFIGURATION_NOT_COMMITTED_CLEAN")
    output = (ROOT / output_relative).resolve()
    supervision = (ROOT / supervision_relative).resolve()
    allowed = (ROOT / "outputs/r6_functional_development").resolve()
    if any(allowed not in path.parents for path in (output, supervision)) or output == supervision:
        raise Eng10kContractError("OUTPUT_PATH_OUTSIDE_ISOLATED_ROOT")
    if output.exists() or (supervision.exists() and not allow_existing_supervision):
        raise Eng10kContractError("OUTPUT_OR_SUPERVISION_PATH_ALREADY_EXISTS")
    if allow_existing_supervision and not supervision.is_dir():
        raise Eng10kContractError("SUPERVISION_EVIDENCE_DIRECTORY_UNAVAILABLE")
    config, config_raw, config_sha = _configuration()
    kernel = _verify_current_kernel()
    r4 = load_r4_continuation_bundle(r4_bundle)
    plan = prepare_pair_5_11(ROOT, expected_branch=branch, boundary_id=r4.boundary_id)
    if (plan.support_ids != r4.support_ids or plan.selected_section.get("boundary_id") != r4.boundary_id
            or plan.signed_extension_m_per_year != r4.forcing_m_per_year
            or plan.assessment.get("source_head") != head
            or not provider_component_bindings_match(
                plan.provider_identities, r4.provider_identities)):
        raise Eng10kContractError("CURRENT_PROVIDER_AUDIT_DIFFERS_FROM_R4_BINDING")
    derived_initial = tuple(initial_reduced_state(p, initial_width_m=plan.initial_width_m)
                            for p in plan.profiles)
    if tuple(s.payload() for s in derived_initial) != tuple(s.payload() for s in r4.initial_states):
        raise Eng10kContractError("CURRENT_PROVIDER_PROFILE_DIFFERS_FROM_R4_INITIAL_STATE")
    if MAX_PROJECTED_OUTPUT_BYTES > 512 * 1024 * 1024:
        raise Eng10kContractError("PROJECTED_OUTPUT_EXCEEDS_MONITORED_BUDGET")
    return {
        "decision": "INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION",
        "repository_branch": branch, "source_head": head,
        "source_worktree_cleanliness": "ENG10K_SOURCE_AND_CONFIGURATION_CLEAN_AT_PREFLIGHT",
        "kernel_identity": kernel, "runtime": {"python": platform.python_version(), "numpy": np.__version__},
        "external_root": str(Path(external_root).resolve()),
        "r4_manifest_sha256": r4.manifest_sha256,
        "r4_historical_source_composite_sha256":
            r4.source_identity.get("r4_source_composite_sha256"),
        "current_source_composite_sha256": plan.assessment.get("source_identity_sha256"),
        "source_composite_identity_includes_current_head": True,
        "historical_provider_component_identities_match": True,
        "r4_checkpoint_time_s": r4.checkpoint_states[0].time_s,
        "r4_boundary_id": r4.boundary_id, "support_ids": list(r4.support_ids),
        "frozen_euler_m_per_year": r4.forcing_m_per_year,
        "provider_identity": dict(plan.provider_identities),
        "configuration_sha256": config_sha,
        "direct_duration_years": config["elapsed_duration_years"],
        "restart_additional_duration_years": config["restart_additional_duration_years"],
        "resolution_factors": list(RESOLUTION_FACTORS),
        "diagnostic_sample_interval_years": config["diagnostic_retention"]["schedule_interval_years"],
        "maximum_retained_samples_per_support": config["diagnostic_retention"][
            "maximum_retained_samples_per_support"],
        "projected_output_upper_bound_bytes": MAX_PROJECTED_OUTPUT_BYTES,
        "output_relative": output_relative.as_posix(),
        "supervision_relative": supervision_relative.as_posix(),
        "monitored_limits_not_os_quotas": {"wall_seconds": 900,
            "process_tree_rss_bytes": 2_147_483_648, "cumulative_output_bytes": 536_870_912},
        "numerical_evolution_executed": False,
        "canonical_publication": False,
    }


def _write_bundle(output: Path, artifacts: dict[str, object], config_raw: bytes,
                  preflight: dict[str, object], result: dict[str, object]) -> dict[str, object]:
    if not output.is_dir() or set(p.name for p in output.iterdir()) != {"RUN_STARTED.json"}:
        raise Eng10kContractError("OUTPUT_COLLISION_OR_UNEXPECTED_PARTIAL_CONTENT")
    manifest_files: dict[str, dict[str, object]] = {}
    try:
        values: dict[str, bytes] = {"engineering_case.json": config_raw,
                                    "RUN_STARTED.json": (output / "RUN_STARTED.json").read_bytes()}
        values.update({name: canonical_bytes(value) for name, value in artifacts.items()})
        values["RUN_RESULT.json"] = canonical_bytes(result)
        manifest_files = {name: {"bytes": len(raw), "sha256": sha256_bytes(raw)}
                          for name, raw in values.items()}
        manifest = {"schema": "ARCANA_R6_INT3_ENG10K_MANIFEST_V1",
            "canonical_publication": False, "files": manifest_files,
            "preflight_identity_sha256": sha256_bytes(canonical_bytes(preflight)),
            "run_result_sha256": sha256_bytes(values["RUN_RESULT.json"]),
            "manifest_is_self_excluded": True}
        manifest_raw = canonical_bytes(manifest)
        projected_total = sum(len(value) for value in values.values()) + len(manifest_raw)
        if projected_total > MAX_PROJECTED_OUTPUT_BYTES or projected_total > 536_870_912:
            raise Eng10kContractError("OUTPUT_SIZE_EXCEEDS_PREFLIGHT_BOUNDS")
        for name, raw in values.items():
            path = output / name
            if path.write_bytes(raw) != len(raw) or path.read_bytes() != raw:
                raise Eng10kContractError(f"OUTPUT_READBACK_FAILED:{name}")
        if (output / "ARTIFACT_MANIFEST.json").write_bytes(manifest_raw) != len(manifest_raw):
            raise Eng10kContractError("MANIFEST_WRITE_FAILED")
        if (output / "ARTIFACT_MANIFEST.json").read_bytes() != manifest_raw:
            raise Eng10kContractError("MANIFEST_READBACK_FAILED")
        return manifest
    except BaseException as exc:
        failure = {"status": "INCOMPLETE_NONAUTHORITATIVE", "error": str(exc),
                   "written_members": manifest_files, "canonical_publication": False}
        try:
            (output / "INCOMPLETE.json").write_bytes(canonical_bytes(failure))
        except OSError:
            pass
        raise


def _diagnostic_summary(diagnostics: dict[str, Any]) -> dict[str, Any]:
    """Keep sample rows in their dedicated artifact, not duplicated in result."""
    return {key: value for key, value in diagnostics.items() if key != "samples"}


def _validate_execution_authorization(authorization: object, *, source_head: str,
                                      configuration_sha256: str,
                                      output_relative: Path,
                                      supervision_relative: Path) -> None:
    if not isinstance(authorization, dict):
        raise Eng10kContractError("SEPARATE_EXECUTION_AUTHORIZATION_INVALID")
    required = {"decision": EXECUTION_DECISION, "source_head": source_head,
        "configuration_sha256": configuration_sha256,
        "output_relative": output_relative.as_posix(),
        "supervision_relative": supervision_relative.as_posix(),
        "one_attempt_only": True, "noncanonical": True,
        "limits": {"wall_seconds": 900, "process_group_rss_bytes": 2_147_483_648,
                   "cumulative_output_bytes": 536_870_912}}
    if any(authorization.get(k) != v for k, v in required.items()):
        raise Eng10kContractError("SEPARATE_EXECUTION_AUTHORIZATION_MISMATCH")


def _execute(output_relative: Path, supervision_relative: Path,
             authorization_path: Path, r4_bundle: Path) -> int:
    preflight = _preflight(output_relative, supervision_relative, r4_bundle,
                           allow_existing_supervision=True)
    config, config_raw, config_sha = _configuration()
    authorization = json.loads(authorization_path.read_bytes())
    _validate_execution_authorization(authorization,
        source_head=str(preflight["source_head"]), configuration_sha256=config_sha,
        output_relative=output_relative, supervision_relative=supervision_relative)
    r4 = load_r4_continuation_bundle(r4_bundle)
    output_path = (ROOT / output_relative).resolve()
    output_path.mkdir(parents=True, exist_ok=False)
    started = {"status": "RUN_STARTED_NONCANONICAL", "source_head": preflight["source_head"],
               "configuration_sha256": config_sha, "r4_manifest_sha256": r4.manifest_sha256,
               "numerical_execution_may_follow": True, "canonical_publication": False}
    (output_path / "RUN_STARTED.json").write_bytes(canonical_bytes(started))
    direct_finals: dict[float, tuple] = {}
    direct_diags: dict[str, Any] = {}
    reference_samples: dict[str, Any] = {}
    for factor in RESOLUTION_FACTORS:
        rows = []
        for support, initial in zip(r4.support_ids, r4.initial_states):
            if factor == config["diagnostic_resolution_factor"]:
                final, diagnostics = advance_with_bounded_samples(initial, support_id=support,
                    duration_years=float(config["elapsed_duration_years"]),
                    extension_velocity_m_per_year=r4.forcing_m_per_year,
                    resolution_factor=factor,
                    sample_interval_years=float(config["diagnostic_retention"]["schedule_interval_years"]))
                reference_samples[support] = diagnostics
                rows.append(final)
            else:
                final, diag = pure_shear_thermal_step(initial,
                    duration_s=float(config["elapsed_duration_years"]) * SECONDS_PER_YEAR,
                    extension_velocity_m_s=r4.forcing_m_per_year / SECONDS_PER_YEAR,
                    maximum_kinematic_fraction_per_substep=factor)
                rows.append(final)
                direct_diags[f"{support}:{factor}"] = {
                    "substeps": diag.substeps, "area_relative_error": diag.area_relative_error,
                    "min_stability_limit_s": diag.min_stability_limit_s,
                    "max_stability_ratio": diag.max_stability_ratio,
                }
        direct_finals[factor] = tuple(rows)
    ref = direct_finals[0.0005]
    restart_finals, restart_samples = [], {}
    for support, state in zip(r4.support_ids, r4.checkpoint_states):
        final, diagnostics = advance_with_bounded_samples(state, support_id=support,
            duration_years=float(config["restart_additional_duration_years"]),
            extension_velocity_m_per_year=r4.forcing_m_per_year,
            resolution_factor=0.0005,
            sample_interval_years=float(config["diagnostic_retention"]["schedule_interval_years"]))
        restart_finals.append(final)
        restart_samples[support] = diagnostics
    restart_finals_t = tuple(restart_finals)
    comparison = {support: compare_reduced_states(a, b)
                  for support, a, b in zip(r4.support_ids, ref, restart_finals_t)}
    convergence = {str(factor): [compare_reduced_states(a, b)
                    for a, b in zip(ref, direct_finals[factor])]
                   for factor in RESOLUTION_FACTORS if factor != 0.0005}
    restart_summary = {support: _diagnostic_summary(diagnostics)
                       for support, diagnostics in restart_samples.items()}
    direct_reference_summary = {support: _diagnostic_summary(diagnostics)
                                for support, diagnostics in reference_samples.items()}
    result = {"decision": "NONCANONICAL_ENG10K_ENGINEERING_RESULT",
        "scope": "FROZEN_FORCING_REDUCED_KERNEL_STRESS_TEST",
        "source_head": preflight["source_head"], "configuration_sha256": config_sha,
        "r4_manifest_sha256": r4.manifest_sha256, "boundary_id": r4.boundary_id,
        "support_ids": list(r4.support_ids), "forcing_m_per_year": r4.forcing_m_per_year,
        "direct_elapsed_years": config["elapsed_duration_years"],
        "restart_elapsed_years_at_start": config["r4_checkpoint_elapsed_years"],
        "restart_additional_duration_years": config["restart_additional_duration_years"],
        "final_age_ma": 210.0 - 10000.0 / 1_000_000.0,
        "direct_resolution_factors": list(RESOLUTION_FACTORS),
        "reference_resolution_factor": 0.0005,
        "diagnostics_are_sparse_observations_not_full_history": True,
        "direct_diagnostics": direct_diags,
        "direct_reference_diagnostics": direct_reference_summary,
        "restart_diagnostics": restart_summary,
        "direct_vs_restart": comparison, "direct_refinement_metrics": convergence,
        "canonical_publication": False, "physical_temporal_validity": "NOT_ESTABLISHED"}
    artifacts = {
        "PREFLIGHT.json": preflight,
        "R4_INPUT_BINDING.json": {"manifest_sha256": r4.manifest_sha256,
            "source_identity": dict(r4.source_identity), "support_ids": list(r4.support_ids),
            "boundary_id": r4.boundary_id, "forcing_m_per_year": r4.forcing_m_per_year,
            "r4_initial_states": [s.payload() for s in r4.initial_states],
            "r4_candidate_checkpoint_states": [s.payload() for s in r4.checkpoint_states]},
        "DIRECT_FINAL_STATES.json": {str(k): [s.payload() for s in values]
                                     for k, values in direct_finals.items()},
        "RESTART_FINAL_STATES.json": [s.payload() for s in restart_finals_t],
        "DIAGNOSTIC_SAMPLES.json": {"direct_reference": reference_samples,
                                     "restart": restart_samples,
                                     "all_substeps_retained": False,
                                     "canonical_history": False},
        "COMPARISON.json": {"direct_vs_restart": comparison,
                            "direct_refinement_only": convergence,
                            "acceptance_threshold": "THRESHOLD_UNJUSTIFIED"},
    }
    _write_bundle((ROOT / output_relative).resolve(), artifacts, config_raw, preflight, result)
    print(json.dumps({"decision": result["decision"], "output": output_relative.as_posix()}, sort_keys=True))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("preflight", "execute"), default="preflight")
    parser.add_argument("--output-relative", type=Path, default=OUTPUT_RELATIVE)
    parser.add_argument("--supervision-relative", type=Path, default=SUPERVISION_RELATIVE)
    parser.add_argument("--authorization-json", type=Path)
    parser.add_argument("--r4-bundle", type=Path, default=R4_BUNDLE)
    args = parser.parse_args()
    try:
        if args.mode == "preflight":
            print(json.dumps(_preflight(args.output_relative, args.supervision_relative,
                                        args.r4_bundle), sort_keys=True))
            return 0
        if args.authorization_json is None:
            raise Eng10kContractError("SEPARATE_EXECUTION_AUTHORIZATION_REQUIRED")
        return _execute(args.output_relative, args.supervision_relative,
                        args.authorization_json, args.r4_bundle)
    except (Eng10kContractError, OSError, ValueError) as exc:
        if args.mode == "execute":
            partial = (ROOT / args.output_relative).resolve()
            if partial.is_dir() and not (partial / "ARTIFACT_MANIFEST.json").exists():
                marker = {"status": "INCOMPLETE_NONAUTHORITATIVE", "error": str(exc),
                          "canonical_publication": False}
                try:
                    (partial / "INCOMPLETE.json").write_bytes(canonical_bytes(marker))
                except OSError:
                    pass
        print(f"INT3_ENG10K_BLOCKED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
