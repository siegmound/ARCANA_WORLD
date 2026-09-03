from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

STAGE = "v0.6D1-R3.21"
PASS = "PASS_R321_H0_PRESENT_LINEAGE_REGISTRY_HISTORICAL_CLOSURE_AND_FUNCTIONAL_PHENOTYPE_FORK_READINESS_SEALED"
EXPECTED_JSON_SHA = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_NPZ_SHA = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_SPECIES = 134
EXPECTED_COMPONENTS = 295
EXPECTED_HIST_SPECIES = 348
EXPECTED_EVENTS = 2925
EXPECTED_POP = 1217.2506240828814
EXPECTED_EVENT_HIST = {
    "paleogeographic_support_loss_remap": 1513,
    "deme_fission": 838,
    "speciation": 228,
    "CHA1_species_extinction": 212,
    "deme_coalescence": 130,
    "ordinary_background_extinction": 2,
    "CHA1_high_resolution_event_bridge_complete": 1,
    "post_CHA1_ordinary_lifecycle_thaw": 1,
}
EXPECTED_FILES = {
    "R3_21_PRESENT_LINEAGE_REGISTRY.json",
    "R3_21_PRESENT_COMPONENT_REGISTRY.json",
    "R3_21_HISTORICAL_LINEAGE_CLOSURE.json",
    "R3_21_REDUCED_GENETIC_STATE.npz",
    "R3_21_REDUCED_GENETIC_STATE_SUMMARY.json",
    "R3_21_FUNCTIONAL_PHENOTYPE_FORK_INTERFACE.json",
    "R3_21_AUDIT_SUMMARY.json",
    "R3_21_AUDIT.md",
    "R3_21_OUTPUT_MANIFEST.json",
}
REDUCED_KEYS = (
    "reduced_va_within",
    "reduced_ancestry_covariance",
    "reduced_neutral_segregation_potential",
    "reduced_adaptive_coordinate",
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def discover(root: Path, suffix: str, expected: str) -> Path | None:
    seen: set[Path] = set()
    for base in (root / "local_runs", root / "outputs", root):
        if not base.exists():
            continue
        it = base.rglob(f"*{suffix}") if base != root else base.glob(f"*{suffix}")
        for p in it:
            if not p.is_file():
                continue
            try:
                rp = p.resolve()
            except OSError:
                rp = p
            if rp in seen:
                continue
            seen.add(rp)
            try:
                if sha256_file(p) == expected:
                    return p
            except OSError:
                pass
    return None


def walk_find(obj: Any, key: str) -> Any:
    hits: list[tuple[int, Any]] = []
    def rec(x: Any, depth: int) -> None:
        if isinstance(x, dict):
            if key in x:
                hits.append((depth, x[key]))
            for v in x.values():
                rec(v, depth + 1)
        elif isinstance(x, list):
            for v in x:
                rec(v, depth + 1)
    rec(obj, 0)
    if not hits:
        raise KeyError(key)
    hits.sort(key=lambda t: t[0])
    return hits[0][1]


def source_pair_ok(obj: dict[str, Any]) -> bool:
    s = obj.get("source_checkpoint", {})
    return s.get("json_sha256") == EXPECTED_JSON_SHA and s.get("npz_sha256") == EXPECTED_NPZ_SHA


def audit(root: Path, out: Path, checkpoint_json: Path, checkpoint_npz: Path) -> tuple[dict[str, Any], bool]:
    checks: list[dict[str, Any]] = []
    def check(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    check("source_json_hash_exact", sha256_file(checkpoint_json) == EXPECTED_JSON_SHA)
    check("source_npz_hash_exact", sha256_file(checkpoint_npz) == EXPECTED_NPZ_SHA)
    check("output_dir_exists", out.is_dir(), str(out))
    actual_files = {p.name for p in out.iterdir() if p.is_file()} if out.is_dir() else set()
    check("expected_output_files_present", EXPECTED_FILES <= actual_files, sorted(EXPECTED_FILES - actual_files))

    manifest = load_json(out / "R3_21_OUTPUT_MANIFEST.json")
    manifest_rows = manifest.get("files", {})
    manifest_ok = True
    manifest_detail: dict[str, Any] = {}
    for name, meta in manifest_rows.items():
        p = out / name
        ok = p.is_file() and sha256_file(p) == meta.get("sha256") and p.stat().st_size == meta.get("bytes")
        manifest_detail[name] = ok
        manifest_ok &= ok
    check("output_manifest_hash_and_size_closure", manifest_ok and set(manifest_rows) == (EXPECTED_FILES - {"R3_21_OUTPUT_MANIFEST.json"}), manifest_detail)
    check("manifest_source_provenance_exact", source_pair_ok(manifest))

    lineage_doc = load_json(out / "R3_21_PRESENT_LINEAGE_REGISTRY.json")
    comp_doc = load_json(out / "R3_21_PRESENT_COMPONENT_REGISTRY.json")
    hist_doc = load_json(out / "R3_21_HISTORICAL_LINEAGE_CLOSURE.json")
    reduced_summary = load_json(out / "R3_21_REDUCED_GENETIC_STATE_SUMMARY.json")
    fork = load_json(out / "R3_21_FUNCTIONAL_PHENOTYPE_FORK_INTERFACE.json")
    summary = load_json(out / "R3_21_AUDIT_SUMMARY.json")

    for name, obj in (
        ("lineage", lineage_doc), ("component", comp_doc), ("historical", hist_doc),
        ("reduced_summary", reduced_summary), ("fork", fork), ("audit_summary", summary),
    ):
        check(f"{name}_source_provenance_exact", source_pair_ok(obj))

    lineages = lineage_doc.get("lineages", [])
    components = comp_doc.get("components", [])
    hist_species = hist_doc.get("historical_species_registry", [])
    events = hist_doc.get("historical_events", [])

    lineage_ids = [str(x.get("lineage_id")) for x in lineages]
    component_ids = [str(x.get("component_id")) for x in components]
    check("present_species_exact_134", len(lineages) == EXPECTED_SPECIES and len(set(lineage_ids)) == EXPECTED_SPECIES, len(lineages))
    check("present_components_exact_295", len(components) == EXPECTED_COMPONENTS and len(set(component_ids)) == EXPECTED_COMPONENTS, len(components))
    check("historical_registry_exact_348", len(hist_species) == EXPECTED_HIST_SPECIES, len(hist_species))
    check("historical_events_exact_2925", len(events) == EXPECTED_EVENTS, len(events))

    # Component <-> present-lineage exact partition.
    comp_by_species: dict[str, set[str]] = {}
    comp_pop = 0.0
    for c in components:
        sid = str(c.get("species_id"))
        cid = str(c.get("component_id"))
        comp_by_species.setdefault(sid, set()).add(cid)
        comp_pop += float(c.get("population_total", 0.0))
    partition_ok = True
    lineage_comp_union: set[str] = set()
    lineage_pop = 0.0
    for row in lineages:
        sid = str(row.get("species_id"))
        cids = {str(x) for x in row.get("component_ids", [])}
        lineage_comp_union |= cids
        partition_ok &= cids == comp_by_species.get(sid, set())
        partition_ok &= int(row.get("component_count", -1)) == len(cids)
        lineage_pop += float(row.get("population_total", 0.0))
    partition_ok &= lineage_comp_union == set(component_ids)
    partition_ok &= set(comp_by_species) == set(lineage_ids)
    check("component_species_partition_exact", partition_ok)

    check("component_population_exact", math.isclose(comp_pop, EXPECTED_POP, rel_tol=0.0, abs_tol=1e-9), comp_pop)
    check("lineage_population_exact", math.isclose(lineage_pop, EXPECTED_POP, rel_tol=0.0, abs_tol=1e-9), lineage_pop)
    check("summary_population_exact", math.isclose(float(summary.get("total_population", float("nan"))), EXPECTED_POP, rel_tol=0.0, abs_tol=1e-12), summary.get("total_population"))
    check("population_accounting_roundoff_only", abs(float(summary.get("population_accounting_error", float("inf")))) <= 1e-9, summary.get("population_accounting_error"))

    # Historical registry parent closure and cycle-free graph.
    hist_map: dict[str, dict[str, Any]] = {}
    for row in hist_species:
        sid = row.get("species_id") or row.get("lineage_id") or row.get("daughter_species_id")
        if sid is not None:
            hist_map[str(sid)] = row
    parent_ok = len(hist_map) == EXPECTED_HIST_SPECIES
    cycle_ok = True
    for sid, row in hist_map.items():
        seen = {sid}
        cur = sid
        while True:
            p = hist_map[cur].get("parent_species_id")
            if p in (None, "", "None"):
                break
            p = str(p)
            if p not in hist_map:
                parent_ok = False
                break
            if p in seen:
                cycle_ok = False
                break
            seen.add(p)
            cur = p
    check("historical_parent_complete", parent_ok)
    check("historical_ancestry_acyclic", cycle_ok)

    chains_ok = True
    for row in lineages:
        sid = str(row.get("species_id"))
        chain = [str(x) for x in row.get("ancestry_chain_root_to_present", [])]
        chains_ok &= bool(chain) and chain[-1] == sid
        chains_ok &= int(row.get("lineage_depth", -1)) == len(chain) - 1
        chains_ok &= all(x in hist_map for x in chain)
        for a, b in zip(chain, chain[1:]):
            chains_ok &= str(hist_map[b].get("parent_species_id")) == a
    check("present_lineage_chains_exact", chains_ok)

    event_hist = Counter(str(e.get("event_type")) for e in events)
    check("historical_event_histogram_exact", dict(event_hist) == EXPECTED_EVENT_HIST, dict(sorted(event_hist.items())))
    extinct_refs: set[str] = set()
    for e in events:
        t = str(e.get("event_type", "")).lower()
        if "extinct" in t or "extinction" in t:
            extinct_refs.update(str(x) for x in e.get("species_refs", []))
    check("no_extinct_species_present", not (set(lineage_ids) & extinct_refs), sorted(set(lineage_ids) & extinct_refs))

    # Functional phenotype must still be schema-only everywhere.
    lineages_no_pheno = all(
        isinstance(r.get("functional_phenotype"), dict)
        and r["functional_phenotype"].get("values") is None
        and r["functional_phenotype"].get("human_readiness_score") is None
        and r["functional_phenotype"].get("status") == "NOT_MATERIALIZED_R3_21"
        for r in lineages
    )
    fork_domains = fork.get("domains_reserved_for_r3_22", [])
    fork_null = all(
        d.get("value") is None and d.get("heritability") is None and d.get("evolvability") is None
        and d.get("metabolic_ecological_cost") is None and d.get("correlations") is None
        and d.get("status") == "UNDEFINED_UNTIL_R3_22"
        for d in fork_domains
    )
    check("functional_phenotype_unmaterialized", lineages_no_pheno and fork_null and fork.get("composite_human_readiness_score") is None)
    check("functional_fork_generic_no_human_target", fork.get("scope") == "GENERIC_ALL_LINEAGES_NO_HUMAN_TARGET")
    check("functional_fork_deep_off", fork.get("deep_coupling") == "OFF")

    # Summary governance gates.
    check("deep_off_triple_evidence", summary.get("deep_biological_coupling_off") is True and len(summary.get("deep_evidence", [])) >= 3 and all(x.get("value") is False for x in summary.get("deep_evidence", [])))
    check("no_new_biology", summary.get("no_new_biology_executed") is True)
    check("no_human_target", summary.get("no_human_target") is True)
    check("no_h0_or_cha2_mutation", summary.get("no_h0_or_cha2_mutation") is True)
    check("no_functional_values_materialized", summary.get("no_functional_phenotype_values_materialized") is True)
    check("exact_zero_inaccessible_population", float(summary.get("inaccessible_population_0ka", float("nan"))) == 0.0)

    # Reduced-state geometry and bit-exact preservation from the SEALED R3.19 NPZ.
    source_meta = load_json(checkpoint_json)
    src_component_ids = [str(x) for x in walk_find(source_meta, "component_ids")]
    with np.load(checkpoint_npz, allow_pickle=False) as src, np.load(out / "R3_21_REDUCED_GENETIC_STATE.npz", allow_pickle=False) as dst:
        reduced_keys_ok = all(k in src.files and k in dst.files for k in REDUCED_KEYS)
        check("reduced_keys_present_source_and_output", reduced_keys_ok)
        dst_cids = [str(x) for x in dst["component_ids"].tolist()]
        check("reduced_component_order_bit_exact_authority", dst_cids == src_component_ids and len(dst_cids) == EXPECTED_COMPONENTS)
        bit_exact = {}
        finite = {}
        for k in REDUCED_KEYS:
            if k in src.files and k in dst.files:
                bit_exact[k] = src[k].dtype == dst[k].dtype and src[k].shape == dst[k].shape and np.array_equal(src[k], dst[k])
                finite[k] = bool(np.isfinite(dst[k]).all())
            else:
                bit_exact[k] = False
                finite[k] = False
        check("reduced_state_bit_exact_preservation", all(bit_exact.values()), bit_exact)
        check("reduced_state_all_finite", all(finite.values()), finite)
        shape_ok = (
            dst["reduced_va_within"].shape == (295, 3)
            and dst["reduced_ancestry_covariance"].shape == (295, 3)
            and dst["reduced_neutral_segregation_potential"].shape == (295, 295, 3)
            and dst["reduced_adaptive_coordinate"].shape == (295, 3)
        )
        check("reduced_state_canonical_geometry_295x3", shape_ok, {k: list(dst[k].shape) for k in REDUCED_KEYS})
        nonneg_ok = bool((dst["reduced_va_within"] >= 0).all() and (dst["reduced_neutral_segregation_potential"] >= 0).all())
        check("reduced_nonnegative_authority_fields", nonneg_ok)

    # Summary must reflect all canonical counters and reduced-state availability.
    rp = summary.get("reduced_state_presence", {})
    check("summary_counts_exact", summary.get("present_species") == EXPECTED_SPECIES and summary.get("present_components") == EXPECTED_COMPONENTS and summary.get("historical_registry_species") == EXPECTED_HIST_SPECIES and summary.get("historical_events") == EXPECTED_EVENTS)
    check("summary_reduced_state_all_present", all(rp.get(k) is True for k in ("va_within_present", "ancestry_covariance_present", "neutral_segregation_potential_present", "adaptive_coordinate_present")))

    passed = sum(1 for c in checks if c["pass"])
    failed = [c for c in checks if not c["pass"]]
    report = {
        "stage": STAGE,
        "audit": "FINAL_SEAL_INDEPENDENT_OUTPUT_AND_AUTHORITY_CLOSURE",
        "status": PASS if not failed else "FAIL_R321_FINAL_SEAL_AUDIT",
        "verdict": "SEALED" if not failed else "FAIL_CLOSED",
        "source_checkpoint": {"json_sha256": EXPECTED_JSON_SHA, "npz_sha256": EXPECTED_NPZ_SHA},
        "checks_passed": passed,
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "event_histogram": dict(sorted(event_hist.items())),
        "checks": checks,
    }
    return report, not failed


def write_report(report: dict[str, Any], seal_dir: Path) -> None:
    seal_dir.mkdir(parents=True, exist_ok=True)
    j = seal_dir / "R3_21_FINAL_SEAL_AUDIT.json"
    j.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    lines = [
        "# v0.6D1-R3.21 — Final Seal Audit",
        "",
        f"- status: `{report['status']}`",
        f"- verdict: `{report['verdict']}`",
        f"- checks: `{report['checks_passed']}/{report['checks_total']} PASS`",
        f"- failed: `{report['checks_failed']}`",
        "",
        "This seal is a read-only audit of the R3.21 derived registry against the exact SEALED R3.19 checkpoint authority.",
    ]
    (seal_dir / "R3_21_FINAL_SEAL_AUDIT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    manifest = {"stage": STAGE, "files": {}}
    for p in sorted(seal_dir.iterdir()):
        if p.is_file() and p.name != "R3_21_FINAL_SEAL_MANIFEST.json":
            manifest["files"][p.name] = {"sha256": sha256_file(p), "bytes": p.stat().st_size}
    (seal_dir / "R3_21_FINAL_SEAL_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--output-dir", type=Path)
    ap.add_argument("--checkpoint-json", type=Path)
    ap.add_argument("--checkpoint-npz", type=Path)
    ap.add_argument("--seal-dir", type=Path)
    ns = ap.parse_args()
    root = ns.root.resolve()
    out = (ns.output_dir or (root / "outputs" / "v0_6D1_R3_21")).resolve()
    cj = ns.checkpoint_json or discover(root, ".json", EXPECTED_JSON_SHA)
    cn = ns.checkpoint_npz or discover(root, ".npz", EXPECTED_NPZ_SHA)
    if cj is None or cn is None:
        print(json.dumps({"stage": STAGE, "status": "FAIL_CLOSED", "error": "Exact SEALED R3.19 checkpoint pair not found"}, indent=2))
        return 2
    try:
        report, ok = audit(root, out, cj, cn)
    except Exception as exc:
        print(json.dumps({"stage": STAGE, "status": "FAIL_CLOSED", "error": f"{type(exc).__name__}: {exc}"}, indent=2))
        return 2
    seal_dir = (ns.seal_dir or (root / "outputs" / "v0_6D1_R3_21_SEAL")).resolve()
    write_report(report, seal_dir)
    print(json.dumps(report, indent=2))
    return 0 if ok else 3


if __name__ == "__main__":
    raise SystemExit(main())
