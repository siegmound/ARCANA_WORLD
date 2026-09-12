from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import numpy as np


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "R5_17_B7_A1_NATURAL_FOOD_SUPPORT_AUTHORITY_PREFLIGHT.json"

A1 = ROOT / "references" / "v0_6D1_R3" / "FULL_A1_REFERENCE_210_0Ma.npz"
A1_SHA256 = "9469118bff69cfc4a5bbfe398f382224f887d81a69581e3a654d08ea11fc604f"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


def git_paths() -> list[str]:
    cp = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return sorted(set(cp.stdout.splitlines()))


def path_group(
    paths: list[str],
    patterns: tuple[str, ...],
    suffixes: tuple[str, ...] | None = None,
) -> list[str]:
    out: list[str] = []

    for p in paths:
        low = p.lower()

        if suffixes is not None:
            if Path(low).suffix not in suffixes:
                continue

        if any(re.search(pattern, p, flags=re.IGNORECASE) for pattern in patterns):
            out.append(p)

    return sorted(set(out))


def summarize_paths(paths: list[str], limit: int = 250) -> list[dict[str, Any]]:
    docs: list[dict[str, Any]] = []

    for p in paths[:limit]:
        path = ROOT / p
        if not path.is_file():
            continue

        docs.append(
            {
                "path": p,
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            }
        )

    return docs


def npz_schema(path: Path) -> dict[str, Any]:
    doc: dict[str, Any] = {
        "path": rel(path),
        "sha256": sha256_file(path),
        "size_bytes": path.stat().st_size,
        "keys": [],
        "arrays": {},
    }

    with np.load(path, allow_pickle=False) as z:
        doc["keys"] = list(z.files)

        for key in z.files:
            arr = np.asarray(z[key])

            item: dict[str, Any] = {
                "shape": list(arr.shape),
                "dtype": str(arr.dtype),
                "size": int(arr.size),
            }

            if arr.size and np.issubdtype(arr.dtype, np.number):
                finite = np.isfinite(arr)
                item["finite"] = bool(finite.all())

                if finite.any():
                    vals = arr[finite].astype(np.float64, copy=False)
                    item["min"] = float(vals.min())
                    item["max"] = float(vals.max())

            doc["arrays"][key] = item

    return doc


def content_hits(
    paths: list[str],
    terms: tuple[str, ...],
    max_files: int = 400,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []

    for p in paths:
        if len(hits) >= max_files:
            break

        path = ROOT / p

        if path.suffix.lower() not in {
            ".py", ".md", ".txt", ".json", ".csv", ".ps1"
        }:
            continue

        try:
            text = path.read_text(
                encoding="utf-8",
                errors="replace",
            )
        except OSError:
            continue

        present = [
            term
            for term in terms
            if term.lower() in text.lower()
        ]

        if present:
            hits.append(
                {
                    "path": p,
                    "matched_terms": present,
                }
            )

    return hits


def main() -> int:
    paths = git_paths()
    checks: dict[str, bool] = {}

    # ------------------------------------------------------------------------
    # A1 inherited trophic resource authority
    # ------------------------------------------------------------------------

    checks["a1_present"] = A1.is_file()

    a1_doc: dict[str, Any] | None = None

    if A1.is_file():
        a1_doc = npz_schema(A1)

        checks["a1_known_sha"] = (
            a1_doc["sha256"].lower() == A1_SHA256
        )

        required = (
            "age_ma",
            "browse_forage",
            "low_forage",
            "wetland_forage",
            "total_edible_forage",
        )

        checks["a1_required_channels_present"] = all(
            key in a1_doc["keys"]
            for key in required
        )

        if checks["a1_required_channels_present"]:
            with np.load(A1, allow_pickle=False) as z:
                browse = np.asarray(z["browse_forage"], dtype=np.float64)
                low = np.asarray(z["low_forage"], dtype=np.float64)
                wet = np.asarray(z["wetland_forage"], dtype=np.float64)
                total = np.asarray(z["total_edible_forage"], dtype=np.float64)

                closure = browse + low + wet
                delta = total - closure

                max_abs = float(np.max(np.abs(delta)))

                checks["a1_forage_closure_consistent"] = bool(
                    np.allclose(
                        total,
                        closure,
                        rtol=1e-6,
                        atol=1e-6,
                    )
                )

                a1_doc["forage_closure"] = {
                    "max_abs_error": max_abs,
                    "rtol": 1e-6,
                    "atol": 1e-6,
                    "consistent": checks["a1_forage_closure_consistent"],
                }

                a1_doc["age_ma_values"] = (
                    np.asarray(z["age_ma"], dtype=float).tolist()
                )
    else:
        checks["a1_known_sha"] = False
        checks["a1_required_channels_present"] = False
        checks["a1_forage_closure_consistent"] = False

    # ------------------------------------------------------------------------
    # R3.33 environmental authority discovery
    # ------------------------------------------------------------------------

    r333 = path_group(
        paths,
        (
            r"R3[_-]33",
            r"r333",
            r"holocene.*environment.*domest",
        ),
    )

    checks["r333_authority_surface_found"] = bool(r333)

    # ------------------------------------------------------------------------
    # R3.34 producer authority discovery
    # ------------------------------------------------------------------------

    r334 = path_group(
        paths,
        (
            r"R3[_-]34",
            r"r334",
            r"producer.*domest",
        ),
    )

    checks["r334_authority_surface_found"] = bool(r334)

    # ------------------------------------------------------------------------
    # H0 wild-fauna / present-biology authority discovery
    # ------------------------------------------------------------------------

    h0 = path_group(
        paths,
        (
            r"R3[_-]19",
            r"R3[_-]21",
            r"R3[_-]22",
            r"R3[_-]23",
            r"H0.*PRESENT",
            r"PRESENT.*LINEAGE",
            r"FUNCTIONAL.*PHENOTYPE",
            r"FUNCTIONAL.*ENSEMBLE",
        ),
    )

    checks["h0_faunal_authority_surface_found"] = bool(h0)

    # ------------------------------------------------------------------------
    # Semantic source evidence
    # ------------------------------------------------------------------------

    forage_source_hits = content_hits(
        paths,
        (
            "browse_forage",
            "low_forage",
            "wetland_forage",
            "total_edible_forage",
        ),
    )

    producer_source_hits = content_hits(
        paths,
        (
            "resource_abundance",
            "harvest_return",
            "propagation_opportunity",
            "build_producer_landscape",
        ),
    )

    human_conditioning_hits = content_hits(
        paths,
        (
            "contact_opportunity",
            "subsistence readiness",
            "landscape management",
        ),
    )

    checks["forage_semantic_source_hits_found"] = bool(forage_source_hits)
    checks["producer_semantic_source_hits_found"] = bool(producer_source_hits)

    # ------------------------------------------------------------------------
    # Aquatic / marine discovery
    # ------------------------------------------------------------------------

    marine_name_hits = path_group(
        paths,
        (
            r"marine",
            r"aquatic",
            r"fish",
            r"ocean",
            r"coastal.*resource",
        ),
    )

    marine_content_hits = content_hits(
        paths,
        (
            "marine resource",
            "aquatic resource",
            "fish biomass",
            "marine productivity",
            "aquatic exploitation",
        ),
    )

    # ------------------------------------------------------------------------
    # Decision
    # ------------------------------------------------------------------------

    required_checks = (
        "a1_present",
        "a1_known_sha",
        "a1_required_channels_present",
        "a1_forage_closure_consistent",
        "r333_authority_surface_found",
        "r334_authority_surface_found",
        "h0_faunal_authority_surface_found",
    )

    core_ok = all(checks[name] for name in required_checks)

    if core_ok:
        status = (
            "PASS_R517_B7_A1_NATURAL_FOOD_SUPPORT_"
            "AUTHORITY_SCHEMA_COVERAGE_PREFLIGHT"
        )
        decision = (
            "AUTHORIZE_B7_A2_SEMANTIC_BINDING_"
            "AND_TEMPORAL_COVERAGE_ADJUDICATION"
        )
    else:
        status = (
            "BLOCKED_R517_B7_A1_REQUIRED_AUTHORITY_SURFACE_INCOMPLETE"
        )
        decision = (
            "RECOVER_OR_ADJUDICATE_MISSING_AUTHORITY_BEFORE_B7_A2"
        )

    result = {
        "schema": "ARCANA_R517_B7_A1_NATURAL_FOOD_SUPPORT_PREFLIGHT_V2",
        "stage": "v0.6D1-R5.17",
        "subphase": "R5.17-B7-A1",
        "status": status,
        "decision": decision,
        "checks": checks,
        "a1_native_trophic_authority": a1_doc,
        "r333_authority_surface": summarize_paths(r333),
        "r334_authority_surface": summarize_paths(r334),
        "h0_faunal_authority_surface": summarize_paths(h0),
        "semantic_source_hits": {
            "forage": forage_source_hits,
            "producer": producer_source_hits,
            "human_conditioning": human_conditioning_hits,
        },
        "aquatic_marine_discovery": {
            "filename_hits": summarize_paths(marine_name_hits),
            "content_hits": marine_content_hits,
            "materialization_decision": (
                "UNADJUDICATED_SOURCE_DISCOVERY_ONLY"
            ),
        },
        "governance": {
            "natural_pre_management_only": True,
            "r332_readiness_used": False,
            "human_technology_used": False,
            "food_processing_used": False,
            "storage_used": False,
            "landscape_management_used": False,
            "domestication_used": False,
            "agriculture_used": False,
            "population_target_used": False,
            "k_x_t_materialized": False,
            "new_food_equation_materialized": False,
            "canonical_mutation": False,
            "external_engine_executed": False,
            "a1_forage_interpreted_as_physical_biomass": False,
            "a1_forage_interpreted_as_human_calories": False,
            "r333_domestication_candidate_subset_used_as_total_wild_fauna": False,
            "r334_propagation_opportunity_used_as_natural_food_support": False,
        },
    }

    OUT.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "status": status,
                "decision": decision,
                "checks_passed": sum(bool(v) for v in checks.values()),
                "checks_total": len(checks),
                "r333_surface_count": len(r333),
                "r334_surface_count": len(r334),
                "h0_surface_count": len(h0),
                "marine_filename_hits": len(marine_name_hits),
                "marine_content_hits": len(marine_content_hits),
                "output": str(OUT),
            },
            indent=2,
        )
    )

    return 0 if core_ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
