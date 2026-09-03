from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping
import json
import os
import shutil
import zipfile

import numpy as np

from arcana_worldsim.late_cenozoic import sealed_120ka_boundary as b1
from arcana_worldsim.late_cenozoic import integrated_provider as ip
from arcana_worldsim.late_cenozoic.cha2_nested_50y import IntegratedLateCenozoicProviderC1
from arcana_worldsim.late_cenozoic.late_pleistocene_boundary import IntegratedLateCenozoicProviderC2
from arcana_worldsim.late_cenozoic.adaptive_clock import AdaptiveClockConfig
from arcana_worldsim.late_cenozoic.adaptive_clock_c2 import build_adaptive_late_cenozoic_clock_c2
from arcana_worldsim.late_cenozoic.eustatic_land_bridge import bridge_relative_eustatic_anomaly

from . import r313_longterm_postcha1_reassembly as r313

STAGE = "v0.6D1-R3.14"
PARENT_STAGE = "v0.6D1-R3.13_SEALED"
BOUNDARY_AGE_MA = 30.0
SCHEMA = "ARCANA_R314_LATE_CENOZOIC_PROVIDER_BINDING_AND_ADAPTIVE_CLOCK_V1"

REQUIRED_V061_RELATIVE_PATHS = {
    "authorial_seal": "AUTHORIAL_SEAL_v0_6_1.json",
    "model_py": "src/arcana_worldsim/paleoclimate/model.py",
    "recent_history": "outputs/hybrid1/paleoclimate_v0_6_1/recent_paleoclimate_history.npz",
    "spatial_snapshots": "outputs/hybrid1/paleoclimate_v0_6_1/paleoclimate_spatial_snapshots.npz",
    "shoreline": "inputs/v0_5_5I_SEALED/shoreline_state_I.npz",
}
EXPECTED_V061_SHA256 = dict(b1.EXPECTED)


@dataclass(frozen=True)
class R314Config:
    boundary_age_ma: float = BOUNDARY_AGE_MA
    search_max_zip_bytes: int = 8_000_000_000
    max_directory_candidates: int = 64
    adaptive_clock_max_geological_step_years: int = 2_000_000
    adaptive_clock_min_secular_step_years: int = 25_000
    adaptive_clock_secular_activity_threshold: float = 1.0
    biology_advanced_in_stage: bool = False
    preview_boundary_authorized: bool = False

    def __post_init__(self) -> None:
        if abs(self.boundary_age_ma - 30.0) > 1e-12:
            raise ValueError("R3.14 binding boundary is fixed at 30.0 Ma")
        if self.biology_advanced_in_stage:
            raise ValueError("R3.14 is a provider/clock binding gate and must not advance biology")
        if self.preview_boundary_authorized:
            raise ValueError("R3.14 forbids the non-authoritative preview/book-era boundary")


def _sha256_file(path: Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _sha256_stream(stream) -> str:
    h = sha256()
    for chunk in iter(lambda: stream.read(1024 * 1024), b""):
        h.update(chunk)
    return h.hexdigest()


def load_a1(root: Path) -> dict[str, np.ndarray]:
    p = Path(root) / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz"
    if not p.is_file():
        raise FileNotFoundError(f"R3.14 requires A1 reference: {p}")
    z = np.load(p, allow_pickle=False)
    return {k: z[k] for k in z.files}


def validate_parent_r313_authority(root: Path) -> dict[str, Any]:
    root = Path(root)
    seal_path = root / "R3_13_SEAL_SUMMARY.json"
    summary_path = root / "local_runs/v0_6D1_R3_13/R3_13_LONGTERM_POST_CHA1_REASSEMBLY_SUMMARY.json"
    checkpoint_path = root / "local_runs/v0_6D1_R3_13/WORLD1_H0_30Ma_LONG_TERM_POST_CHA1_DIVERSIFICATION_REASSEMBLY_CHECKPOINT_v0_6D1_R3_13.json"
    npz_path = checkpoint_path.with_suffix(".npz")
    for p in (seal_path, summary_path, checkpoint_path, npz_path):
        if not p.is_file():
            raise RuntimeError(f"R3.14 requires materialized R3.13 SEALED evidence: missing {p}")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    if seal.get("stage") != "v0.6D1-R3.13" or not str(seal.get("verdict", "")).endswith("30MA_LATE_CENOZOIC_HANDOFF_BOUNDARY_SEALED"):
        raise RuntimeError("R3.13 seal verdict is not authoritative")
    if not str(summary.get("verdict", "")).startswith("PASS_CANONICAL_POST_CHA1_46_TO_30_H0_LONGTERM_DIVERSIFICATION_REASSEMBLY"):
        raise RuntimeError("R3.13 parent run verdict is not authoritative")
    boundary = seal.get("boundary", {})
    if abs(float(boundary.get("age_ma", -1.0)) - 30.0) > 1e-12:
        raise RuntimeError("R3.13 seal boundary is not 30.0 Ma")
    expected = seal.get("artifact_hashes", {})
    actual = {
        "summary": _sha256_file(summary_path),
        "checkpoint_json": _sha256_file(checkpoint_path),
        "checkpoint_npz": _sha256_file(npz_path),
    }
    for key, got in actual.items():
        want = expected.get(key)
        if want and got != want:
            raise RuntimeError(f"R3.13 parent {key} SHA mismatch: {got} != {want}")
    st = r313.load_checkpoint(checkpoint_path)
    if abs(float(st.age_ma) - 30.0) > 1e-12:
        raise RuntimeError("R3.13 checkpoint loader did not restore 30.0 Ma")
    return {
        "seal": str(seal_path),
        "summary": str(summary_path),
        "checkpoint_json": str(checkpoint_path),
        "checkpoint_npz": str(npz_path),
        "hashes": actual,
        "species": int(len(set(st.current_species))),
        "components": int(len(st.component_ids)),
        "population": float(st.pop.sum()),
        "age_ma": float(st.age_ma),
    }


def _verify_candidate_directory(candidate: Path) -> dict[str, Any] | None:
    candidate = Path(candidate)
    try:
        got = b1.verify_v061_sealed_root(candidate)
    except (FileNotFoundError, ValueError):
        return None
    return {"kind": "directory", "source": str(candidate.resolve()), "hashes": got}


def _zip_prefixes(zf: zipfile.ZipFile) -> list[str]:
    suffix = REQUIRED_V061_RELATIVE_PATHS["authorial_seal"]
    out = []
    for name in zf.namelist():
        n = name.replace("\\", "/")
        if n.endswith(suffix):
            out.append(n[:-len(suffix)].rstrip("/"))
    return sorted(set(out))


def inspect_zip_for_exact_v061(zip_path: Path) -> dict[str, Any] | None:
    zip_path = Path(zip_path)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = {n.replace("\\", "/"): n for n in zf.namelist()}
            for prefix in _zip_prefixes(zf):
                got: dict[str, str] = {}
                members: dict[str, str] = {}
                ok = True
                for key, rel in REQUIRED_V061_RELATIVE_PATHS.items():
                    logical = f"{prefix}/{rel}" if prefix else rel
                    member = names.get(logical)
                    if member is None:
                        ok = False
                        break
                    with zf.open(member, "r") as fh:
                        digest = _sha256_stream(fh)
                    got[key] = digest
                    members[key] = member
                    if digest != EXPECTED_V061_SHA256[key]:
                        ok = False
                        break
                if ok:
                    return {
                        "kind": "zip",
                        "source": str(zip_path.resolve()),
                        "prefix": prefix,
                        "members": members,
                        "hashes": got,
                    }
    except (zipfile.BadZipFile, OSError, PermissionError):
        return None
    return None


def extract_exact_v061_from_zip(proof: Mapping[str, Any], target_root: Path) -> Path:
    if proof.get("kind") != "zip":
        raise ValueError("zip proof required")
    target_root = Path(target_root)
    if target_root.exists():
        shutil.rmtree(target_root)
    target_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(Path(proof["source"]), "r") as zf:
        for key, rel in REQUIRED_V061_RELATIVE_PATHS.items():
            member = proof["members"][key]
            dst = target_root / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member, "r") as src, dst.open("wb") as out:
                shutil.copyfileobj(src, out, length=1024 * 1024)
    b1.verify_v061_sealed_root(target_root)
    return target_root


def discover_exact_v061(search_roots: Iterable[Path], target_root: Path, cfg: R314Config | None = None) -> dict[str, Any] | None:
    cfg = cfg or R314Config()
    target_root = Path(target_root)
    if target_root.is_dir():
        proof = _verify_candidate_directory(target_root)
        if proof:
            proof["rehydrated_to"] = str(target_root.resolve())
            proof["reused_existing_local_binding"] = True
            return proof

    seen: set[Path] = set()
    directory_candidates = 0
    zip_candidates: list[Path] = []
    skip_names = {".git", ".venv", "venv", "node_modules", "__pycache__", ".pytest_tmp"}
    for raw in search_roots:
        root = Path(raw).expanduser()
        if not root.exists():
            continue
        try:
            root = root.resolve()
        except OSError:
            continue
        if root in seen:
            continue
        seen.add(root)
        if root.is_file() and root.suffix.lower() == ".zip":
            zip_candidates.append(root)
            continue
        if not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in skip_names]
            p = Path(dirpath)
            if "AUTHORIAL_SEAL_v0_6_1.json" in filenames:
                directory_candidates += 1
                proof = _verify_candidate_directory(p)
                if proof:
                    if target_root.exists():
                        shutil.rmtree(target_root)
                    for rel in REQUIRED_V061_RELATIVE_PATHS.values():
                        src = p / rel; dst = target_root / rel
                        dst.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src, dst)
                    b1.verify_v061_sealed_root(target_root)
                    proof["rehydrated_to"] = str(target_root.resolve())
                    proof["reused_existing_local_binding"] = False
                    return proof
                if directory_candidates >= cfg.max_directory_candidates:
                    dirnames[:] = []
            for f in filenames:
                if f.lower().endswith(".zip"):
                    zp = p / f
                    try:
                        if zp.stat().st_size <= cfg.search_max_zip_bytes:
                            zip_candidates.append(zp)
                    except OSError:
                        pass

    # Prefer filenames that explicitly advertise v0.6.1 or late-Cenozoic packages.
    def priority(p: Path) -> tuple[int, str]:
        n = p.name.lower()
        score = 0
        if "v0_6_1" in n or "v0.6.1" in n: score -= 4
        if "6_4d" in n or "late_cenozoic" in n: score -= 3
        if "6_5" in n or "natural_control_30ma_0" in n: score -= 2
        return score, str(p)

    unique_zips = sorted({p.resolve() for p in zip_candidates if p.exists()}, key=priority)
    for zp in unique_zips:
        proof = inspect_zip_for_exact_v061(zp)
        if proof:
            extract_exact_v061_from_zip(proof, target_root)
            proof["rehydrated_to"] = str(target_root.resolve())
            proof["reused_existing_local_binding"] = False
            proof["zip_candidates_considered"] = len(unique_zips)
            return proof
    return None


def materialize_b1_b2(a1: Mapping[str, Any], sealed_root: Path, out_root: Path) -> dict[str, Any]:
    sealed_root = Path(sealed_root); out_root = Path(out_root)
    b1_dir = out_root / "v0_6_4B1"; b2_dir = out_root / "v0_6_4B2"
    b1_dir.mkdir(parents=True, exist_ok=True); b2_dir.mkdir(parents=True, exist_ok=True)

    proof = b1.verify_v061_sealed_root(sealed_root)
    equivalence = b1.verify_generalizer_against_materialized_snapshot(sealed_root, -21_000.0)
    if not equivalence.get("all_fields_bit_exact", False):
        raise RuntimeError("sealed v0.6.1 spatial equation generalizer is not bit-exact at -21 ka")
    spatial = b1.reconstruct_v061_spatial_at_year(sealed_root, -120_000.0)
    remapped = b1.remap_exact_120ka_to_a1(a1, spatial)
    boundary = b1.boundary_state_from_remapped_120ka(a1, remapped, proof["recent_history"], proof["spatial_snapshots"])

    b1_path = b1_dir / "exact_120ka_A1_boundary_state.npz"
    np.savez_compressed(
        b1_path,
        age_ma=np.asarray([boundary.age_ma], dtype=float),
        atmospheric_co2_ppm=np.asarray([boundary.atmospheric_co2_ppm], dtype=float),
        temperature_c=np.asarray(boundary.temperature_c, dtype=float),
        aridity_index=np.asarray(boundary.aridity_index, dtype=float),
        browse_forage=np.asarray(boundary.browse_forage, dtype=float),
        low_forage=np.asarray(boundary.low_forage, dtype=float),
        wetland_forage=np.asarray(boundary.wetland_forage, dtype=float),
        total_edible_forage=np.asarray(boundary.total_edible_forage, dtype=float),
        paleo_land_fraction=np.asarray(boundary.paleo_land_mask, dtype=float),
    )
    loaded = b1.load_materialized_a1_boundary(b1_path)
    for field in ("temperature_c", "aridity_index", "browse_forage", "low_forage", "wetland_forage", "total_edible_forage", "paleo_land_mask"):
        if not np.array_equal(np.asarray(getattr(boundary, field)), np.asarray(getattr(loaded, field))):
            raise RuntimeError(f"B1 serialization mismatch for {field}")

    recent = ip.SealedRecentA1Provider(a1, sealed_root)
    exact120 = recent.state_at(0.12)
    effective = np.asarray(exact120["land_support"], dtype=float)
    b2_path = b2_dir / "relative_eustatic_shoreline_anomaly_120ka_A1.npz"
    np.savez_compressed(
        b2_path,
        age_ma=np.asarray([0.12], dtype=float),
        effective_land_support_120ka=effective,
        colonizable_shelf_support_120ka=np.asarray(exact120["colonizable_shelf_support"], dtype=float),
    )
    z = np.load(b2_path, allow_pickle=False)
    if not np.array_equal(z["effective_land_support_120ka"], effective):
        raise RuntimeError("B2 serialization mismatch")

    return {
        "sealed_payload_hashes": proof,
        "generalizer_equivalence_21ka": equivalence,
        "b1_npz": str(b1_path), "b1_sha256": _sha256_file(b1_path),
        "b2_npz": str(b2_path), "b2_sha256": _sha256_file(b2_path),
        "b2_diagnostics": exact120["effective_land_bridge_diagnostics"],
    }


def build_bound_provider_and_clock(a1: Mapping[str, Any], sealed_root: Path, b1_path: Path, b2_path: Path, cfg: R314Config | None = None) -> tuple[IntegratedLateCenozoicProviderC2, dict[str, Any]]:
    cfg = cfg or R314Config()
    c1 = IntegratedLateCenozoicProviderC1(a1, sealed_root, b1_path, b2_path)
    c2 = IntegratedLateCenozoicProviderC2(c1)
    clock_cfg = AdaptiveClockConfig(
        max_geological_step_years=cfg.adaptive_clock_max_geological_step_years,
        min_secular_step_years=cfg.adaptive_clock_min_secular_step_years,
        secular_activity_threshold=cfg.adaptive_clock_secular_activity_threshold,
    )
    clock = build_adaptive_late_cenozoic_clock_c2(c2, clock_cfg)
    val = clock["validation"]
    if val.get("status") != "PASS" or not val.get("production_replay_ready", False):
        raise RuntimeError(f"C2 adaptive clock not production replay ready: {val}")
    return c2, clock


def validate_30ma_binding(a1: Mapping[str, Any], provider: IntegratedLateCenozoicProviderC2) -> dict[str, Any]:
    # R3.13 already established exact identity against the old R3 provider.
    old = r313.validate_30ma_environment_handoff(a1)
    if not isinstance(provider.parent, IntegratedLateCenozoicProviderC1):
        raise TypeError("R3.14 C2 provider is not bound to the required IntegratedLateCenozoicProviderC1 parent")
    late = provider.state_at(30.0)
    fields = ("land_support", "temperature_c", "aridity_index", "browse_forage", "low_forage", "wetland_forage", "total_edible_forage")
    diffs = {}
    exact = bool(old["environmental_endpoint_identity_exact"])
    baseline = __import__("arcana_worldsim.late_cenozoic.environment", fromlist=["late_cenozoic_environment_state"]).late_cenozoic_environment_state(a1, 30.0)
    for key in fields:
        a = np.asarray(baseline[key]); b = np.asarray(late[key])
        same = bool(np.array_equal(a, b)); err = float(np.max(np.abs(a.astype(float) - b.astype(float))))
        diffs[key] = {"exact": same, "max_abs_error": err}; exact &= same
    return {
        "age_ma": 30.0,
        "r313_old_to_late_endpoint_identity_exact": bool(old["environmental_endpoint_identity_exact"]),
        "r314_bound_c2_endpoint_identity_exact": bool(exact),
        "fields": diffs,
        "biology_advanced": False,
    }


def summarize_clock(clock: Mapping[str, Any]) -> dict[str, Any]:
    ages = np.asarray(clock["age_ma"], dtype=float)
    intervals = list(clock["intervals"])
    dts = np.asarray([int(r["dt_years"]) for r in intervals], dtype=int)
    domains: dict[str, int] = {}
    for row in intervals:
        domains[str(row["domain"])] = domains.get(str(row["domain"]), 0) + 1
    return {
        "status": clock["status"],
        "checkpoint_count": int(ages.size),
        "interval_count": int(len(intervals)),
        "start_age_ma": float(ages[0]),
        "end_age_ma": float(ages[-1]),
        "contains_200ka": bool(np.any(np.isclose(ages, 0.2, atol=1e-12, rtol=0))),
        "contains_120ka": bool(np.any(np.isclose(ages, 0.12, atol=1e-12, rtol=0))),
        "min_dt_years": int(dts.min()) if dts.size else None,
        "max_dt_years": int(dts.max()) if dts.size else None,
        "domain_interval_counts": domains,
        "validation": clock["validation"],
    }


def write_clock_json(clock: Mapping[str, Any], path: Path) -> None:
    payload = {
        "status": clock["status"],
        "age_ma": [float(x) for x in np.asarray(clock["age_ma"]).tolist()],
        "model_seconds": [int(x) for x in np.asarray(clock["model_seconds"]).tolist()],
        "intervals": list(clock["intervals"]),
        "validation": clock["validation"],
    }
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")


def run_binding(root: Path, search_roots: Iterable[Path], cfg: R314Config | None = None) -> dict[str, Any]:
    cfg = cfg or R314Config(); root = Path(root)
    parent = validate_parent_r313_authority(root)
    a1 = load_a1(root)
    out = root / "local_bindings/v0_6D1_R3_14"
    sealed_root = out / "v0_6_1_SEALED_MINIMAL"
    out.mkdir(parents=True, exist_ok=True)
    discovery = discover_exact_v061(search_roots, sealed_root, cfg)
    if discovery is None:
        blocked = {
            "schema": SCHEMA, "stage": STAGE,
            "verdict": "BLOCKED_R314_EXACT_V061_SEALED_PAYLOAD_NOT_FOUND",
            "parent_r313_authority": parent,
            "search_roots": [str(Path(x)) for x in search_roots],
            "required_v061_relative_paths": REQUIRED_V061_RELATIVE_PATHS,
            "required_v061_sha256": EXPECTED_V061_SHA256,
            "biology_advanced": False,
            "preview_boundary_used": False,
            "next_action": "Locate an archive/directory containing all five exact v0.6.1 sealed artifacts and rerun R3.14 binding.",
        }
        bp = out / "R3_14_BINDING_BLOCKER_REPORT.json"
        bp.write_text(json.dumps(blocked, indent=2), encoding="utf-8")
        blocked["blocker_report"] = str(bp)
        blocked["blocker_report_sha256"] = _sha256_file(bp)
        return blocked

    materialized = materialize_b1_b2(a1, sealed_root, out)
    c2, clock = build_bound_provider_and_clock(a1, sealed_root, materialized["b1_npz"], materialized["b2_npz"], cfg)
    binding = validate_30ma_binding(a1, c2)
    if not binding["r314_bound_c2_endpoint_identity_exact"]:
        raise RuntimeError("R3.14 C2 provider does not preserve exact 30 Ma environmental endpoint")
    clock_path = out / "R3_14_ADAPTIVE_CLOCK_C2_30Ma_TO_BOOK.json"
    write_clock_json(clock, clock_path)
    summary = {
        "schema": SCHEMA, "stage": STAGE,
        "verdict": "PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__BIOLOGY_REPLAY_NOT_STARTED",
        "parent_r313_authority": parent,
        "discovery": discovery,
        "materialized_boundaries": materialized,
        "binding_30ma": binding,
        "adaptive_clock": summarize_clock(clock),
        "adaptive_clock_json": str(clock_path),
        "adaptive_clock_json_sha256": _sha256_file(clock_path),
        "governance": {
            "biology_advanced": False,
            "deep_biological_coupling": False,
            "cha1_reapplied": False,
            "lifecycle_thaw_reapplied": False,
            "preview_boundary_used": False,
            "exact_v061_hash_binding_required": True,
            "b1_b2_rematerialized_from_existing_authorized_equations": True,
            "c2_120ka_replay_safe_boundary_required": True,
            "adaptive_clock_is_scheduler_not_new_physics": True,
            "richness_target_used": False,
            "guild_target_used": False,
            "cross_guild_transition_operator_activated": False,
        },
        "config": asdict(cfg),
    }
    sp = out / "R3_14_LATE_CENOZOIC_BINDING_SUMMARY.json"
    sp.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary["summary_path"] = str(sp)
    summary["summary_sha256"] = _sha256_file(sp)
    return summary
