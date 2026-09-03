from __future__ import annotations

from dataclasses import dataclass, asdict, replace
from collections import Counter, defaultdict
from contextlib import contextmanager
from typing import Any
import numpy as np

import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
import d3_additive_variance_v0_6_3D3_3A as av

R35_STAGE_ID = "v0.6D1-R3.5"
R35_SCOPE = "TIME_RESOLVED_VA_HEADROOM_INSTRUMENTATION_AND_DYNAMIC_CEILING_SENSITIVITY"
R35_DEEP_BIOLOGICAL_COUPLING_ENABLED = False


@dataclass(frozen=True)
class R35Config(r34.R34Config):
    # The scientific defaults remain R3.4. R3.5 adds only instrumentation and
    # exposes the already-existing safety ceiling as a sensitivity parameter.
    variance_ceiling_normalized: float = 0.08
    telemetry_enabled: bool = True
    telemetry_near_ceiling_fraction: float = 0.99
    diagnostic_unclipped_ceiling: float = 1.0e6


def _q_matrix(va: np.ndarray, root_idx: np.ndarray, root_species_ids: list[str],
              metadata: dict, body_mass_scale: float) -> np.ndarray:
    out = np.zeros_like(np.asarray(va, dtype=float), dtype=float)
    for di, si0 in enumerate(np.asarray(root_idx, dtype=int)):
        sid = root_species_ids[int(si0)]
        sc = av.trait_scales(metadata[sid], body_mass_scale)
        out[di] = av.normalize_variance(va[di], sc)
    return out


def _q_summary(q: np.ndarray, root_idx: np.ndarray, root_species_ids: list[str],
               component_count: int) -> dict[str, Any]:
    q = np.asarray(q, dtype=float)
    if q.size == 0:
        return {
            "max_q": 0.0, "median_q": 0.0, "p95_q": 0.0, "p99_q": 0.0,
            "per_axis_max": [0.0, 0.0, 0.0], "max_deme_index": None,
            "max_axis": None, "max_root_species": None,
        }
    flat_idx = int(np.argmax(q))
    di, ax = np.unravel_index(flat_idx, q.shape)
    return {
        "max_q": float(np.max(q)),
        "median_q": float(np.median(q)),
        "p95_q": float(np.quantile(q, 0.95)),
        "p99_q": float(np.quantile(q, 0.99)),
        "per_axis_max": [float(x) for x in np.max(q, axis=0)],
        "max_deme_index": int(di),
        "max_axis": int(ax),
        "max_root_species": str(root_species_ids[int(root_idx[di])]),
        "component_count": int(component_count),
    }


def _threshold_stats(q: np.ndarray, ceiling: float, frac: float) -> dict[str, Any]:
    q = np.asarray(q, dtype=float)
    threshold = float(frac) * float(ceiling)
    return {
        "threshold_q": threshold,
        "count_ge_threshold": int(np.count_nonzero(q >= threshold - 1e-15)),
        "fraction_ge_threshold": float(np.count_nonzero(q >= threshold - 1e-15) / max(q.size, 1)),
        "count_ge_ceiling": int(np.count_nonzero(q >= float(ceiling) - 1e-15)),
        "count_gt_ceiling": int(np.count_nonzero(q > float(ceiling) + 1e-12)),
    }


@contextmanager
def _instrument_additive_variance(cfg: R35Config):
    """Intercept the existing D3.3A operators without changing their outputs.

    Scientific state is produced by the exact parent functions.  A second
    *diagnostic only* Riccati call with a very high cap estimates the unclipped
    homeostasis result.  That diagnostic value is never fed back into the run.
    """
    original_gf = av.gene_flow_moment_mix
    original_nf = av.advance_nonflow_variance
    pending_pre_gf: list[np.ndarray] = []
    records: list[dict[str, Any]] = []

    def gf_wrapper(trait, va, population_total, gene_flow, intrinsic_ri,
                   root_species_index, av_cfg):
        pending_pre_gf.append(np.asarray(va, dtype=float).copy())
        return original_gf(trait, va, population_total, gene_flow, intrinsic_ri,
                           root_species_index, av_cfg)

    def nf_wrapper(va, trait_before_selection, targets, populations,
                   generation_time, root_idx, root_species_ids, metadata,
                   body_mass_scale, dt_years, av_cfg):
        # Parent scientific result first.
        actual, components = original_nf(
            va, trait_before_selection, targets, populations, generation_time,
            root_idx, root_species_ids, metadata, body_mass_scale, dt_years, av_cfg
        )
        # Same D3.3A Riccati operator, diagnostic only, with non-binding cap.
        diag_cfg = replace(av_cfg, mutation_variance_ceiling_normalized=float(cfg.diagnostic_unclipped_ceiling))
        diagnostic_unclipped, _ = original_nf(
            va, trait_before_selection, targets, populations, generation_time,
            root_idx, root_species_ids, metadata, body_mass_scale, dt_years, diag_cfg
        )
        pre_gf_va = pending_pre_gf.pop(0) if pending_pre_gf else np.asarray(va, dtype=float).copy()
        q_pre = _q_matrix(pre_gf_va, root_idx, root_species_ids, metadata, body_mass_scale)
        q_post_gf = _q_matrix(va, root_idx, root_species_ids, metadata, body_mass_scale)
        q_unclipped = _q_matrix(diagnostic_unclipped, root_idx, root_species_ids, metadata, body_mass_scale)
        q_post = _q_matrix(actual, root_idx, root_species_ids, metadata, body_mass_scale)
        ceiling = float(av_cfg.mutation_variance_ceiling_normalized)
        clipped = q_unclipped > ceiling + 1e-15
        near = q_post >= (float(cfg.telemetry_near_ceiling_fraction) * ceiling - 1e-15)
        axis_names = ("thermal", "aridity", "body")
        clipped_reservoirs = []
        near_reservoirs = []
        for di, ax in np.argwhere(clipped):
            clipped_reservoirs.append({
                "deme_index": int(di),
                "root_species": str(root_species_ids[int(root_idx[int(di)])]),
                "axis": axis_names[int(ax)],
                "q_unclipped": float(q_unclipped[int(di), int(ax)]),
                "q_after_homeostasis": float(q_post[int(di), int(ax)]),
            })
        for di, ax in np.argwhere(near):
            near_reservoirs.append({
                "deme_index": int(di),
                "root_species": str(root_species_ids[int(root_idx[int(di)])]),
                "axis": axis_names[int(ax)],
                "q": float(q_post[int(di), int(ax)]),
            })
        records.append({
            "step_index": len(records),
            "dt_years": float(dt_years),
            "ceiling_q": ceiling,
            "before_gene_flow": _q_summary(q_pre, root_idx, root_species_ids, len(q_pre)),
            "after_gene_flow": _q_summary(q_post_gf, root_idx, root_species_ids, len(q_post_gf)),
            "after_homeostasis_unclipped": _q_summary(q_unclipped, root_idx, root_species_ids, len(q_unclipped)),
            "after_homeostasis": _q_summary(q_post, root_idx, root_species_ids, len(q_post)),
            "before_gene_flow_threshold": _threshold_stats(q_pre, ceiling, cfg.telemetry_near_ceiling_fraction),
            "after_gene_flow_threshold": _threshold_stats(q_post_gf, ceiling, cfg.telemetry_near_ceiling_fraction),
            "after_homeostasis_threshold": _threshold_stats(q_post, ceiling, cfg.telemetry_near_ceiling_fraction),
            "homeostasis_clipping_count": int(np.count_nonzero(clipped)),
            "homeostasis_clipping_fraction": float(np.count_nonzero(clipped) / max(clipped.size, 1)),
            "homeostasis_unclipped_excess_max": float(max(0.0, np.max(q_unclipped) - ceiling)),
            "clipped_reservoirs": clipped_reservoirs,
            "near_ceiling_reservoirs": near_reservoirs,
        })
        return actual, components

    av.gene_flow_moment_mix = gf_wrapper
    av.advance_nonflow_variance = nf_wrapper
    try:
        yield records
    finally:
        av.gene_flow_moment_mix = original_gf
        av.advance_nonflow_variance = original_nf


def _attach_time_and_events(records: list[dict[str, Any]], result: dict, cfg: R35Config) -> None:
    events_by_elapsed: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for e in result.get("events", []):
        if "elapsed_year" not in e:
            continue
        k = int(round(float(e["elapsed_year"])))
        events_by_elapsed[k].append(e)
    for rec in records:
        elapsed = float((int(rec["step_index"]) + 1) * cfg.biology_cadence_years)
        rec["elapsed_year"] = elapsed
        rec["elapsed_myr"] = elapsed / 1e6
        rec["age_ma"] = float(cfg.start_age_ma - elapsed / 1e6)
        evs = events_by_elapsed.get(int(round(elapsed)), [])
        counts = Counter(str(e.get("event", "UNKNOWN")) for e in evs)
        rec["event_counts_same_step"] = dict(sorted(counts.items()))
        rec["event_ids_same_step"] = [
            str(e.get("daughter_species_id") or e.get("daughter_component_id") or
                e.get("survivor_component_id") or e.get("parent_component_id") or "")
            for e in evs
        ]


def summarize_headroom_telemetry(records: list[dict[str, Any]], cfg: R35Config) -> dict[str, Any]:
    if not records:
        return {"record_count": 0}
    peak = max(records, key=lambda r: r["after_homeostasis"]["max_q"])
    peak_gf = max(records, key=lambda r: r["after_gene_flow"]["max_q"])
    peak_unclipped = max(records, key=lambda r: r["after_homeostasis_unclipped"]["max_q"])
    clipping_steps = [r for r in records if r["homeostasis_clipping_count"] > 0]
    near_steps = [r for r in records if r["after_homeostasis_threshold"]["count_ge_threshold"] > 0]
    per_axis = [max(float(r["after_homeostasis"]["per_axis_max"][i]) for r in records) for i in range(3)]
    return {
        "record_count": len(records),
        "biology_cadence_years": float(cfg.biology_cadence_years),
        "ceiling_q": float(cfg.variance_ceiling_normalized),
        "near_ceiling_fraction": float(cfg.telemetry_near_ceiling_fraction),
        "peak_after_homeostasis_q": float(peak["after_homeostasis"]["max_q"]),
        "peak_after_homeostasis_age_ma": float(peak["age_ma"]),
        "peak_after_homeostasis_root_species": peak["after_homeostasis"]["max_root_species"],
        "peak_after_gene_flow_q": float(peak_gf["after_gene_flow"]["max_q"]),
        "peak_after_gene_flow_age_ma": float(peak_gf["age_ma"]),
        "peak_unclipped_homeostasis_q": float(peak_unclipped["after_homeostasis_unclipped"]["max_q"]),
        "peak_unclipped_homeostasis_age_ma": float(peak_unclipped["age_ma"]),
        "steps_with_homeostasis_clipping": len(clipping_steps),
        "fraction_steps_with_homeostasis_clipping": float(len(clipping_steps) / len(records)),
        "total_clipped_reservoir_step_contacts": int(sum(r["homeostasis_clipping_count"] for r in records)),
        "steps_with_ge_99pct_ceiling_after_homeostasis": len(near_steps),
        "fraction_steps_with_ge_99pct_ceiling_after_homeostasis": float(len(near_steps) / len(records)),
        "per_axis_peak_after_homeostasis": per_axis,
        "event_context_at_peak": peak.get("event_counts_same_step", {}),
    }


def run(common, a1, metadata_rows, cfg: R35Config):
    # R3.5 is instrumentation around the already-validated R3.4 scientific
    # runtime. The parent run is not reimplemented.
    parent_cfg = r34.R34Config(**{
        k: v for k, v in asdict(cfg).items()
        if k in r34.R34Config.__dataclass_fields__
    })
    if not cfg.telemetry_enabled:
        out = r34.run(common, a1, metadata_rows, parent_cfg)
        out["stage"] = R35_STAGE_ID
        out["r35_telemetry"] = []
        out["r35_headroom_summary"] = {"record_count": 0, "telemetry_enabled": False}
        return out
    with _instrument_additive_variance(cfg) as records:
        out = r34.run(common, a1, metadata_rows, parent_cfg)
    _attach_time_and_events(records, out, cfg)
    out["stage"] = R35_STAGE_ID
    out["config"] = asdict(cfg)
    out["r35_telemetry"] = records
    out["r35_headroom_summary"] = summarize_headroom_telemetry(records, cfg)
    out["authority"]["r3_5_instrumentation_semantics"] = (
        "NON_INVASIVE_WRAPPERS_AROUND_EXACT_D3_3A_GENE_FLOW_AND_RICCATI_OPERATORS"
    )
    out["authority"]["r3_5_unclipped_probe_semantics"] = (
        "SECOND_DIAGNOSTIC_ONLY_EXACT_RICCATI_CALL_WITH_NON_BINDING_CAP_NOT_FED_BACK_TO_STATE"
    )
    return out
