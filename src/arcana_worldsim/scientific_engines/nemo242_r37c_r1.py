from __future__ import annotations

from pathlib import Path
from typing import Sequence
import json

import numpy as np

from .nemo242_r36d import _nemo_matrix, _nemo_vector, NEMO_REQUIRED_VERSION, NEMO_REQUIRED_EXECUTABLE
from .nemo242_r37c import (
    R37CSelectionProtocol,
    r37c_exchange_matrix,
    r37c_nemo_transition,
    r37c_local_optima,
)
from .serialization import file_sha256

R37C_R1_STAGE = "v0.6D1-R3.7C-R1"
R37C_R1_SELECTED_LCE = "breed_selection_disperse"
R37C_R1_SELECTION_FITNESS_MODEL = "absolute"
R37C_R1_NUMERICAL_EFFICACY_TOL = 1e-12


def _trait_mean_from_qtl(effect_a: np.ndarray, freq: np.ndarray) -> np.ndarray:
    return np.sum(effect_a[None, :] * (2.0 * freq - 1.0), axis=1)


def _segregation_potential_from_qtl(effect_a: np.ndarray, freq: np.ndarray) -> np.ndarray:
    a2 = np.asarray(effect_a, float) ** 2
    p = np.asarray(freq, float)
    d = p[:, None, :] - p[None, :, :]
    return 2.0 * np.sum(a2[None, None, :] * d * d, axis=2)


def _signed_group_divergence(z: np.ndarray) -> float:
    return float(np.mean(z[[2, 3]]) - np.mean(z[[0, 1]]))


def _cross_group_mean(s: np.ndarray) -> float:
    return float(np.mean([s[i, j] for i in (0, 1) for j in (2, 3)]))


def selection_efficacy_metrics(
    effect_a: Sequence[float],
    selected_freq: np.ndarray,
    neutral_freq: np.ndarray,
    *,
    numerical_tol: float = R37C_R1_NUMERICAL_EFFICACY_TOL,
) -> dict:
    """Fail-closed liveness check for the NEMO selection oracle.

    This is NOT an effect-size calibration threshold. ``numerical_tol`` only
    distinguishes exact/numerically-null selected-vs-neutral behavior from a
    live response. Scientific acceptance of K_eff remains a later review gate.
    """
    effects = np.asarray(effect_a, float)
    sel = np.asarray(selected_freq, float)
    ctl = np.asarray(neutral_freq, float)
    if effects.ndim != 1 or sel.shape != ctl.shape or sel.shape != (4, effects.size):
        raise ValueError("R3.7C-R1 efficacy gate requires matching 4-patch QTL frequency states")
    if numerical_tol < 0 or not np.isfinite(numerical_tol):
        raise ValueError("numerical_tol must be finite and non-negative")

    zs = _trait_mean_from_qtl(effects, sel)
    zn = _trait_mean_from_qtl(effects, ctl)
    ss = _segregation_potential_from_qtl(effects, sel)
    sn = _segregation_potential_from_qtl(effects, ctl)
    adaptive_dz = _signed_group_divergence(zs) - _signed_group_divergence(zn)
    adaptive_ds = _cross_group_mean(ss) - _cross_group_mean(sn)
    max_freq_delta = float(np.max(np.abs(sel - ctl)))
    exact_identical = bool(np.array_equal(sel, ctl))
    direction_aligned = bool(adaptive_dz > numerical_tol)
    positive_adaptive_s = bool(adaptive_ds > 0.0)
    pass_gate = bool((not exact_identical) and max_freq_delta > numerical_tol and direction_aligned and positive_adaptive_s)
    return {
        "selected_neutral_frequency_state_exactly_identical": exact_identical,
        "max_abs_allele_frequency_delta": max_freq_delta,
        "selected_group_trait_divergence": _signed_group_divergence(zs),
        "neutral_group_trait_divergence": _signed_group_divergence(zn),
        "adaptive_trait_divergence": adaptive_dz,
        "adaptive_cross_group_S": adaptive_ds,
        "direction_aligned_with_optima": direction_aligned,
        "positive_adaptive_S": positive_adaptive_s,
        "numerical_liveness_tolerance": float(numerical_tol),
        "selection_efficacy_gate_pass": pass_gate,
        "gate_semantics": "NUMERICAL_LIVENESS_ONLY__NOT_EFFECT_SIZE_CALIBRATION",
    }


def render_r37c_r1_phase_ini(
    *,
    phase: str,
    transitions: int,
    effect_a: Sequence[float],
    allele_frequencies: np.ndarray,
    population_size: int,
    seed: int,
    output_dir: str | Path,
    chain_id: str,
    selection_enabled: bool,
    selection_variance: float | None = None,
    optimum_amplitude: float = 0.6,
    exchange_matrix: np.ndarray,
) -> dict:
    effects = np.asarray(effect_a, float)
    freq = np.asarray(allele_frequencies, float)
    exchange = np.asarray(exchange_matrix, float)
    if effects.ndim != 1 or freq.shape != (4, effects.size):
        raise ValueError("R3.7C-R1 requires 4 patches and locus-matched frequency state")
    if np.any(~np.isfinite(freq)) or np.any(freq < -1e-15) or np.any(freq > 1 + 1e-15):
        raise ValueError("allele frequencies must lie in [0,1]")
    freq = np.clip(freq, 0.0, 1.0)
    if int(population_size) < 20 or int(transitions) < 1:
        raise ValueError("invalid N/transitions")
    if selection_enabled and (selection_variance is None or not np.isfinite(selection_variance) or selection_variance <= 0):
        raise ValueError("selected phase requires a positive selection variance")
    if (not selection_enabled) and selection_variance is not None:
        raise ValueError("neutral phase must not carry a selection variance")

    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)
    trans = r37c_nemo_transition(exchange)
    generations = int(transitions) + 1
    filename = f"arcana_r37c_r1_{chain_id}_{phase.lower()}"
    ini = root / "Nemo2_ARCANA_R37C_R1.ini"
    half = 0.5 * effects

    lifecycle = ["quanti_init                 1"]
    if selection_enabled:
        # NEMO 2.4.2 composite LCE: offspring are created, selected and then
        # transitioned in the WF population inside one event. This avoids the
        # invalid standalone viability_selection ordering of parent R3.7C.
        lifecycle.append("breed_selection_disperse    2")
        lifecycle.append("save_stats                  3")
        lifecycle.append("save_files                  4")
    else:
        lifecycle.append("breed_disperse              2")
        lifecycle.append("save_stats                  3")
        lifecycle.append("save_files                  4")

    selection_block = ""
    if selection_enabled:
        selection_block = f"""
selection_trait         quant
selection_model         gaussian
selection_fitness_model absolute
selection_trait_dimension 1
selection_variance      {float(selection_variance):.17g}
selection_local_optima  {_nemo_matrix(r37c_local_optima(optimum_amplitude))}
"""

    text = f"""## ARCANA WorldSim {R37C_R1_STAGE} -- NEMO 2.4.2 composite directional-selection oracle repair
logfile                 arcana_nemo242_r37c_r1.log
run_mode                overwrite
random_seed             {int(seed)}
root_dir                .
filename                {filename}
replicates              1
generations             {generations}

patch_number            4
patch_nbfem             {_nemo_vector([int(population_size)] * 4)}
patch_nbmal             0

{chr(10).join(lifecycle)}
mating_system           6
mating_isWrightFisher
breed_disperse_matrix   {_nemo_matrix(trans)}

quanti_traits           1
quanti_loci             {effects.size}
quanti_allele_model     diallelic
quanti_diallele_datatype byte
quanti_allele_value     {_nemo_vector(half.tolist())}
quanti_init_freq        {_nemo_matrix(freq)}
quanti_mutation_rate    0
quanti_recombination_rate 0.5
{selection_block}
stat                    adlt.demography adlt.quanti
stat_log_time           {generations}
quanti_freq_output      1
quanti_freq_logtime     {generations}
quanti_dir              .
"""
    ini.write_text(text, encoding="utf-8")
    np.savetxt(root / "initial_allele_frequencies.tsv", freq, delimiter="\t", fmt="%.17g")
    np.savetxt(root / "nemo_transition.tsv", trans, delimiter="\t", fmt="%.17g")
    if selection_enabled:
        np.savetxt(root / "selection_local_optima.tsv", r37c_local_optima(optimum_amplitude), delimiter="\t", fmt="%.17g")

    manifest = {
        "schema": "ARCANA_R37C_R1_NEMO_SELECTION_PHASE_BINDING_V1",
        "stage": R37C_R1_STAGE,
        "parent_stage": "v0.6D1-R3.7C",
        "chain_id": str(chain_id),
        "phase": str(phase),
        "transitions": int(transitions),
        "nemo_generations_parameter": generations,
        "population_size": int(population_size),
        "seed": int(seed),
        "nemo_required_version": NEMO_REQUIRED_VERSION,
        "nemo_required_executable": NEMO_REQUIRED_EXECUTABLE,
        "selection_enabled": bool(selection_enabled),
        "selected_lifecycle_event": R37C_R1_SELECTED_LCE if selection_enabled else None,
        "selection_model": "gaussian" if selection_enabled else None,
        "selection_fitness_model": R37C_R1_SELECTION_FITNESS_MODEL if selection_enabled else None,
        "selection_variance": float(selection_variance) if selection_enabled else None,
        "selection_local_optimum_amplitude": float(optimum_amplitude) if selection_enabled else None,
        "mutation_rate": 0.0,
        "recombination_rate": 0.5,
        "phase_boundary_semantics": "QFREQ_ALLELE_FREQUENCIES_REINITIALIZED__HARDY_WEINBERG_AND_LD_RESET_AT_BOUNDARY",
        "observable_authority": "TRAIT_MEAN_AND_SEGREGATION_POTENTIAL_FROM_ALLELE_FREQUENCIES",
        "repair_semantics": "COMPOSITE_BREED_SELECTION_DISPERSE_FOR_SELECTED_BRANCH__ABSOLUTE_GAUSSIAN_FITNESS",
        "canonical_write_allowed": False,
        "automatic_calibration_allowed": False,
        "production_selection_mapping_authorized": False,
        "ini_file": ini.name,
        "ini_sha256": file_sha256(ini),
    }
    (root / "R3_7C_R1_PHASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
