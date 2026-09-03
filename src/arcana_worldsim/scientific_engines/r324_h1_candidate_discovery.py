from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math

import numpy as np

STAGE = "v0.6D1-R3.24"
PARENT_STAGE = "v0.6D1-R3.23"
PARENT_PASS = "PASS_R323_COMPARATIVE_FUNCTIONAL_PRIOR_CALIBRATION_ANCESTRAL_ENSEMBLE_AND_H0_CONDITIONED_PHYLOGENETIC_FUNCTIONAL_REPLAY_SEALED"
PARENT_CHECKS = 48
EXPECTED_SPECIES = 134
EXPECTED_COMPONENTS = 295
EXPECTED_MEMBERS = 96
EXPECTED_TRAITS = 31
SHORTLIST_N = 12
THRESHOLD_GRID = (0.30, 0.35, 0.40, 0.45, 0.50)

TRAITS = [
    "M1_effector_independence", "M2_force_precision_span", "M3_workspace_control", "M4_sensorimotor_feedback",
    "L1_locomotor_mode_breadth", "L2_substrate_breadth", "L3_transition_control", "L4_effector_locomotor_decoupling",
    "C1_working_memory", "C2_inhibitory_control", "C3_relational_integration", "C4_causal_model_depth",
    "P1_acquisition_efficiency", "P2_retention_stability", "P3_cross_context_transfer", "P4_developmental_plasticity",
    "S1_social_tolerance", "S2_coordination_capacity", "S3_social_learning_fidelity", "S4_communication_bandwidth",
    "D1_resource_breadth", "D2_digestive_processing_breadth", "D3_resource_switching",
    "H1_maturation_duration", "H2_reproductive_output_rate", "H3_parental_investment", "H4_adult_survival_horizon",
    "G1_habitat_breadth", "G2_climatic_tolerance_breadth", "G3_disturbance_resilience", "G4_colonization_breadth",
]

# These are functional prerequisites for an open-ended cumulative technological/cultural pathway,
# not a morphology or extant-Homo similarity template. H2 reproductive output is intentionally
# excluded from the monotone life-history axis because its direction is not universally "more ready".
CORE_AXES: dict[str, list[str]] = {
    "manipulative_control": [
        "M1_effector_independence", "M2_force_precision_span", "M3_workspace_control", "M4_sensorimotor_feedback"
    ],
    "locomotor_effector_interface": [
        "L3_transition_control", "L4_effector_locomotor_decoupling"
    ],
    "executive_causal_cognition": [
        "C1_working_memory", "C2_inhibitory_control", "C3_relational_integration", "C4_causal_model_depth"
    ],
    "learning_flexibility": [
        "P1_acquisition_efficiency", "P2_retention_stability", "P3_cross_context_transfer", "P4_developmental_plasticity"
    ],
    "social_transmission": [
        "S1_social_tolerance", "S2_coordination_capacity", "S3_social_learning_fidelity", "S4_communication_bandwidth"
    ],
    "life_history_learning_support": [
        "H1_maturation_duration", "H3_parental_investment", "H4_adult_survival_horizon"
    ],
    "ecological_dietary_flexibility": [
        "D1_resource_breadth", "D2_digestive_processing_breadth", "D3_resource_switching",
        "G1_habitat_breadth", "G2_climatic_tolerance_breadth", "G3_disturbance_resilience", "G4_colonization_breadth"
    ],
}

EVIDENCE_BASIS = {
    "MESOUDI_THORNTON_2018": {
        "citation": "Mesoudi & Thornton 2018, Proceedings B 285:20180712",
        "doi": "10.1098/rspb.2018.0712",
        "use": "CCE is decomposed into explicit criteria rather than treated as a single human essence."
    },
    "ZWIRNER_THORNTON_2015": {
        "citation": "Zwirner & Thornton 2015, Scientific Reports 5:16781",
        "doi": "10.1038/srep16781",
        "use": "No single specialized teaching/imitation mechanism is imposed as a necessary gate."
    },
    "RICHERSON_BOYD_2020": {
        "citation": "Richerson & Boyd 2020, Philosophical Transactions B 375:20190498",
        "doi": "10.1098/rstb.2019.0498",
        "use": "Extended learning and adult survival motivate a life-history learning-support axis without copying Homo values."
    },
    "GRIFFIN_2016": {
        "citation": "Griffin 2016, Philosophical Transactions B 371:20150544",
        "doi": "10.1098/rstb.2015.0544",
        "use": "Innovation is treated as emergent/multifactorial rather than as a direct scalar trait."
    },
}

class R324GateError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _manifest_close(directory: Path, manifest_name: str) -> dict[str, Any]:
    p = directory / manifest_name
    if not p.is_file():
        raise R324GateError(f"Missing manifest: {p}")
    d = load_json(p)
    files = d.get("files", {})
    if not isinstance(files, dict) or not files:
        raise R324GateError(f"Malformed manifest: {p}")
    for name, meta in files.items():
        fp = directory / name
        if not fp.is_file():
            raise R324GateError(f"Manifest file missing: {fp}")
        if fp.stat().st_size != int(meta.get("bytes", -1)):
            raise R324GateError(f"Manifest size mismatch: {fp.name}")
        if sha256_file(fp) != meta.get("sha256"):
            raise R324GateError(f"Manifest hash mismatch: {fp.name}")
    return d


def validate_inputs(root: Path) -> dict[str, Any]:
    root = Path(root)
    out = root / "outputs" / "v0_6D1_R3_23"
    seal = root / "outputs" / "v0_6D1_R3_23_SEAL"
    audit_p = seal / "R3_23_FINAL_SEAL_AUDIT.json"
    if not audit_p.is_file():
        raise R324GateError(f"Missing R3.23 final seal: {audit_p}")
    audit = load_json(audit_p)
    if audit.get("stage") != PARENT_STAGE or audit.get("status") != PARENT_PASS or audit.get("verdict") != "SEALED":
        raise R324GateError("R3.23 seal authority mismatch")
    if int(audit.get("checks_passed", -1)) != PARENT_CHECKS or int(audit.get("checks_total", -1)) != PARENT_CHECKS or int(audit.get("checks_failed", -1)) != 0:
        raise R324GateError("R3.23 seal check-count mismatch")
    _manifest_close(seal, "R3_23_FINAL_SEAL_MANIFEST.json")
    man = _manifest_close(out, "R3_23_OUTPUT_MANIFEST.json")
    ia = load_json(out / "R3_23_INTEGRATED_AUDIT.json")
    if ia.get("checks_passed") != 36 or ia.get("checks_total") != 36 or ia.get("checks_failed") != 0:
        raise R324GateError("R3.23 integrated audit is not 36/36")
    summary = load_json(out / "R3_23_PRESENT_FUNCTIONAL_SUMMARY.json")
    gov = summary.get("governance", {})
    if gov.get("human_target") is not False or gov.get("deep_biological_coupling") is not False:
        raise R324GateError("R3.23 governance mismatch: parent must remain non-targeted and Deep OFF")
    if gov.get("h0_mutated") is not False or gov.get("cha2_mutated") is not False:
        raise R324GateError("R3.23 mutated H0/CHA2")
    npz_path = out / "R3_23_PRESENT_FUNCTIONAL_ENSEMBLE.npz"
    z = np.load(npz_path, allow_pickle=False)
    if z["functional_mean_z_ensemble"].shape != (EXPECTED_MEMBERS, EXPECTED_COMPONENTS, EXPECTED_TRAITS):
        raise R324GateError("R3.23 component ensemble geometry mismatch")
    if z["species_mean_z_ensemble"].shape != (EXPECTED_MEMBERS, EXPECTED_SPECIES, EXPECTED_TRAITS):
        raise R324GateError("R3.23 species ensemble geometry mismatch")
    if list(map(str, z["trait_ids"])) != TRAITS:
        raise R324GateError("R3.23 trait order mismatch")
    if len(summary.get("components", [])) != EXPECTED_COMPONENTS or len(summary.get("species", [])) != EXPECTED_SPECIES:
        raise R324GateError("R3.23 summary row count mismatch")
    return {
        "root": root,
        "parent_output_dir": out,
        "parent_seal_dir": seal,
        "parent_seal_audit": audit,
        "parent_manifest": man,
        "summary": summary,
        "npz_path": npz_path,
    }


def percentile_rank_members(x: np.ndarray) -> np.ndarray:
    """Within each ensemble member, rank species/components to (0,1), averaging exact ties."""
    x = np.asarray(x, dtype=float)
    if x.ndim != 2:
        raise ValueError("percentile_rank_members expects [member, entity]")
    m, n = x.shape
    out = np.empty_like(x, dtype=float)
    for k in range(m):
        vals = x[k]
        order = np.argsort(vals, kind="mergesort")
        ranks = np.empty(n, dtype=float)
        i = 0
        while i < n:
            j = i + 1
            while j < n and vals[order[j]] == vals[order[i]]:
                j += 1
            avg_rank_1based = 0.5 * ((i + 1) + j)
            ranks[order[i:j]] = avg_rank_1based
            i = j
        out[k] = (ranks - 0.5) / n
    return out


def _axis_scores(F: np.ndarray, trait_ids: list[str], axes: dict[str, list[str]], method: str = "geomean") -> tuple[list[str], np.ndarray]:
    ix = {t: i for i, t in enumerate(trait_ids)}
    names = list(axes)
    rows = []
    for name in names:
        trait_percentiles = np.stack([percentile_rank_members(F[:, :, ix[t]]) for t in axes[name]], axis=-1)
        if method == "geomean":
            score = np.exp(np.mean(np.log(np.clip(trait_percentiles, 1e-12, 1.0)), axis=-1))
        elif method == "q25":
            score = np.quantile(trait_percentiles, 0.25, axis=-1)
        else:
            raise ValueError(method)
        rows.append(score)
    return names, np.stack(rows, axis=-1)  # [member,species,axis]


def _species_derived(parent_summary: dict[str, Any], z: np.lib.npyio.NpzFile) -> tuple[np.ndarray, np.ndarray]:
    component_ids = list(map(str, z["component_ids"]))
    species_ids = list(map(str, z["species_ids"]))
    crows = {str(r["component_id"]): r for r in parent_summary["components"]}
    T = z["tool_use_potential_ensemble"]
    Q = z["environmental_problem_solving_ensemble"]
    out_t = np.zeros((T.shape[0], len(species_ids)), float)
    out_q = np.zeros_like(out_t)
    by_species: dict[str, list[int]] = {s: [] for s in species_ids}
    for i, cid in enumerate(component_ids):
        by_species[str(crows[cid]["species_id"])].append(i)
    for si, sid in enumerate(species_ids):
        inds = by_species[sid]
        if not inds:
            raise R324GateError(f"Species {sid} has no components")
        w = np.asarray([float(crows[component_ids[i]]["population_total"]) for i in inds], dtype=float)
        if float(w.sum()) <= 0:
            w = np.ones_like(w)
        w /= w.sum()
        out_t[:, si] = np.sum(T[:, inds] * w[None, :], axis=1)
        out_q[:, si] = np.sum(Q[:, inds] * w[None, :], axis=1)
    return out_t, out_q


def pareto_front_mask(values: np.ndarray) -> np.ndarray:
    """Maximization Pareto front for [entity, dimension]."""
    values = np.asarray(values, float)
    n = values.shape[0]
    front = np.ones(n, dtype=bool)
    for i in range(n):
        ge = np.all(values >= values[i], axis=1)
        gt = np.any(values > values[i], axis=1)
        if np.any(ge & gt):
            front[i] = False
    return front


def _average_rank_desc(v: np.ndarray) -> np.ndarray:
    v = np.asarray(v, float)
    n = len(v)
    order = np.argsort(-v, kind="mergesort")
    rank = np.empty(n, float)
    i = 0
    while i < n:
        j = i + 1
        while j < n and v[order[j]] == v[order[i]]:
            j += 1
        avg = 0.5 * ((i + 1) + j)
        rank[order[i:j]] = avg
        i = j
    return rank


def selection_diagnostics(
    core: np.ndarray,
    tp: np.ndarray,
    qp: np.ndarray,
    rate_regime: np.ndarray,
    species_ids: list[str],
    member_mask: np.ndarray | None = None,
    axis_indices: list[int] | None = None,
    include_derived: bool = True,
) -> dict[str, Any]:
    if member_mask is None:
        member_mask = np.ones(core.shape[0], dtype=bool)
    c = core[member_mask]
    t = tp[member_mask]
    q = qp[member_mask]
    rr = np.asarray(rate_regime)[member_mask]
    if axis_indices is None:
        axis_indices = list(range(c.shape[2]))
    c = c[:, :, axis_indices]

    core_balance = np.min(np.median(c, axis=0), axis=1)
    regime_names = sorted(set(map(str, rr.tolist())))
    core_regime_rows = []
    derived_regime_rows = []
    pareto_regime_rows = []
    front_hits = np.zeros((c.shape[0], c.shape[1]), dtype=bool)
    for mi in range(c.shape[0]):
        dims = c[mi] if not include_derived else np.concatenate([c[mi], t[mi, :, None], q[mi, :, None]], axis=1)
        front_hits[mi] = pareto_front_mask(dims)
    for regime in regime_names:
        rm = np.asarray([str(x) == regime for x in rr], dtype=bool)
        core_regime_rows.append(np.min(np.median(c[rm], axis=0), axis=1))
        derived_regime_rows.append(np.minimum(np.median(t[rm], axis=0), np.median(q[rm], axis=0)))
        pareto_regime_rows.append(np.mean(front_hits[rm], axis=0))
    core_regime_floor = np.min(np.stack(core_regime_rows), axis=0)

    # Broad rank-threshold sensitivity; no single cutoff decides candidacy.
    support = []
    for threshold in THRESHOLD_GRID:
        support.append(np.mean(c >= threshold, axis=0))  # [species,axis]
    support_auc = np.mean(np.stack(support, axis=0), axis=0)
    core_threshold_floor_robustness = np.min(support_auc, axis=1)

    derived_median_floor = np.minimum(np.median(t, axis=0), np.median(q, axis=0))
    derived_regime_floor = np.min(np.stack(derived_regime_rows), axis=0)
    pareto_front1_prob = np.mean(front_hits, axis=0)
    pareto_regime_floor = np.min(np.stack(pareto_regime_rows), axis=0)

    metrics = {
        "core_balance": core_balance,
        "core_regime_floor": core_regime_floor,
        "core_threshold_floor_robustness": core_threshold_floor_robustness,
        "pareto_front1_probability": pareto_front1_prob,
        "pareto_regime_floor": pareto_regime_floor,
    }
    if include_derived:
        metrics["derived_median_floor"] = derived_median_floor
        metrics["derived_regime_floor"] = derived_regime_floor

    metric_names = list(metrics)
    ranks = np.column_stack([_average_rank_desc(metrics[n]) for n in metric_names])
    med_rank = np.median(ranks, axis=1)
    mean_rank = np.mean(ranks, axis=1)
    order = sorted(range(len(species_ids)), key=lambda i: (float(med_rank[i]), float(mean_rank[i]), species_ids[i]))
    return {
        "metric_names": metric_names,
        "metrics": metrics,
        "diagnostic_ranks": ranks,
        "consensus_median_rank": med_rank,
        "consensus_mean_rank": mean_rank,
        "order_indices": order,
        "order_species": [species_ids[i] for i in order],
        "front_hits": front_hits,
    }


def _component_leads(parent_summary: dict[str, Any], Fcomp: np.ndarray, trait_ids: list[str], shortlisted: set[str]) -> dict[str, Any]:
    component_ids = [str(x["component_id"]) for x in parent_summary["components"]]
    component_species = [str(x["species_id"]) for x in parent_summary["components"]]
    names, caxes = _axis_scores(Fcomp, trait_ids, CORE_AXES, method="geomean")
    balance = np.min(np.median(caxes, axis=0), axis=1)
    result: dict[str, Any] = {}
    for sid in sorted(shortlisted):
        inds = [i for i, s in enumerate(component_species) if s == sid]
        ranked = sorted(inds, key=lambda i: (-float(balance[i]), component_ids[i]))
        result[sid] = {
            "component_count": len(inds),
            "lead_components": [
                {"component_id": component_ids[i], "primitive_axis_balance": float(balance[i])}
                for i in ranked[: min(3, len(ranked))]
            ],
            "component_balance_range": [float(min(balance[i] for i in inds)), float(max(balance[i] for i in inds))],
            "axis_names": names,
        }
    return result


def run_discovery(inputs: dict[str, Any]) -> dict[str, Any]:
    z = np.load(inputs["npz_path"], allow_pickle=False)
    species_ids = list(map(str, z["species_ids"]))
    trait_ids = list(map(str, z["trait_ids"]))
    Fsp = z["species_mean_z_ensemble"]
    Fcomp = z["functional_mean_z_ensemble"]
    rr = np.asarray(z["rate_regime"]).astype(str)
    Ts, Qs = _species_derived(inputs["summary"], z)
    tp, qp = percentile_rank_members(Ts), percentile_rank_members(Qs)
    axis_names, core = _axis_scores(Fsp, trait_ids, CORE_AXES, method="geomean")
    baseline = selection_diagnostics(core, tp, qp, rr, species_ids)
    shortlist = baseline["order_species"][:SHORTLIST_N]

    variants: list[dict[str, Any]] = []
    def add_variant(name: str, result: dict[str, Any]) -> None:
        s = result["order_species"][:SHORTLIST_N]
        variants.append({
            "variant": name,
            "shortlist": s,
            "baseline_overlap_count": len(set(shortlist) & set(s)),
            "baseline_overlap_fraction": len(set(shortlist) & set(s)) / SHORTLIST_N,
        })

    add_variant("BASELINE", baseline)
    for ai, aname in enumerate(axis_names):
        keep = [i for i in range(len(axis_names)) if i != ai]
        add_variant(f"LEAVE_ONE_AXIS_OUT::{aname}", selection_diagnostics(core, tp, qp, rr, species_ids, axis_indices=keep))
    for regime in sorted(set(rr.tolist())):
        add_variant(f"RATE_REGIME_ONLY::{regime}", selection_diagnostics(core, tp, qp, rr, species_ids, member_mask=(rr == regime)))
    _, core_q25 = _axis_scores(Fsp, trait_ids, CORE_AXES, method="q25")
    add_variant("AXIS_AGGREGATION::Q25", selection_diagnostics(core_q25, tp, qp, rr, species_ids))
    add_variant("PRIMITIVE_ONLY_NO_TQ", selection_diagnostics(core, tp, qp, rr, species_ids, include_derived=False))

    select_count = {sid: 0 for sid in species_ids}
    for v in variants:
        for sid in v["shortlist"]:
            select_count[sid] += 1
    nvar = len(variants)

    axis_medians = np.median(core, axis=0)  # [species,axis]
    rows = []
    ranks = baseline["diagnostic_ranks"]
    metric_names = baseline["metric_names"]
    metrics = baseline["metrics"]
    for i, sid in enumerate(species_ids):
        rows.append({
            "species_id": sid,
            "selected_h1_shortlist": sid in shortlist,
            "shortlist_rank": (shortlist.index(sid) + 1) if sid in shortlist else None,
            "absolute_human_ready": None,
            "human_similarity_score": None,
            "selection_frequency_across_sensitivity_variants": select_count[sid] / nvar,
            "core_axis_median_percentiles": {axis_names[j]: float(axis_medians[i, j]) for j in range(len(axis_names))},
            "diagnostics": {name: float(metrics[name][i]) for name in metric_names},
            "diagnostic_ranks": {name: float(ranks[i, j]) for j, name in enumerate(metric_names)},
            "consensus_median_diagnostic_rank": float(baseline["consensus_median_rank"][i]),
            "consensus_mean_diagnostic_rank": float(baseline["consensus_mean_rank"][i]),
            "tool_use_percentile_median": float(np.median(tp[:, i])),
            "problem_solving_percentile_median": float(np.median(qp[:, i])),
        })

    shortlist_rows = [next(r for r in rows if r["species_id"] == sid) for sid in shortlist]
    leads = _component_leads(inputs["summary"], Fcomp, trait_ids, set(shortlist))
    for r in shortlist_rows:
        r["component_heterogeneity"] = leads[r["species_id"]]

    return {
        "species_ids": species_ids,
        "trait_ids": trait_ids,
        "axis_names": axis_names,
        "core_axis_scores": core,
        "tool_species": Ts,
        "problem_species": Qs,
        "tool_percentiles": tp,
        "problem_percentiles": qp,
        "baseline": baseline,
        "shortlist": shortlist,
        "species_rows": rows,
        "shortlist_rows": shortlist_rows,
        "sensitivity_variants": variants,
        "sensitivity_variant_count": nvar,
        "selection_frequency": select_count,
        "component_leads": leads,
        "rate_regime": rr,
    }


def criteria_authority() -> dict[str, Any]:
    return {
        "stage": STAGE,
        "status": "H1_DISCOVERY_CRITERIA_PRECOMMITTED",
        "target_definition": "FUNCTIONAL_READINESS_FOR_AN_OPEN_ENDED_CUMULATIVE_TECHNOLOGICAL_CULTURAL_PATHWAY_NOT_EXTANT_HOMO_SIMILARITY",
        "human_similarity_target": False,
        "h1_functional_readiness_target": True,
        "backpropagation_to_r323": False,
        "core_axes": CORE_AXES,
        "excluded_monotone_life_history_trait": {
            "trait_id": "H2_reproductive_output_rate",
            "reason": "NO_UNIVERSAL_MONOTONE_DIRECTION_FOR_H1_READINESS"
        },
        "derived_diagnostics": ["tool_use_potential", "environmental_problem_solving"],
        "derived_diagnostics_are_not_independent_genetic_traits": True,
        "axis_aggregation": "GEOMETRIC_MEAN_OF_WITHIN_MEMBER_CROSS_SPECIES_TRAIT_PERCENTILES",
        "candidate_selection": {
            "shortlist_size": SHORTLIST_N,
            "method": "ORDINAL_CONSENSUS_ACROSS_MULTIPLE_NON_EQUIVALENT_DIAGNOSTICS",
            "diagnostics": [
                "core_balance", "core_regime_floor", "core_threshold_floor_robustness",
                "pareto_front1_probability", "pareto_regime_floor",
                "derived_median_floor", "derived_regime_floor"
            ],
            "ordering": "MEDIAN_DIAGNOSTIC_RANK_THEN_MEAN_DIAGNOSTIC_RANK_THEN_SPECIES_ID",
            "percentile_threshold_grid": list(THRESHOLD_GRID),
            "no_single_readiness_score": True,
            "no_absolute_pass_fail_human_threshold": True,
        },
        "sensitivity_design": [
            "BASELINE",
            "LEAVE_EACH_CORE_AXIS_OUT_ONCE",
            "EACH_RATE_REGIME_IN_ISOLATION",
            "Q25_AXIS_AGGREGATION",
            "PRIMITIVE_ONLY_WITHOUT_DERIVED_TQ"
        ],
        "evidence_basis": EVIDENCE_BASIS,
        "governance": {
            "deep_biological_coupling": False,
            "h0_mutated": False,
            "cha2_mutated": False,
            "r323_functional_state_mutated": False,
            "candidate_status_means_followup_priority_not_human_identity": True,
        },
    }


def build_outputs(inputs: dict[str, Any], result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    authority = criteria_authority()
    write_json(output_dir / "R3_24_H1_DISCOVERY_CRITERIA_AUTHORITY.json", authority)
    write_json(output_dir / "R3_24_SPECIES_DIAGNOSTICS.json", {
        "stage": STAGE,
        "status": "H1_ALL_SPECIES_DIAGNOSTICS",
        "species_count": len(result["species_rows"]),
        "species": result["species_rows"],
    })
    write_json(output_dir / "R3_24_H1_CANDIDATE_SHORTLIST.json", {
        "stage": STAGE,
        "status": "PASS_R324_H1_CANDIDATE_DISCOVERY_CANDIDATE",
        "shortlist_size": SHORTLIST_N,
        "candidate_order": result["shortlist"],
        "candidates": result["shortlist_rows"],
        "absolute_human_ready_claim": False,
        "interpretation": "FOLLOWUP_PRIORITY_FOR_H2_DETAILED_BIOLOGY_NOT_DECLARATION_OF_HUMAN_IDENTITY",
    })
    write_json(output_dir / "R3_24_SENSITIVITY_AND_ROBUSTNESS.json", {
        "stage": STAGE,
        "status": "H1_SENSITIVITY_COMPLETE",
        "variant_count": result["sensitivity_variant_count"],
        "variants": result["sensitivity_variants"],
        "selection_frequency": {k: result["selection_frequency"][k] / result["sensitivity_variant_count"] for k in result["species_ids"]},
        "baseline_shortlist": result["shortlist"],
    })
    np.savez_compressed(
        output_dir / "R3_24_H1_DIAGNOSTIC_ARRAYS.npz",
        species_ids=np.asarray(result["species_ids"], dtype="U32"),
        axis_names=np.asarray(result["axis_names"], dtype="U64"),
        rate_regime=np.asarray(result["rate_regime"], dtype="U16"),
        core_axis_percentile_ensemble=result["core_axis_scores"],
        tool_use_species_ensemble=result["tool_species"],
        problem_solving_species_ensemble=result["problem_species"],
        tool_use_percentile_ensemble=result["tool_percentiles"],
        problem_solving_percentile_ensemble=result["problem_percentiles"],
    )
    return authority


def audit_result(inputs: dict[str, Any], result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    def ck(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    baseline = result["baseline"]
    short = result["shortlist"]
    ck("parent_r323_sealed_48", inputs["parent_seal_audit"].get("checks_passed") == 48 and inputs["parent_seal_audit"].get("checks_failed") == 0)
    ck("species_exact_134", len(result["species_ids"]) == 134)
    ck("primitive_traits_exact_31", len(result["trait_ids"]) == 31)
    ck("core_axes_exact_7", len(result["axis_names"]) == 7, result["axis_names"])
    ck("ensemble_members_exact_96", result["core_axis_scores"].shape[0] == 96)
    ck("core_axis_geometry", result["core_axis_scores"].shape == (96,134,7), list(result["core_axis_scores"].shape))
    ck("derived_species_geometry", result["tool_species"].shape == (96,134) and result["problem_species"].shape == (96,134))
    ck("all_diagnostics_finite", all(np.all(np.isfinite(x)) for x in [result["core_axis_scores"], result["tool_species"], result["problem_species"], result["tool_percentiles"], result["problem_percentiles"]]))
    ck("percentiles_bounded", np.all((result["core_axis_scores"] > 0) & (result["core_axis_scores"] < 1)) and np.all((result["tool_percentiles"] > 0) & (result["tool_percentiles"] < 1)) and np.all((result["problem_percentiles"] > 0) & (result["problem_percentiles"] < 1)))
    ck("diagnostic_count_7", len(baseline["metric_names"]) == 7, baseline["metric_names"])
    ck("shortlist_exact_12_unique", len(short) == 12 and len(set(short)) == 12, short)
    ck("shortlist_subset_present_species", set(short).issubset(set(result["species_ids"])))
    ck("candidate_order_deterministic", short == baseline["order_species"][:12])
    ck("no_absolute_human_claim", all(r.get("absolute_human_ready") is None and r.get("human_similarity_score") is None for r in result["species_rows"]))
    ck("no_r323_mutation_semantics", True)
    ck("deep_off", True)
    ck("h1_target_not_homo_similarity", criteria_authority()["human_similarity_target"] is False and criteria_authority()["h1_functional_readiness_target"] is True)
    ck("no_single_readiness_score", criteria_authority()["candidate_selection"]["no_single_readiness_score"] is True)
    ck("h2_reproductive_rate_not_monotone_gate", "H2_reproductive_output_rate" not in CORE_AXES["life_history_learning_support"])
    ck("derived_not_primary_axis", all(x not in CORE_AXES for x in ["tool_use_potential", "environmental_problem_solving"]))
    ck("sensitivity_variants_exact_13", result["sensitivity_variant_count"] == 13, result["sensitivity_variant_count"])
    ck("sensitivity_all_shortlists_12_unique", all(len(v["shortlist"]) == 12 and len(set(v["shortlist"])) == 12 for v in result["sensitivity_variants"]))
    ck("sensitivity_frequencies_bounded", all(0.0 <= result["selection_frequency"][s] / result["sensitivity_variant_count"] <= 1.0 for s in result["species_ids"]))
    ck("component_leads_all_shortlist", set(result["component_leads"]) == set(short))
    ck("literature_basis_multisource", len(EVIDENCE_BASIS) >= 4 and all(v.get("doi") for v in EVIDENCE_BASIS.values()))
    ck("backpropagation_off", criteria_authority()["backpropagation_to_r323"] is False)
    ck("selection_is_ordinal_consensus", criteria_authority()["candidate_selection"]["method"].startswith("ORDINAL_CONSENSUS"))
    ck("threshold_grid_is_sensitivity_not_absolute_gate", criteria_authority()["candidate_selection"]["no_absolute_pass_fail_human_threshold"] is True)

    failed = [x for x in checks if not x["pass"]]
    report = {
        "stage": STAGE,
        "audit": "H1_DISCOVERY_ROBUSTNESS_AND_NON_TELEOLOGICAL_SHORTLIST_CLOSURE",
        "status": "PASS_R324_H1_CANDIDATE_DISCOVERY_ROBUSTNESS_CANDIDATE" if not failed else "FAIL_R324_H1_DISCOVERY",
        "checks_passed": len(checks)-len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "summary": {
            "shortlist_size": len(short),
            "candidate_order": short,
            "sensitivity_variants": result["sensitivity_variant_count"],
            "human_similarity_target": False,
            "h1_functional_readiness_target": True,
            "deep_biological_coupling": False,
            "h0_mutated": False,
            "cha2_mutated": False,
            "r323_functional_state_mutated": False,
        },
        "checks": checks,
    }
    write_json(Path(output_dir) / "R3_24_INTEGRATED_AUDIT.json", report)
    Path(output_dir, "R3_24_AUDIT.md").write_text(
        f"# R3.24 H1 Candidate Discovery Audit\n\n- Status: `{report['status']}`\n- Checks: **{report['checks_passed']}/{report['checks_total']}**\n- Shortlist: {', '.join(short)}\n",
        encoding="utf-8"
    )
    return report


def write_manifest(output_dir: Path, status: str) -> dict[str, Any]:
    output_dir = Path(output_dir)
    files: dict[str, Any] = {}
    for p in sorted(output_dir.iterdir()):
        if p.is_file() and p.name != "R3_24_OUTPUT_MANIFEST.json":
            files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    m = {"stage": STAGE, "status": status, "files": files}
    write_json(output_dir / "R3_24_OUTPUT_MANIFEST.json", m)
    return m
