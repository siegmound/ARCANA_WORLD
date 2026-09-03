from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
import numpy as np

import rebased_natural_control_runtime_v0_6D1_R3_4 as r34
import rebased_natural_control_runtime_v0_6D1_R3_5 as r35

from .r37d_selection_closure import AdaptiveSelectionShadowEnvelope
from .r37e_short_shadow_replay import (
    _initialize_context,
    _parity,
    _shadow_bindings,
    _summarize_shadow,
)

STAGE = "v0.6D1-R3.7F"
PARENT_STAGE = "v0.6D1-R3.7E"


@dataclass(frozen=True)
class R37FStressWindowConfig(r35.R35Config):
    """Governed stress-window shadow replay.

    The full governed window 210->188 Ma deliberately crosses the first legacy
    R3.5 q=0.08 clipping onset (~191.25 Ma) by roughly 3 Myr.  The three K values
    remain the R3.7D high-N *shadow* envelope and are not production constants.
    """

    start_age_ma: float = 210.0
    end_age_ma: float = 188.0
    adaptive_k_low: float = 37.614
    adaptive_k_center: float = 38.470
    adaptive_k_high: float = 41.002
    shadow_recombination_fraction_per_generation: float = 0.5
    diagnostic_smoke: bool = False

    def __post_init__(self) -> None:
        if abs(self.start_age_ma - 210.0) > 1e-12:
            raise ValueError("R3.7F starts at 210 Ma")
        if self.diagnostic_smoke:
            if not (188.0 < self.end_age_ma < 210.0):
                raise ValueError("R3.7F diagnostic smoke must stay within 210->188 Ma")
        elif abs(self.end_age_ma - 188.0) > 1e-12:
            raise ValueError("R3.7F governed stress window is 210->188 Ma")
        if not (0 < self.adaptive_k_low <= self.adaptive_k_center <= self.adaptive_k_high):
            raise ValueError("invalid R3.7D K envelope")
        if not (0 <= self.shadow_recombination_fraction_per_generation <= 0.5):
            raise ValueError("invalid shadow recombination fraction")

    @property
    def envelope(self) -> AdaptiveSelectionShadowEnvelope:
        return AdaptiveSelectionShadowEnvelope(
            self.adaptive_k_low,
            self.adaptive_k_center,
            self.adaptive_k_high,
        )


def _legacy_clip_diagnostics(canonical: dict[str, Any]) -> dict[str, Any]:
    rows = canonical.get("r35_telemetry", [])
    clipped = [r for r in rows if int(r.get("homeostasis_clipping_count", 0)) > 0]
    first = clipped[0] if clipped else None
    last = clipped[-1] if clipped else None
    return {
        "step_count": len(rows),
        "steps_with_clipping": len(clipped),
        "total_clipped_reservoir_step_contacts": int(
            sum(int(r.get("homeostasis_clipping_count", 0)) for r in rows)
        ),
        "first_clipping_age_ma": None if first is None else float(first.get("age_ma")),
        "last_clipping_age_ma": None if last is None else float(last.get("age_ma")),
        "first_clipping_step_index": None if first is None else int(first.get("step_index", -1)),
        "legacy_clipping_reproduced": bool(clipped),
    }


def _k_sensitivity_diagnostics(records: list[dict[str, Any]]) -> dict[str, Any]:
    labels = ("K_LOW", "K_CENTER", "K_HIGH")
    metrics = (
        "max_normalized_va",
        "median_normalized_va",
        "p99_normalized_va",
        "same_species_S_max",
        "same_species_S_median",
        "ancestry_abs_total",
        "adaptive_coordinate_abs_max",
    )
    out: dict[str, Any] = {}
    for metric in metrics:
        max_abs = 0.0
        age_at = None
        final = {k: 0.0 for k in labels}
        for r in records:
            vals = [float(r["variants"][k]["state"][metric]) for k in labels]
            spread = max(vals) - min(vals)
            if spread > max_abs:
                max_abs = spread
                age_at = float(r["age_ma"])
            final = {k: float(r["variants"][k]["state"][metric]) for k in labels}
        center = final["K_CENTER"]
        final_rel_span = None if center == 0 else float(
            (max(final.values()) - min(final.values())) / abs(center)
        )
        out[metric] = {
            "maximum_absolute_envelope_spread": float(max_abs),
            "age_ma_at_maximum_absolute_spread": age_at,
            "final_by_variant": final,
            "final_relative_span_vs_abs_center": final_rel_span,
        }
    return out


def run_stress_window_shadow(
    common,
    a1,
    metadata_rows,
    cfg: R37FStressWindowConfig = R37FStressWindowConfig(),
) -> dict[str, Any]:
    # Canonical reference: exact R3.5 scientific run + telemetry.
    canonical = r35.run(common, a1, metadata_rows, cfg)

    # Observation-only reduced genetic shadow on exact R3.4 parent dynamics.
    ctx, initdiag = _initialize_context(common, metadata_rows, cfg)
    parent_cfg = r34.R34Config(
        **{
            k: v
            for k, v in asdict(cfg).items()
            if k in r34.R34Config.__dataclass_fields__
        }
    )
    with _shadow_bindings(ctx):
        observed = r34.run(common, a1, metadata_rows, parent_cfg)

    parity = _parity(canonical, observed)
    if not parity["all_core_parity"]:
        raise RuntimeError("R3.7F shadow bindings changed canonical R3.5/R3.4 scientific state")

    shadow = _summarize_shadow(ctx, canonical)
    legacy_diag = _legacy_clip_diagnostics(canonical)
    k_diag = _k_sensitivity_diagnostics(ctx.records)

    expected_steps = int(
        round((cfg.start_age_ma - cfg.end_age_ma) * 1e6 / cfg.biology_cadence_years)
    )
    valid_steps = len(ctx.records) == expected_steps
    shadow_contacts = shadow["ceiling_contacts_by_variant"]
    shadow_clear = all(int(v) == 0 for v in shadow_contacts.values())
    shadow_contact_states = {k: bool(int(v) > 0) for k, v in shadow_contacts.items()}
    no_qualitative_k_headroom_divergence = len(set(shadow_contact_states.values())) <= 1

    legacy_peak = float(canonical["r35_headroom_summary"]["peak_after_homeostasis_q"])
    shadow_peaks = {
        k: float(v) for k, v in shadow["trajectory_max_q"]["peak_by_variant"].items()
    }
    center_peak = shadow_peaks["K_CENTER"]
    headroom_gain_vs_legacy_peak_q = float(legacy_peak - center_peak)

    governed_stress_pass = bool(
        (not cfg.diagnostic_smoke)
        and valid_steps
        and parity["all_core_parity"]
        and legacy_diag["legacy_clipping_reproduced"]
        and shadow_clear
        and no_qualitative_k_headroom_divergence
    )

    if cfg.diagnostic_smoke:
        verdict = (
            "PASS_R37F_DIAGNOSTIC_SHADOW_SMOKE__CANONICAL_PARITY"
            if valid_steps and parity["all_core_parity"]
            else "REVIEW_R37F_DIAGNOSTIC_SHADOW_SMOKE"
        )
    elif governed_stress_pass:
        verdict = (
            "PASS_STRESS_WINDOW_CROSSING__LEGACY_CLIPPING_REPRODUCED__"
            "SEGREGATION_AWARE_SHADOW_HEADROOM_CLEAR__K_ENVELOPE_ROBUST__"
            "PRODUCTION_BINDING_READINESS_REVIEW_REQUIRED"
        )
    else:
        verdict = "REVIEW_STRESS_WINDOW_CROSSING__PRODUCTION_BINDING_NOT_AUTHORIZED"

    return {
        "schema": "ARCANA_R37F_STRESS_WINDOW_ADAPTIVE_GENETIC_SHADOW_REPLAY_V1",
        "stage": STAGE,
        "parent_stage": PARENT_STAGE,
        "verdict": verdict,
        "config": asdict(cfg),
        "initialization": initdiag,
        "canonical_parity": parity,
        "canonical_r35_headroom": canonical["r35_headroom_summary"],
        "canonical_final": {
            "population": canonical["final_total_population"],
            "species_count": len(canonical["species_ids"]),
            "component_count": len(canonical["component_ids"]),
        },
        "legacy_stress_diagnostics": legacy_diag,
        "legacy_peak_q": legacy_peak,
        "shadow_peak_q": shadow_peaks,
        "headroom_gain_vs_legacy_peak_q": headroom_gain_vs_legacy_peak_q,
        "shadow": shadow,
        "k_envelope_sensitivity": k_diag,
        "stress_gate": {
            "expected_biology_steps": expected_steps,
            "valid_biology_steps": bool(valid_steps),
            "legacy_clipping_reproduced": bool(legacy_diag["legacy_clipping_reproduced"]),
            "shadow_all_variants_clear_of_ceiling": bool(shadow_clear),
            "shadow_ceiling_contact_state_by_variant": shadow_contact_states,
            "no_qualitative_k_headroom_divergence": bool(no_qualitative_k_headroom_divergence),
            "governed_stress_pass": governed_stress_pass,
        },
        "records": ctx.records,
        "authority": {
            "trait_response": "R3.5/R3.4_EXISTING_SELECTION_AUTHORITY_UNCHANGED",
            "migration": "R3.4_CURRENT_SPECIES_BOUND_GENE_FLOW_AND_45PCT_CAP_UNCHANGED",
            "nonflow_variance": "D3.3A_MU_B_DRIFT_AND_CEILING_UNCHANGED",
            "deme_lifecycle": "R3.3/R3.2C_PARENT_EVENTS_ONLY",
            "adaptive_participation": "R3.7D_HIGH_N_SHADOW_ENVELOPE",
            "legacy_stress_target": "R3.5_Q0P08_FIRST_CLIPPING_ONSET_APPROX_191P25MA",
        },
        "governance": {
            "shadow_only": True,
            "canonical_write_allowed": False,
            "production_runtime_replacement_authorized": False,
            "production_binding_readiness_may_be_reviewed_only_after_governed_stress_pass": True,
            "scalar_K_eff_production_authorized": False,
            "direct_WorldSim_N_to_NEMO_N_mapping_authorized": False,
            "mu_b_or_ceiling_change_authorized": False,
            "recombination_fraction_is_reference_shadow_architecture_not_world1_constant": True,
        },
    }
