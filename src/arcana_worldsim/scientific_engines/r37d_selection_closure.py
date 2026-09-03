from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
import itertools
import json
import math
import zipfile

import numpy as np

from .segregation_potential_lifecycle import (
    ReducedGeneticLifecycleState,
    advance_directional_selection_coordinate,
)

R37D_STAGE = "v0.6D1-R3.7D"
R37D_PARENT_STAGE = "v0.6D1-R3.7C-R1"


def _read_effects(zf: zipfile.ZipFile, name: str, axis: int) -> np.ndarray:
    vals: list[tuple[int, float]] = []
    for line in zf.read(name).decode("utf-8").splitlines():
        if not line.strip() or line.startswith("trait"):
            continue
        tok = line.split("\t")
        if int(tok[1]) == int(axis):
            vals.append((int(tok[2]), float(tok[3])))
    vals.sort()
    out = np.asarray([v for _, v in vals], dtype=float)
    if out.ndim != 1 or out.size == 0 or np.any(~np.isfinite(out)):
        raise ValueError("invalid QTL effect table")
    return out


def _read_qfreq(zf: zipfile.ZipFile, name: str, locus_count: int) -> np.ndarray:
    lines = [x.strip() for x in zf.read(name).decode("utf-8").splitlines() if x.strip()]
    if not lines or lines[0].split()[:4] != ["pop", "trait", "locus", "allele"]:
        raise ValueError("unexpected qfreq format")
    pops = sorted({int(x.split()[0]) for x in lines[1:]})
    if len(pops) != 4:
        raise ValueError("R3.7D expects four NEMO patches")
    pidx = {p: i for i, p in enumerate(pops)}
    freq = np.full((4, locus_count), np.nan, dtype=float)
    for line in lines[1:]:
        tok = line.split()
        freq[pidx[int(tok[0])], int(tok[2]) - 1] = float(tok[-1])
    if np.any(~np.isfinite(freq)) or np.any(freq < -1e-12) or np.any(freq > 1 + 1e-12):
        raise ValueError("incomplete/invalid qfreq state")
    return np.clip(freq, 0.0, 1.0)


def _group_contrast(freq: np.ndarray) -> np.ndarray:
    f = np.asarray(freq, dtype=float)
    if f.ndim != 2 or f.shape[0] != 4:
        raise ValueError("group contrast requires four patches")
    return np.mean(f[[2, 3]], axis=0) - np.mean(f[[0, 1]], axis=0)


def geometric_adaptive_participation(
    effect_a: np.ndarray,
    selected_freq: np.ndarray,
    neutral_freq: np.ndarray,
) -> dict[str, float]:
    """Matched geometric participation for the selected-minus-neutral displacement.

    R3.7C's aggregate diagnostic used Delta S = S(selected)-S(neutral).
    Because S is quadratic, that subtraction contains a cross term with the
    neutral displacement and is not the squared norm of the adaptive displacement.

    R3.7D therefore forms the matched adaptive allele-frequency contrast first,
    then computes its squared segregation norm. This yields the exact reduced-
    order geometry needed by the R3.7A adaptive-coordinate mapping and obeys
    K <= number of loci by Cauchy-Schwarz.
    """
    a = np.asarray(effect_a, dtype=float)
    fs = np.asarray(selected_freq, dtype=float)
    fn = np.asarray(neutral_freq, dtype=float)
    if a.ndim != 1 or fs.shape != fn.shape or fs.shape != (4, a.size):
        raise ValueError("effect/frequency shape mismatch")
    dp = _group_contrast(fs) - _group_contrast(fn)
    weighted = a * dp
    dz = 2.0 * float(np.sum(weighted))
    s_adapt = 2.0 * float(np.sum(weighted * weighted))
    k = (dz * dz / (2.0 * s_adapt)) if s_adapt > 0 else float("nan")
    return {
        "adaptive_trait_divergence": dz,
        "geometric_adaptive_S": s_adapt,
        "geometric_K_eff": k,
        "active_locus_count": int(np.count_nonzero(np.abs(dp) > 1e-12)),
        "max_abs_adaptive_allele_contrast": float(np.max(np.abs(dp))) if dp.size else 0.0,
    }


def _summary(values: Iterable[float]) -> dict[str, float | int]:
    a = np.asarray(list(values), dtype=float)
    a = a[np.isfinite(a)]
    if not a.size:
        return {"n": 0}
    mean = float(np.mean(a))
    return {
        "n": int(a.size),
        "minimum": float(np.min(a)),
        "median": float(np.median(a)),
        "mean": mean,
        "maximum": float(np.max(a)),
        "cv": float(np.std(a) / abs(mean)) if mean != 0 else float("nan"),
    }


def _paired_signflip_p(diffs: Iterable[float]) -> float:
    d = np.asarray(list(diffs), dtype=float)
    if d.ndim != 1 or d.size == 0 or d.size > 20:
        raise ValueError("paired exact sign-flip requires 1..20 observations")
    obs = abs(float(np.mean(d)))
    ge = 0
    total = 1 << d.size
    for mask in range(total):
        signs = np.asarray([1.0 if ((mask >> i) & 1) else -1.0 for i in range(d.size)])
        if abs(float(np.mean(d * signs))) >= obs - 1e-15:
            ge += 1
    return ge / total


def analyze_r37c_r1_selection_evidence(raw_results_zip: str | Path) -> dict[str, Any]:
    raw = Path(raw_results_zip)
    rows: list[dict[str, Any]] = []
    with zipfile.ZipFile(raw) as zf:
        suite = json.loads(zf.read("R3_7C_R1_NEMO_SELECTION_SUITE_SUMMARY.json"))
        if suite.get("stage") != R37D_PARENT_STAGE:
            raise ValueError("wrong parent stage")
        if suite.get("status") != "NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED":
            raise ValueError("R3.7C-R1 suite incomplete")
        if int(suite.get("complete_chain_count", -1)) != int(suite.get("chain_count", -2)):
            raise ValueError("incomplete selection chains")
        if int(suite.get("selection_efficacy_pass_count", -1)) != int(suite.get("chain_count", -2)):
            raise ValueError("selection efficacy gate incomplete")

        for rec in suite["records"]:
            if rec.get("status") != "ENGINE_COMPLETED_SELECTION_CHAIN":
                raise ValueError("incomplete chain record")
            N = int(rec["population_size"])
            rep = int(rec["replicate"])
            axis = int(rec["axis"])
            sv = float(rec["selection_variance"])
            base = f"selection_variance_{sv:g}/N_{N}/rep_{rep:03d}/axis_{axis}/"
            effects = _read_effects(zf, base + "qtl/qtl_effects.tsv", axis)
            sel = rec["selected_branch"]
            ctl = rec["neutral_branch"]
            fs = _read_qfreq(zf, base + sel["fragmented"]["qfreq_relpath"], effects.size)
            fn = _read_qfreq(zf, base + ctl["fragmented"]["qfreq_relpath"], effects.size)
            fsr = _read_qfreq(zf, base + sel["reconnected"]["qfreq_relpath"], effects.size)
            fnr = _read_qfreq(zf, base + ctl["reconnected"]["qfreq_relpath"], effects.size)

            geom = geometric_adaptive_participation(effects, fs, fn)
            geom_rec = geometric_adaptive_participation(effects, fsr, fnr)
            eff = rec["selection_efficacy"]
            agg_ds = float(eff["adaptive_cross_group_S"])
            agg_dz = float(eff["adaptive_trait_divergence"])
            aggregate_k = agg_dz * agg_dz / (2.0 * agg_ds) if agg_ds > 0 else float("nan")
            if not math.isclose(geom["adaptive_trait_divergence"], agg_dz, rel_tol=0.0, abs_tol=2e-12):
                raise ValueError("geometric and parent adaptive trait divergence disagree")
            rows.append({
                "chain_id": rec["chain_id"],
                "population_size": N,
                "replicate": rep,
                "axis": axis,
                "selection_variance": sv,
                "aggregate_deltaS_K_eff_diagnostic": aggregate_k,
                **geom,
                "reconnected_geometric_adaptive_S": geom_rec["geometric_adaptive_S"],
                "reconnected_adaptive_trait_divergence": geom_rec["adaptive_trait_divergence"],
                "geometric_S_retention_after_reconnection": (
                    geom_rec["geometric_adaptive_S"] / geom["geometric_adaptive_S"]
                    if geom["geometric_adaptive_S"] > 0 else float("nan")
                ),
                "trait_divergence_retention_after_reconnection": (
                    geom_rec["adaptive_trait_divergence"] / geom["adaptive_trait_divergence"]
                    if abs(geom["adaptive_trait_divergence"]) > 0 else float("nan")
                ),
            })

    if len(rows) != 16:
        raise ValueError("R3.7D closure expects the full 16-chain oracle")

    lookup = {
        (r["population_size"], r["replicate"], r["axis"], r["selection_variance"]): r
        for r in rows
    }
    n_diffs = [
        lookup[(2000, rep, axis, sv)]["geometric_K_eff"] - lookup[(500, rep, axis, sv)]["geometric_K_eff"]
        for rep, axis, sv in itertools.product((0, 1), (0, 1), (1.0, 4.0))
    ]
    sv_diffs = [
        lookup[(N, rep, axis, 4.0)]["geometric_K_eff"] - lookup[(N, rep, axis, 1.0)]["geometric_K_eff"]
        for N, rep, axis in itertools.product((500, 2000), (0, 1), (0, 1))
    ]
    axis_diffs = [
        lookup[(N, rep, 1, sv)]["geometric_K_eff"] - lookup[(N, rep, 0, sv)]["geometric_K_eff"]
        for N, rep, sv in itertools.product((500, 2000), (0, 1), (1.0, 4.0))
    ]

    by_N = {str(N): _summary(r["geometric_K_eff"] for r in rows if r["population_size"] == N) for N in (500, 2000)}
    by_sv = {str(sv): _summary(r["geometric_K_eff"] for r in rows if r["selection_variance"] == sv) for sv in (1.0, 4.0)}
    by_axis = {str(axis): _summary(r["geometric_K_eff"] for r in rows if r["axis"] == axis) for axis in (0, 1)}
    high_n = [r["geometric_K_eff"] for r in rows if r["population_size"] == 2000]
    locus_count = 64
    if any((not np.isfinite(r["geometric_K_eff"])) or r["geometric_K_eff"] <= 0 or r["geometric_K_eff"] > locus_count + 1e-9 for r in rows):
        verdict = "REVIEW_GEOMETRIC_PARTICIPATION_INVALID"
    else:
        verdict = "PASS_DIRECTIONAL_SELECTION_EVIDENCE_CLOSURE__SCALAR_K_EFF_NOT_PRODUCTION_AUTHORIZED__HIGH_N_SHADOW_ENVELOPE_READY"

    return {
        "schema": "ARCANA_R37D_DIRECTIONAL_SELECTION_EVIDENCE_CLOSURE_V1",
        "stage": R37D_STAGE,
        "parent_stage": R37D_PARENT_STAGE,
        "verdict": verdict,
        "chain_count": len(rows),
        "geometric_K_eff_all": _summary(r["geometric_K_eff"] for r in rows),
        "aggregate_deltaS_K_eff_diagnostic": _summary(r["aggregate_deltaS_K_eff_diagnostic"] for r in rows),
        "by_population_size": by_N,
        "by_selection_variance": by_sv,
        "by_axis": by_axis,
        "paired_effects": {
            "N_2000_minus_500": {
                **_summary(n_diffs),
                "exact_two_sided_signflip_p": _paired_signflip_p(n_diffs),
            },
            "selection_variance_4_minus_1": {
                **_summary(sv_diffs),
                "exact_two_sided_signflip_p": _paired_signflip_p(sv_diffs),
            },
            "axis_1_minus_0": {
                **_summary(axis_diffs),
                "exact_two_sided_signflip_p": _paired_signflip_p(axis_diffs),
            },
        },
        "reconnection_geometric_S_retention": _summary(r["geometric_S_retention_after_reconnection"] for r in rows),
        "reconnection_trait_divergence_retention": _summary(r["trait_divergence_retention_after_reconnection"] for r in rows),
        "high_N_dynamic_selection_shadow_envelope": {
            "source_population_size": 2000,
            "minimum": float(np.min(high_n)),
            "center_median": float(np.median(high_n)),
            "maximum": float(np.max(high_n)),
            "semantics": "SHADOW_SENSITIVITY_ONLY__NOT_WORLD1_POPULATION_MAPPING__NOT_PRODUCTION_CONSTANT",
        },
        "static_parent_QTL_participation_reference": {
            "minimum": 46.6464,
            "median": 59.6152,
            "maximum": 63.5,
            "semantics": "R3.7A_STANDING_DIVERGENCE_REFERENCE__NOT_SELECTION_INCREMENT_CONSTANT",
        },
        "inference_correction": {
            "parent_aggregate_formula": "K=(Delta z)^2/(2*(S_selected-S_neutral))",
            "problem": "S is quadratic; subtracting S states retains neutral-adaptive cross terms and is not the squared norm of the matched adaptive displacement.",
            "r37d_formula": "Delta p_adapt = contrast(p_selected)-contrast(p_neutral); S_adapt=2*sum(a^2*Delta p_adapt^2); K=(Delta z)^2/(2*S_adapt)",
            "cauchy_bound_loci": locus_count,
        },
        "governance": {
            "scalar_K_eff_production_authorized": False,
            "direct_WorldSim_N_to_NEMO_N_mapping_authorized": False,
            "high_N_shadow_envelope_authorized": True,
            "canonical_write_allowed": False,
            "production_runtime_replacement_authorized": False,
            "mu_b_or_ceiling_change_authorized": False,
        },
        "rows": rows,
    }


@dataclass(frozen=True)
class AdaptiveSelectionShadowEnvelope:
    minimum: float
    center: float
    maximum: float

    def __post_init__(self) -> None:
        if not (0 < self.minimum <= self.center <= self.maximum):
            raise ValueError("invalid K_eff envelope")

    def values(self) -> tuple[float, float, float]:
        return (self.minimum, self.center, self.maximum)


def shadow_adaptive_selection_envelope(
    state: ReducedGeneticLifecycleState,
    trait_before: np.ndarray,
    trait_after_selection: np.ndarray,
    envelope: AdaptiveSelectionShadowEnvelope,
) -> tuple[dict[str, ReducedGeneticLifecycleState], dict[str, Any]]:
    """Apply selection displacement under a governed K envelope in shadow only.

    The ARCANA selection operator remains authoritative for the trait response.
    R3.7D only maps that already-produced response into adaptive latent geometry.
    No variant returned here is eligible for canonical state replacement.
    """
    outputs: dict[str, ReducedGeneticLifecycleState] = {}
    diagnostics: dict[str, Any] = {}
    for label, k in zip(("K_LOW", "K_CENTER", "K_HIGH"), envelope.values()):
        h, diag = advance_directional_selection_coordinate(
            state.adaptive_coordinate,
            trait_before,
            trait_after_selection,
            effective_polygenic_dimension=k,
        )
        outputs[label] = ReducedGeneticLifecycleState(
            va_within=state.va_within,
            ancestry_covariance=state.ancestry_covariance,
            neutral_segregation_potential=state.neutral_segregation_potential,
            adaptive_coordinate=h,
        )
        diagnostics[label] = {"K_eff": k, **diag}
    diagnostics["governance"] = {
        "semantic_status": "R3_7D_ADAPTIVE_SELECTION_SHADOW_ENVELOPE_ONLY",
        "canonical_write_allowed": False,
        "production_runtime_replacement_authorized": False,
        "scalar_K_eff_production_authorized": False,
    }
    return outputs, diagnostics
