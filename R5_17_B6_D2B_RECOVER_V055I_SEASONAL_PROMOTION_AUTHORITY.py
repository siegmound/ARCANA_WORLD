from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from typing import Any

TARGET_NAME = "seasonal_climate_state_I.npz"
TARGET_DIR = "v0_5_5I_SEALED"
PHYSICAL_HASH = "347f07b9ff16f5c097319898c0b33b86851fc66775b9243ce0f98dce279b954f"
MARGIN_HASH = "1b32d97a0b4dad12f01f4c286461d6ca597c2d46a390a8801771735d972d93f6"
PHYSICAL_SOURCE = "outputs/hybrid1/physical_finalization/seasonal_climate_state.npz"
MARGIN_SOURCE = "outputs/hybrid1/margin_morphogenesis/seasonal_climate_state.npz"
TEXT_SUFFIXES = {".py", ".json", ".md", ".txt", ".ps1", ".yaml", ".yml", ".toml"}
MAX_TEXT_BYTES = 8 * 1024 * 1024
MAX_NPZ_BYTES = 1024 * 1024 * 1024
EXCLUDED_BASENAME_PREFIXES = ("R5_17_B6_",)
EXCLUDED_BASENAMES = {"ARCANA_WORLD_CURRENT_STATE.md"}
ACTION_TERMS = ("copy", "copy-item", "copyfile", "shutil.copy", "stage", "staging", "promot", "rename", "package", "seal", "manifest")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(value: Path | str) -> str:
    return str(value).replace("\\", "/")


def excluded_name(name: str) -> bool:
    base = Path(name).name
    if base in EXCLUDED_BASENAMES:
        return True
    return any(base.startswith(prefix) for prefix in EXCLUDED_BASENAME_PREFIXES)


def inspect_npz_bytes(data: bytes) -> dict[str, Any]:
    import numpy as np
    try:
        with np.load(io.BytesIO(data), allow_pickle=False) as z:
            return {
                "ok": True,
                "keys": sorted(z.files),
                "key_count": len(z.files),
                "arrays": {k: {"shape": list(z[k].shape), "dtype": str(z[k].dtype)} for k in z.files},
            }
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def exact_payload_candidates(root: Path) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for p in root.rglob(TARGET_NAME):
        if ".git" in p.parts or not p.is_file():
            continue
        try:
            rec = {
                "source_class": "direct",
                "path": str(p.resolve()),
                "sha256": sha256_file(p),
                "size_bytes": p.stat().st_size,
            }
            if p.stat().st_size <= MAX_NPZ_BYTES:
                rec["npz"] = inspect_npz_bytes(p.read_bytes())
            out.append(rec)
        except OSError:
            continue

    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    if Path(info.filename).name.lower() != TARGET_NAME.lower():
                        continue
                    rec: dict[str, Any] = {
                        "source_class": "zip",
                        "archive": str(archive.resolve()),
                        "member": info.filename,
                        "size_bytes": info.file_size,
                    }
                    if info.file_size <= MAX_NPZ_BYTES:
                        data = zf.read(info)
                        rec["sha256"] = sha256_bytes(data)
                        rec["npz"] = inspect_npz_bytes(data)
                    out.append(rec)
        except (OSError, zipfile.BadZipFile):
            continue
    return out


def candidate_tokens(kind: str) -> tuple[str, str]:
    if kind == "physical_finalization":
        return PHYSICAL_HASH.lower(), PHYSICAL_SOURCE.lower()
    return MARGIN_HASH.lower(), MARGIN_SOURCE.lower()


def classify_text_bridge(text: str, kind: str) -> dict[str, Any]:
    lower = text.lower()
    candidate_hash, source_path = candidate_tokens(kind)
    target_name = TARGET_NAME.lower()
    target_dir = TARGET_DIR.lower()

    has_target_name = target_name in lower
    has_target_dir = target_dir in lower
    has_source = candidate_hash in lower or source_path in lower
    has_action = any(term in lower for term in ACTION_TERMS)

    lines = text.splitlines()
    strong_windows: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        ll = line.lower()
        if target_name not in ll and candidate_hash not in ll and source_path not in ll:
            continue
        lo = max(0, i - 5)
        hi = min(len(lines), i + 6)
        window = "\n".join(lines[lo:hi])
        wl = window.lower()
        window_target = target_name in wl
        window_source = candidate_hash in wl or source_path in wl
        window_action = any(term in wl for term in ACTION_TERMS)
        if window_target and window_source and window_action:
            strong_windows.append({
                "start_line": lo + 1,
                "end_line": hi,
                "text": window[:8000],
            })
            if len(strong_windows) >= 20:
                break

    strong = bool(strong_windows)
    weak = bool(has_target_name and has_source and has_action)
    return {
        "has_exact_target_name": has_target_name,
        "has_target_dir": has_target_dir,
        "has_candidate_source_or_hash": has_source,
        "has_promotion_copy_packaging_semantics": has_action,
        "strong_bridge": strong,
        "weak_same_file_bridge": weak,
        "strong_windows": strong_windows,
    }


def scan_text_files(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    coarse_needles = (
        TARGET_NAME.lower(), TARGET_DIR.lower(), PHYSICAL_HASH.lower(), MARGIN_HASH.lower(),
        PHYSICAL_SOURCE.lower(), MARGIN_SOURCE.lower(),
    )
    for p in root.rglob("*"):
        if not p.is_file() or ".git" in p.parts or p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if excluded_name(p.name):
            continue
        try:
            if p.stat().st_size > MAX_TEXT_BYTES:
                continue
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        lower = text.lower()
        if not any(n in lower for n in coarse_needles):
            continue
        physical = classify_text_bridge(text, "physical_finalization")
        margin = classify_text_bridge(text, "margin_morphogenesis")
        if not (physical["has_exact_target_name"] or physical["has_target_dir"] or margin["has_exact_target_name"] or margin["has_target_dir"]):
            continue
        records.append({
            "source_class": "direct_text",
            "path": str(p.resolve()),
            "sha256": sha256_file(p),
            "physical_finalization": physical,
            "margin_morphogenesis": margin,
        })
    return records


def scan_zip_text(root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    coarse_needles = (
        TARGET_NAME.lower(), TARGET_DIR.lower(), PHYSICAL_HASH.lower(), MARGIN_HASH.lower(),
        PHYSICAL_SOURCE.lower(), MARGIN_SOURCE.lower(),
    )
    for archive in root.rglob("*.zip"):
        if ".git" in archive.parts:
            continue
        try:
            with zipfile.ZipFile(archive) as zf:
                for info in zf.infolist():
                    if Path(info.filename).suffix.lower() not in TEXT_SUFFIXES or info.file_size > MAX_TEXT_BYTES:
                        continue
                    if excluded_name(info.filename):
                        continue
                    try:
                        text = zf.read(info).decode("utf-8", errors="replace")
                    except Exception:
                        continue
                    lower = text.lower()
                    if not any(n in lower for n in coarse_needles):
                        continue
                    physical = classify_text_bridge(text, "physical_finalization")
                    margin = classify_text_bridge(text, "margin_morphogenesis")
                    if not (physical["has_exact_target_name"] or physical["has_target_dir"] or margin["has_exact_target_name"] or margin["has_target_dir"]):
                        continue
                    records.append({
                        "source_class": "zip_text",
                        "archive": str(archive.resolve()),
                        "member": info.filename,
                        "physical_finalization": physical,
                        "margin_morphogenesis": margin,
                    })
        except (OSError, zipfile.BadZipFile):
            continue
    return records


def main() -> None:
    ap = argparse.ArgumentParser(description="R5.17-B6-D2B: recover strict historical promotion authority for the lost v0.5.5I seasonal climate baseline, excluding self-generated R5.17 audit evidence.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D2B_V055I_SEASONAL_PROMOTION_AUTHORITY.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    payloads = exact_payload_candidates(root)
    direct_physical_payloads = [p for p in payloads if p.get("sha256") == PHYSICAL_HASH]
    direct_margin_payloads = [p for p in payloads if p.get("sha256") == MARGIN_HASH]
    other_payloads = [p for p in payloads if p.get("sha256") not in {PHYSICAL_HASH, MARGIN_HASH}]

    text_records = scan_text_files(root)
    zip_records = scan_zip_text(root)
    all_records = [*text_records, *zip_records]

    physical_strong = [r for r in all_records if r["physical_finalization"].get("strong_bridge")]
    margin_strong = [r for r in all_records if r["margin_morphogenesis"].get("strong_bridge")]
    physical_weak = [r for r in all_records if r["physical_finalization"].get("weak_same_file_bridge")]
    margin_weak = [r for r in all_records if r["margin_morphogenesis"].get("weak_same_file_bridge")]

    authorized_hash: str | None = None
    authorized_source: str | None = None
    exact_identity = False

    if direct_physical_payloads and not direct_margin_payloads:
        authorized_hash = PHYSICAL_HASH
        authorized_source = "materialized_exact_target_payload"
        exact_identity = True
    elif direct_margin_payloads and not direct_physical_payloads:
        authorized_hash = MARGIN_HASH
        authorized_source = "materialized_exact_target_payload"
        exact_identity = True
    elif physical_strong and not margin_strong:
        authorized_hash = PHYSICAL_HASH
        authorized_source = "strict_historical_promotion_bridge"
        exact_identity = True
    elif margin_strong and not physical_strong:
        authorized_hash = MARGIN_HASH
        authorized_source = "strict_historical_promotion_bridge"
        exact_identity = True

    if exact_identity:
        status = "PASS_R517_B6_D2B_EXACT_V055I_SEASONAL_PROMOTION_AUTHORITY_RECOVERED"
        decision = "AUTHORIZE_RECOVERED_V055I_SEASONAL_BASELINE_FOR_D3_REPLAY"
    elif physical_strong and margin_strong:
        status = "BLOCKED_R517_B6_D2B_CONFLICTING_STRONG_PROMOTION_BRIDGES"
        decision = "PROMOTION_IDENTITY_CONFLICT_REQUIRES_TARGETED_MANUAL_PROVENANCE_REVIEW"
    else:
        status = "PASS_R517_B6_D2B_NO_EXACT_PROMOTION_AUTHORITY_RECOVERED"
        decision = "DESIGN_CANONICAL_BASELINE_RECONSTRUCTION_WITH_PROVENANCE_GAP"

    result = {
        "schema": "ARCANA_R5_17_B6_D2B_V055I_SEASONAL_PROMOTION_AUTHORITY_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D2B",
        "purpose": "Recover strict historical promotion/copy authority linking one recovered seasonal climate candidate to inputs/v0_5_5I_SEALED/seasonal_climate_state_I.npz while excluding current R5.17 self-generated evidence.",
        "search_root": str(root),
        "target_payload": f"inputs/{TARGET_DIR}/{TARGET_NAME}",
        "physical_finalization_candidate_sha256": PHYSICAL_HASH,
        "margin_morphogenesis_candidate_sha256": MARGIN_HASH,
        "excluded_current_evidence_prefixes": list(EXCLUDED_BASENAME_PREFIXES),
        "exact_target_payload_candidates": payloads,
        "exact_target_payload_count": len(payloads),
        "exact_target_matches_physical_count": len(direct_physical_payloads),
        "exact_target_matches_margin_count": len(direct_margin_payloads),
        "exact_target_other_hash_count": len(other_payloads),
        "historical_text_record_count": len(text_records),
        "historical_zip_text_record_count": len(zip_records),
        "physical_strong_bridge_count": len(physical_strong),
        "margin_strong_bridge_count": len(margin_strong),
        "physical_weak_bridge_count": len(physical_weak),
        "margin_weak_bridge_count": len(margin_weak),
        "physical_strong_bridges": physical_strong[:30],
        "margin_strong_bridges": margin_strong[:30],
        "physical_weak_bridges": physical_weak[:30],
        "margin_weak_bridges": margin_weak[:30],
        "exact_v055i_seasonal_baseline_identity_adjudicated": exact_identity,
        "authorized_baseline_sha256": authorized_hash,
        "authorized_identity_source": authorized_source,
        "replay_execution_ready_from_d2b": exact_identity,
        "decision": decision,
        "historical_source_executed": False,
        "external_provider_authorized": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_exact": "R5.17-B6-D3_CANONICAL_PALEOHYDROLOGY_REPLAY_IMPLEMENTATION",
        "next_if_gap": "R5.17-B6-D2C_CANONICAL_SEASONAL_BASELINE_RECONSTRUCTION_DESIGN",
    }

    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "decision": decision,
        "exact_target_payload_count": len(payloads),
        "physical_strong_bridge_count": len(physical_strong),
        "margin_strong_bridge_count": len(margin_strong),
        "physical_weak_bridge_count": len(physical_weak),
        "margin_weak_bridge_count": len(margin_weak),
        "exact_v055i_seasonal_baseline_identity_adjudicated": exact_identity,
        "authorized_baseline_sha256": authorized_hash,
        "authorized_identity_source": authorized_source,
        "replay_execution_ready_from_d2b": exact_identity,
        "output": str(args.output.resolve()),
    }, indent=2))

    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
