from __future__ import annotations

import argparse
import hashlib
import importlib
import inspect
import json
import sys
import traceback
from pathlib import Path
from typing import Any

import R5_17_B6_D2D_VALIDATE_SEASONAL_GENERATOR_AND_RECONSTRUCT_I as d2d

TARGET_GENERATOR_SUFFIX = d2d.TARGET_GENERATOR_SUFFIX
TARGET_GENERATOR_SHA256 = d2d.TARGET_GENERATOR_SHA256


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path | str) -> str:
    return str(path).replace("\\", "/")


def clear_arcana_modules() -> None:
    for name in list(sys.modules):
        if name == "arcana_worldsim" or name.startswith("arcana_worldsim."):
            del sys.modules[name]
    importlib.invalidate_caches()


def remove_src_from_syspath(src: Path) -> None:
    target = str(src)
    while target in sys.path:
        sys.path.remove(target)


def package_snapshot(generator: Path) -> dict[str, Any]:
    src = d2d.generator_source_root(generator)
    package = src / "arcana_worldsim"
    finalization = package / "finalization"
    py_files = []
    if package.is_dir():
        try:
            py_files = [p for p in package.rglob("*.py") if p.is_file()]
        except OSError:
            py_files = []
    return {
        "generator_path": str(generator.resolve()),
        "generator_sha256": sha256_file(generator),
        "src_root": str(src.resolve()),
        "package_root": str(package.resolve()),
        "package_root_exists": package.is_dir(),
        "arcana_init_exists": (package / "__init__.py").is_file(),
        "finalization_dir_exists": finalization.is_dir(),
        "finalization_init_exists": (finalization / "__init__.py").is_file(),
        "python_file_count_under_arcana_worldsim": len(py_files),
    }


def test_candidate(generator: Path) -> dict[str, Any]:
    src = d2d.generator_source_root(generator)
    rec = package_snapshot(generator)
    clear_arcana_modules()
    remove_src_from_syspath(src)
    try:
        fn = d2d.import_exact_generator(generator)
        resolved_module = inspect.getmodule(fn)
        resolved_file = Path(inspect.getsourcefile(resolved_module) or "").resolve() if resolved_module else None
        rec.update({
            "importable": True,
            "function": getattr(fn, "__name__", None),
            "signature": str(inspect.signature(fn)),
            "resolved_module_file": str(resolved_file) if resolved_file else None,
            "resolved_file_matches_candidate": bool(resolved_file == generator.resolve()) if resolved_file else False,
        })
    except Exception as exc:
        rec.update({
            "importable": False,
            "error": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": traceback.format_exc(limit=20),
            },
        })
    finally:
        clear_arcana_modules()
        remove_src_from_syspath(src)
    return rec


def main() -> None:
    ap = argparse.ArgumentParser(
        description=(
            "R5.17-B6-D2D1: resolve the runtime binding for the exact SHA-authenticated "
            "canonical seasonal generator by testing every identical local materialization "
            "before delegating unchanged scientific replay/reconstruction gates to D2D."
        )
    )
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument(
        "--d2c1-json",
        type=Path,
        default=Path("R5_17_B6_D2C1_SHORELINE_LAND_MASK_ADAPTER_ADJUDICATION.json"),
    )
    ap.add_argument(
        "--reconstructed-output",
        type=Path,
        default=Path("R5_17_B6_D2D_RECONSTRUCTED/seasonal_climate_state_I_RECONSTRUCTED.npz"),
    )
    ap.add_argument(
        "--d2d-output",
        type=Path,
        default=Path("R5_17_B6_D2D_SEASONAL_GENERATOR_REPLAY_AND_I_RECONSTRUCTION.json"),
    )
    ap.add_argument(
        "--output",
        type=Path,
        default=Path("R5_17_B6_D2D1_EXACT_SEASONAL_GENERATOR_RUNTIME_BINDING.json"),
    )
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    candidates = d2d.locate_exact_suffix(root, TARGET_GENERATOR_SUFFIX, TARGET_GENERATOR_SHA256)
    attempts = [test_candidate(p) for p in candidates]

    selected: Path | None = None
    for path, attempt in zip(candidates, attempts):
        if attempt.get("importable") and attempt.get("resolved_file_matches_candidate"):
            selected = path.resolve()
            break

    result: dict[str, Any] = {
        "schema": "ARCANA_R5_17_B6_D2D1_EXACT_SEASONAL_GENERATOR_RUNTIME_BINDING_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2D1",
        "purpose": (
            "Resolve only the Python runtime/package binding of the already SHA-authenticated "
            "canonical seasonal generator. No source substitution, scientific tolerance change, "
            "external provider, or canonical mutation is authorized here."
        ),
        "search_root": str(root),
        "target_generator_suffix": TARGET_GENERATOR_SUFFIX,
        "target_generator_sha256": TARGET_GENERATOR_SHA256,
        "exact_candidate_count": len(candidates),
        "candidate_attempts": attempts,
        "runtime_binding_resolved": selected is not None,
        "selected_generator_path": str(selected) if selected else None,
        "selected_generator_sha256": sha256_file(selected) if selected else None,
        "delegated_d2d": False,
        "delegated_d2d_status": None,
        "external_provider_authorized": False,
        "canonical_mutation": False,
        "scientific_contract_changed": False,
    }

    if selected is None:
        result["status"] = "BLOCKED_R517_B6_D2D1_NO_IMPORTABLE_EXACT_GENERATOR_MATERIALIZATION"
        result["decision"] = "RECOVER_OR_COMPOSE_EXACT_RUNTIME_DEPENDENCY_BINDING"
        args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({
            "status": result["status"],
            "decision": result["decision"],
            "exact_candidate_count": len(candidates),
            "importable_candidate_count": sum(bool(x.get("importable")) for x in attempts),
            "selected_generator_path": None,
            "output": str(args.output.resolve()),
        }, indent=2))
        raise SystemExit(2)

    original_locator = d2d.locate_exact_suffix

    def prioritized_locator(search_root: Path, suffix: str, expected_sha: str) -> list[Path]:
        located = original_locator(search_root, suffix, expected_sha)
        if suffix == TARGET_GENERATOR_SUFFIX and expected_sha == TARGET_GENERATOR_SHA256:
            selected_resolved = selected.resolve()
            return [selected_resolved] + [p for p in located if p.resolve() != selected_resolved]
        return located

    d2d.locate_exact_suffix = prioritized_locator

    previous_argv = list(sys.argv)
    delegated_exit: int | None = None
    try:
        sys.argv = [
            str(Path(d2d.__file__).resolve()),
            "--search-root", str(root),
            "--d2c1-json", str(args.d2c1_json.resolve()),
            "--reconstructed-output", str(args.reconstructed_output.resolve()),
            "--output", str(args.d2d_output.resolve()),
        ]
        result["delegated_d2d"] = True
        try:
            d2d.main()
            delegated_exit = 0
        except SystemExit as exc:
            delegated_exit = int(exc.code or 0)
    finally:
        sys.argv = previous_argv
        d2d.locate_exact_suffix = original_locator

    if args.d2d_output.is_file():
        try:
            delegated = json.loads(args.d2d_output.read_text(encoding="utf-8"))
            result["delegated_d2d_status"] = delegated.get("status")
            result["delegated_d2d_decision"] = delegated.get("decision")
            result["delegated_f_fixture_exact_replay_validated"] = delegated.get(
                "f_fixture_exact_replay_validated"
            )
            result["delegated_i_reconstruction_materialized"] = delegated.get(
                "i_reconstruction_materialized"
            )
        except Exception as exc:
            result["delegated_output_read_error"] = {
                "type": type(exc).__name__,
                "message": str(exc),
            }

    result["delegated_exit_code"] = delegated_exit

    if delegated_exit == 0 and str(result.get("delegated_d2d_status", "")).startswith("PASS_"):
        result["status"] = "PASS_R517_B6_D2D1_RUNTIME_BINDING_RESOLVED_AND_D2D_DELEGATED_PASS"
        result["decision"] = "ACCEPT_D2D_RESULT"
    else:
        result["status"] = "PASS_R517_B6_D2D1_RUNTIME_BINDING_RESOLVED_D2D_STILL_BLOCKED"
        result["decision"] = "INSPECT_DELEGATED_D2D_SCIENTIFIC_OR_FIXTURE_GATE"

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "decision": result["decision"],
        "exact_candidate_count": len(candidates),
        "importable_candidate_count": sum(bool(x.get("importable")) for x in attempts),
        "selected_generator_path": str(selected),
        "selected_generator_sha256": sha256_file(selected),
        "delegated_d2d_status": result.get("delegated_d2d_status"),
        "delegated_exit_code": delegated_exit,
        "output": str(args.output.resolve()),
    }, indent=2))

    if delegated_exit not in (None, 0):
        raise SystemExit(delegated_exit)


if __name__ == "__main__":
    main()
