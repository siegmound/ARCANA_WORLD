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
from .r37f_stress_window_shadow_replay import (
    _k_sensitivity_diagnostics,
    _legacy_clip_diagnostics,
)

STAGE = "v0.6D1-R3.7G"
PARENT_STAGE = "v0.6D1-R3.7F"


@dataclass(frozen=True)
class R37GProductionValidationConfig(r35.R35Config):
    """Governed 210->150 Ma production-binding validation replay.

    R3.7G does not yet replace the production runtime.  It runs the unchanged
    R3.5/R3.4 world state in parallel with the segregation-aware reduced
    genetic state over the historically audited 210->150 Ma interval.

    K_CENTER is a *nominal validation branch only*.  K_LOW and K_HIGH remain
    uncertainty sentinels.  None of the three values becomes a World-1
    canonical constant in this stage.
    """

    start_age_ma: float = 210.0
    end_age_ma: float = 150.0
    adaptive_k_low: float = 37.614
    adaptive_k_center: float = 38.470
    adaptive_k_high: float = 41.002
    shadow_recombination_fraction_per_generation: float = 0.5
    diagnostic_smoke: bool = False

    def __post_init__(self) -> None:
        if abs(self.start_age_ma - 210.0) > 1e-12:
            raise ValueError("R3.7G starts at 210 Ma")
        if self.diagnostic_smoke:
            if not (150.0 < self.end_age_ma < 210.0):
                raise ValueError("R3.7G diagnostic smoke must stay within 210->150 Ma")
        elif abs(self.end_age_ma - 150.0) > 1e-12:
            raise ValueError("R3.7G governed validation window is 210->150 Ma")
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


def run_production_binding_validation(
    common,
    a1,
    metadata_rows,
    cfg: R37GProductionValidationConfig = R37GProductionValidationConfig(),
) -> dict[str, Any]:
    # Canonical reference remains the untouched R3.5 run.
    canonical = r35.run(common, a1, metadata_rows, cfg)

    # Segregation-aware state remains observation-only in R3.7G.
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
        raise RuntimeError("R3.7G shadow bindings changed canonical R3.5/R3.4 state")

    shadow = _summarize_shadow(ctx, canonical)
    legacy_diag = _legacy_clip_diagnostics(canonical)
    k_diag = _k_sensitivity_diagnostics(ctx.records)

    expected_steps = int(
        round((cfg.start_age_ma - cfg.end_age_ma) * 1e6 / cfg.biology_cadence_years)
    )
    valid_steps = len(ctx.records) == expected_steps

    shadow_contacts = {k: int(v) for k, v in shadow["ceiling_contacts_by_variant"].items()}
    shadow_clear = all(v == 0 for v in shadow_contacts.values())
    contact_states = {k: bool(v > 0) for k, v in shadow_contacts.items()}
    no_qualitative_k_headroom_divergence = len(set(contact_states.values())) <= 1

    shadow_peaks = {
        k: float(v) for k, v in shadow["trajectory_max_q"]["peak_by_variant"].items()
    }
    legacy_peak = float(canonical["r35_headroom_summary"]["peak_after_homeostasis_q"])
    center_peak = shadow_peaks["K_CENTER"]
    center_headroom_to_existing_ceiling = float(cfg.variance_ceiling_normalized - center_peak)

    validation_pass = bool(
        (not cfg.diagnostic_smoke)
        and valid_steps
        and parity["all_core_parity"]
        and legacy_diag["legacy_clipping_reproduced"]
        and shadow_clear
        and center_headroom_to_existing_ceiling > 0.0
        and no_qualitative_k_headroom_divergence
    )

    if cfg.diagnostic_smoke:
        verdict = (
            "PASS_R37G_DIAGNOSTIC_SMOKE__CANONICAL_PARITY"
            if valid_steps and parity["all_core_parity"]
            else "REVIEW_R37G_DIAGNOSTIC_SMOKE"
        )
    elif validation_pass:
        verdict = (
            "PASS_210_TO_150_PRODUCTION_BINDING_VALIDATION__"
            "LEGACY_CLIPPING_REPRODUCED__SEGREGATION_AWARE_HEADROOM_CLEAR__"
            "K_ENVELOPE_SENTINELS_COHERENT__PRODUCTION_PROMOTION_REVIEW_REQUIRED"
        )
    else:
        verdict = "REVIEW_210_TO_150_PRODUCTION_BINDING_VALIDATION__PROMOTION_NOT_AUTHORIZED"

    return {
        "schema": "ARCANA_R37G_PRODUCTION_BINDING_VALIDATION_V1",
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
        "center_headroom_to_existing_ceiling": center_headroom_to_existing_ceiling,
        "shadow": shadow,
        "k_envelope_sensitivity": k_diag,
        "production_validation_gate": {
            "expected_biology_steps": expected_steps,
            "valid_biology_steps": bool(valid_steps),
            "canonical_parity": bool(parity["all_core_parity"]),
            "legacy_clipping_reproduced": bool(legacy_diag["legacy_clipping_reproduced"]),
            "shadow_all_variants_clear_of_ceiling": bool(shadow_clear),
            "shadow_ceiling_contacts_by_variant": shadow_contacts,
            "center_positive_headroom_to_existing_ceiling": bool(center_headroom_to_existing_ceiling > 0.0),
            "no_qualitative_k_headroom_divergence": bool(no_qualitative_k_headroom_divergence),
            "governed_validation_pass": validation_pass,
        },
        "branch_semantics": {
            "K_CENTER": "NOMINAL_VALIDATION_BRANCH_NOT_CANONICAL_CONSTANT",
            "K_LOW": "LOW_UNCERTAINTY_SENTINEL",
            "K_HIGH": "HIGH_UNCERTAINTY_SENTINEL",
        },
        "records": ctx.records,
        "authority": {
            "trait_response": "R3.5/R3.4_EXISTING_SELECTION_AUTHORITY_UNCHANGED",
            "migration": "R3.4_CURRENT_SPECIES_BOUND_GENE_FLOW_AND_45PCT_CAP_UNCHANGED",
            "nonflow_variance": "D3.3A_MU_B_DRIFT_AND_CEILING_UNCHANGED",
            "deme_lifecycle": "R3.3/R3.2C_PARENT_EVENTS_ONLY",
            "adaptive_participation": "R3.7D_HIGH_N_SHADOW_ENVELOPE",
            "stress_evidence": "R3.7F_210_TO_188_EXTERNAL_PASS",
        },
        "governance": {
            "shadow_only": True,
            "canonical_write_allowed": False,
            "production_runtime_replacement_authorized": False,
            "production_promotion_may_be_reviewed_only_after_governed_validation_pass": True,
            "scalar_K_eff_production_authorized": False,
            "nominal_K_center_is_not_a_world1_constant": True,
            "direct_WorldSim_N_to_NEMO_N_mapping_authorized": False,
            "mu_b_or_ceiling_change_authorized": False,
            "recombination_fraction_is_reference_shadow_architecture_not_world1_constant": True,
        },
    }
