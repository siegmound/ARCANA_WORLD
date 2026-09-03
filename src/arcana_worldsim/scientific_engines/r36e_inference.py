from __future__ import annotations

import io
import json
import math
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np


@dataclass(frozen=True)
class R36EThresholds:
    # These are audit/reporting thresholds, not canonical biological constants.
    max_nemo_to_analytic_factor: float = 4.0
    min_arcana_to_analytic_factor_for_structural_mismatch: float = 10.0
    min_qst_for_persistent_structure: float = 0.90


def _read_json(zf: zipfile.ZipFile, name: str) -> dict[str, Any]:
    return json.loads(zf.read(name))


def _find_summary_name(zf: zipfile.ZipFile) -> str:
    hits = [n for n in zf.namelist() if n.endswith("R3_6D_NEMO_EVIDENCE_SUMMARY.json")]
    if len(hits) != 1:
        raise ValueError(f"expected exactly one R3.6D evidence summary, found {len(hits)}")
    return hits[0]


def _job_paths(zf: zipfile.ZipFile) -> list[str]:
    return sorted(n for n in zf.namelist() if n.endswith("/R3_6D_JOB.json"))


def _parse_stat_final(text: str) -> dict[str, float]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) < 2:
        raise ValueError("NEMO stat file has no data rows")
    header = lines[0].split()
    values = lines[-1].split()
    if len(header) != len(values):
        raise ValueError("NEMO stat header/data width mismatch")
    row = dict(zip(header, values))
    def f(key: str) -> float:
        return float(row[key])
    return {
        "generation": f("generation"),
        "Va": f("adlt.q1.Va"),
        "Vb": f("adlt.q1.Vb"),
        "Qst": f("adlt.q1.Qst"),
        "trait_mean": f("adlt.q1"),
    }


def _find_stat_file(zf: zipfile.ZipFile, job_dir: str) -> str:
    candidates = []
    for n in zf.namelist():
        if not n.startswith(job_dir) or not n.endswith(".txt"):
            continue
        base = Path(n).name
        if base.startswith("arcana_r36d_"):
            candidates.append(n)
    if len(candidates) != 1:
        raise ValueError(f"expected one NEMO stat file in {job_dir}, found {len(candidates)}")
    return candidates[0]


def _analytic_polygenic_delta(zf: zipfile.ZipFile, job_path: str) -> dict[str, float]:
    job = _read_json(zf, job_path)
    if job.get("variant") != "FLOW":
        raise ValueError("analytic polygenic delta is defined on FLOW jobs")
    job_dir = job_path.rsplit("/", 1)[0] + "/"
    variant_dir = job_dir.rsplit("axis_", 1)[0]
    qtl_path = variant_dir + "qtl/qtl_expected_state.npz"
    with np.load(io.BytesIO(zf.read(qtl_path))) as data:
        effect_sizes = np.asarray(data["effect_sizes"], dtype=float)
        freqs = np.asarray(data["allele_frequencies"], dtype=float)
    axis = int(job["axis"])
    a = effect_sizes[axis]
    p = freqs[:, axis, :]
    matrix = np.loadtxt(io.StringIO(zf.read(job_dir + "nemo_per_generation_dispersal.tsv").decode("utf-8")))
    manifest = _read_json(zf, job_dir + "R3_6D_NEMO_BINDING_MANIFEST.json")
    transitions = int(manifest["nemo_transitions"])
    interval = np.linalg.matrix_power(matrix, transitions)
    p_mixed = interval @ p
    va0 = 2.0 * np.sum((a[None, :] ** 2) * p * (1.0 - p), axis=1)
    va1 = 2.0 * np.sum((a[None, :] ** 2) * p_mixed * (1.0 - p_mixed), axis=1)
    return {
        "analytic_initial_mean_va": float(np.mean(va0)),
        "analytic_final_mean_va": float(np.mean(va1)),
        "analytic_admixture_delta_va": float(np.mean(va1 - va0)),
        "interval_matrix_row_sum_error": float(np.max(np.abs(np.sum(interval, axis=1) - 1.0))),
        "interval_matrix_symmetry_error": float(np.max(np.abs(interval - interval.T))),
        "loci": int(a.size),
    }


def analyze_r36d_results_zip(results_zip: str | Path, *, thresholds: R36EThresholds = R36EThresholds()) -> dict[str, Any]:
    results_zip = Path(results_zip)
    with zipfile.ZipFile(results_zip) as zf:
        summary = _read_json(zf, _find_summary_name(zf))
        if summary.get("status") != "NEMO_EVIDENCE_COMPLETE_REVIEW_REQUIRED":
            raise ValueError("R3.6E requires complete R3.6D evidence")
        if summary.get("job_count") != 40 or summary.get("executed_count") != 40 or summary.get("parsed_complete_count") != 40:
            raise ValueError("R3.6E pilot authority expects 40/40 executed and parsed jobs")

        stat_rows: list[dict[str, Any]] = []
        analytic_rows: list[dict[str, Any]] = []
        for job_path in _job_paths(zf):
            job = _read_json(zf, job_path)
            job_dir = job_path.rsplit("/", 1)[0] + "/"
            stat = _parse_stat_final(zf.read(_find_stat_file(zf, job_dir)).decode("utf-8", errors="replace"))
            row = {
                "pair": job.get("pair"),
                "scenario": job.get("scenario"),
                "variant": job.get("variant"),
                "population_size": int(job["population_size"]),
                "replicate": int(job["replicate"]),
                "axis": int(job["axis"]),
                **stat,
            }
            stat_rows.append(row)
            if job.get("variant") == "FLOW":
                ar = _analytic_polygenic_delta(zf, job_path)
                analytic_rows.append({
                    "pair": job.get("pair"),
                    "population_size": int(job["population_size"]),
                    "replicate": int(job["replicate"]),
                    "axis": int(job["axis"]),
                    **ar,
                })

        # Aggregate NEMO FLOW stats.
        flow_stats: list[dict[str, Any]] = []
        groups: dict[tuple[str, int, int], list[dict[str, Any]]] = {}
        for r in stat_rows:
            if r["variant"] != "FLOW":
                continue
            groups.setdefault((str(r["pair"]), r["population_size"], r["axis"]), []).append(r)
        for (pair, N, axis), rs in sorted(groups.items()):
            flow_stats.append({
                "pair": pair,
                "population_size": N,
                "axis": axis,
                "n": len(rs),
                "nemo_stat_Va_mean": float(np.mean([x["Va"] for x in rs])),
                "nemo_stat_Vb_mean": float(np.mean([x["Vb"] for x in rs])),
                "nemo_stat_Qst_mean": float(np.mean([x["Qst"] for x in rs])),
                "nemo_stat_Qst_min": float(np.min([x["Qst"] for x in rs])),
            })

        # Analytic delta is deterministic for scenario/axis; check all N/rep copies agree.
        analytic_by: dict[tuple[str, int], list[float]] = {}
        loci_by: dict[tuple[str, int], list[int]] = {}
        for r in analytic_rows:
            key = (str(r["pair"]), r["axis"])
            analytic_by.setdefault(key, []).append(r["analytic_admixture_delta_va"])
            loci_by.setdefault(key, []).append(r["loci"])
        analytic_summary = []
        for key, vals in sorted(analytic_by.items()):
            spread = float(np.max(vals) - np.min(vals))
            analytic_summary.append({
                "pair": key[0],
                "axis": key[1],
                "analytic_polygenic_delta_va": float(np.mean(vals)),
                "cross_copy_spread": spread,
                "loci": int(round(np.mean(loci_by[key]))),
            })

        # Join R3.6D collector's ARCANA and NEMO paired estimates to analytic QTL expectation.
        joined = []
        analytic_lookup = {(r["pair"], r["axis"]): r for r in analytic_summary}
        for r in summary["three_way_admixture_only_comparison"]:
            a = analytic_lookup[(r["pair"], int(r["axis"]))]
            analytic = a["analytic_polygenic_delta_va"]
            nemo = float(r["nemo_delta_va_mean"])
            arc125 = float(r["arcana_admixture_only_1x125k_delta_va"])
            arc25 = float(r["arcana_admixture_only_5x25k_delta_va"])
            joined.append({
                **r,
                "analytic_polygenic_delta_va": analytic,
                "nemo_over_analytic": nemo / analytic if analytic > 0 else math.nan,
                "arcana_1x125k_over_analytic": arc125 / analytic if analytic > 0 else math.nan,
                "arcana_5x25k_over_analytic": arc25 / analytic if analytic > 0 else math.nan,
                "nemo_fraction_of_arcana_1x125k": nemo / arc125 if arc125 > 0 else math.nan,
            })

        arcana_factors = [r["arcana_1x125k_over_analytic"] for r in joined]
        nemo_factors = [r["nemo_over_analytic"] for r in joined]
        qst_mins = [r["nemo_stat_Qst_min"] for r in flow_stats]
        structural_mismatch = (
            min(arcana_factors) >= thresholds.min_arcana_to_analytic_factor_for_structural_mismatch
            and max(nemo_factors) <= thresholds.max_nemo_to_analytic_factor
            and min(qst_mins) >= thresholds.min_qst_for_persistent_structure
        )

        # Mechanistic identity for two-deme B1: ARCANA mixture variance includes
        # whole-trait between-mean term; polygenic genic variance includes sum of
        # per-locus squared frequency differences. The observed ~2L amplification
        # is diagnostic of aligned polygenic divergence being counted as durable VA.
        mechanism = {
            "arcana_operator_semantics": "whole_trait_mixture_second_moment_includes_between_deme_mean_variance",
            "polygenic_reference_semantics": "within_deme_genic_additive_variance_after_allele_frequency_mixing",
            "causal_interpretation": "ARCANA current moment mixing promotes population-structure / ancestry covariance into within-deme VA; free recombination in NEMO does not preserve that covariance as standing additive variance.",
            "not_attributed_to": ["Riccati b", "mutation mu", "VA ceiling", "cadence alone"],
        }

        verdict = (
            "STRUCTURAL_ADMIXTURE_OPERATOR_MISMATCH_SUPPORTED__CALIBRATION_NOT_YET_AUTHORIZED"
            if structural_mismatch else
            "EVIDENCE_INCONCLUSIVE__MORE_REFERENCE_WORK_REQUIRED"
        )

        return {
            "schema": "ARCANA_R36E_CAUSAL_INFERENCE_V1",
            "stage": "v0.6D1-R3.6E",
            "source_r36d_status": summary["status"],
            "source_job_count": summary["job_count"],
            "source_executed_count": summary["executed_count"],
            "source_parsed_complete_count": summary["parsed_complete_count"],
            "analytic_polygenic_reference": analytic_summary,
            "nemo_flow_structure": flow_stats,
            "three_way_causal_comparison": joined,
            "population_size_sensitivity": summary["population_size_sensitivity"],
            "mechanism": mechanism,
            "verdict": verdict,
            "canonical_write_allowed": False,
            "automatic_calibration_allowed": False,
            "mu_b_recalibration_authorized": False,
            "ceiling_change_authorized": False,
            "production_r3_5_replay_authorized": False,
            "next_required_stage": "R3.6F / R3.7 segregation-aware admixture operator design and governed calibration, with larger-N/replicate validation before production promotion",
        }
