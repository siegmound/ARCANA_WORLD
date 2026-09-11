from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

EXPECTED = {
    "src/arcana_worldsim/surface/hydrology.py": "34584d0e8a8696b26e4026aad28f362850b7e9b98bb7754cc5cab8e4d282ff42",
    "src/arcana_worldsim/regional/hydrology.py": "e32d766e3e700dd2da22adda3c09b0327e503d1ab9df663eb1c23e6730832b87",
    "src/arcana_worldsim/climate/water_balance.py": "23090416ef8234d43689171241d80d8ca2609882455bd30761de30301e5bfb61",
    "src/arcana_worldsim/finalization/hydrology.py": "29c808bd889d3f0c6e5390775d8751f68b9c9dd2cb5bab1736d6ad6cc6486351",
}

INTEREST = (
    "def ", "class ", "@dataclass", "precip", "rain", "snow", "temperature",
    "evap", "infil", "groundwater", "storage", "cryo", "runoff", "route",
    "discharge", "receiver_flat", "drainage_area_km2", "lake_candidate_mask",
    "depression_depth_m", "cell_area", "monthly", "annual", "np.savez",
    "savez_compressed", "load(", "seasonal_climate", "shoreline", "hydrology",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def norm(path: Path) -> str:
    return str(path).replace("\\", "/")


def locate_exact_sources(root: Path) -> dict[str, list[Path]]:
    found: dict[str, list[Path]] = {k: [] for k in EXPECTED}
    for p in root.rglob("*.py"):
        if ".git" in p.parts:
            continue
        np = norm(p).lower()
        for suffix, expected_hash in EXPECTED.items():
            if np.endswith(suffix.lower()):
                try:
                    if sha256_file(p) == expected_hash:
                        found[suffix].append(p)
                except OSError:
                    pass
    return found


def block_ranges(lines: list[str]) -> list[tuple[int, int, str]]:
    starts: list[tuple[int, int, str]] = []
    for i, line in enumerate(lines):
        m = re.match(r"^(\s*)(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(|^(\s*)class\s+([A-Za-z_][A-Za-z0-9_]*)", line)
        if m:
            indent = len(m.group(1) or m.group(3) or "")
            name = m.group(2) or m.group(4) or "unknown"
            starts.append((i, indent, name))
    out: list[tuple[int, int, str]] = []
    for idx, (start, indent, name) in enumerate(starts):
        end = len(lines)
        for j in range(start + 1, len(lines)):
            line = lines[j]
            if not line.strip():
                continue
            cur_indent = len(line) - len(line.lstrip())
            if cur_indent <= indent and re.match(r"^(?:async\s+)?def\s+|^class\s+", line.lstrip()):
                end = j
                break
        out.append((start, end, name))
    return out


def inspect_source(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    signatures: list[dict[str, Any]] = []
    for i, line in enumerate(lines, start=1):
        if re.match(r"^\s*(?:async\s+)?def\s+", line) or re.match(r"^\s*class\s+", line) or line.lstrip().startswith("@dataclass"):
            signatures.append({"line": i, "text": line[:1000]})

    blocks: list[dict[str, Any]] = []
    for start, end, name in block_ranges(lines):
        block_text = "\n".join(lines[start:end])
        lower = block_text.lower()
        matched = sorted({term for term in INTEREST if term.lower() in lower})
        if matched:
            excerpts: list[dict[str, Any]] = []
            for j in range(start, end):
                ll = lines[j].lower()
                terms = [t for t in INTEREST if t.lower() in ll]
                if terms:
                    a = max(start, j - 2)
                    b = min(end, j + 3)
                    excerpts.append({
                        "start_line": a + 1,
                        "end_line": b,
                        "terms": terms,
                        "text": "\n".join(f"{k+1}: {lines[k]}" for k in range(a, b)),
                    })
                    if len(excerpts) >= 40:
                        break
            blocks.append({"name": name, "start_line": start + 1, "end_line": end, "terms": matched, "excerpts": excerpts})

    literals = {
        "loads_npz": [],
        "saves_npz": [],
    }
    for i, line in enumerate(lines, start=1):
        ll = line.lower()
        if "np.load" in ll:
            literals["loads_npz"].append({"line": i, "text": line[:1000]})
        if "np.savez" in ll or "savez_compressed" in ll:
            literals["saves_npz"].append({"line": i, "text": line[:1000]})

    return {
        "path": str(path.resolve()),
        "sha256": sha256_file(path),
        "line_count": len(lines),
        "signatures": signatures,
        "relevant_blocks": blocks,
        "io_literals": literals,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract exact callable/input/output replay contract from adjudicated canonical ARCANA hydrology sources without executing historical source.")
    ap.add_argument("--search-root", type=Path, required=True)
    ap.add_argument("--output", type=Path, default=Path("R5_17_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT.json"))
    args = ap.parse_args()

    root = args.search_root.resolve()
    if not root.is_dir():
        raise NotADirectoryError(root)

    located = locate_exact_sources(root)
    representatives: dict[str, Path] = {}
    for suffix, candidates in located.items():
        if candidates:
            representatives[suffix] = sorted(candidates, key=lambda p: len(str(p)))[0]

    exact_complete = len(representatives) == len(EXPECTED)
    inspected = {suffix: inspect_source(path) for suffix, path in representatives.items()}

    wb = inspected.get("src/arcana_worldsim/climate/water_balance.py", {})
    fin = inspected.get("src/arcana_worldsim/finalization/hydrology.py", {})
    replay_contract_ready = bool(exact_complete and wb.get("relevant_blocks") and fin.get("relevant_blocks"))

    status = (
        "PASS_R517_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT_CAPTURED"
        if replay_contract_ready else
        "BLOCKED_R517_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT_INCOMPLETE"
    )

    result = {
        "schema": "ARCANA_R5_17_B6_D1_CANONICAL_HYDROLOGY_REPLAY_CONTRACT_V1",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B6-D1",
        "purpose": "Extract the exact callable/input/output contract needed to reuse adjudicated canonical ARCANA hydrology for paleoclimate freshwater derivation without executing historical source during inspection.",
        "search_root": str(root),
        "expected_source_hashes": EXPECTED,
        "candidate_counts": {k: len(v) for k, v in located.items()},
        "representative_sources": inspected,
        "all_expected_generator_hashes_recovered": exact_complete,
        "replay_contract_ready_for_implementation_design": replay_contract_ready,
        "reuse_canonical_arcana": True,
        "external_provider_authorized": False,
        "source_executed": False,
        "freshwater_support_materialized": False,
        "canonical_mutation": False,
        "status": status,
        "next_if_pass": "R5.17-B6-D2_CANONICAL_PALEOHYDROLOGY_DERIVATION_IMPLEMENTATION",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({
        "status": status,
        "all_expected_generator_hashes_recovered": exact_complete,
        "replay_contract_ready_for_implementation_design": replay_contract_ready,
        "candidate_counts": result["candidate_counts"],
        "output": str(args.output.resolve()),
    }, indent=2))
    if status.startswith("BLOCKED_"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
