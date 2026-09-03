from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import json

import numpy as np

from .nemo242_r36d import _nemo_matrix, _nemo_vector, NEMO_REQUIRED_VERSION, NEMO_REQUIRED_EXECUTABLE
from .serialization import file_sha256


@dataclass(frozen=True)
class R37CSelectionProtocol:
    burnin_transitions: int = 200
    selected_transitions: int = 300
    reconnect_transitions: int = 400
    optimum_amplitude: float = 0.6
    selection_variances: tuple[float, ...] = (1.0, 4.0)
    exchange_rate: float = 0.03
    recombination_rate: float = 0.5
    mutation_rate: float = 0.0

    def __post_init__(self) -> None:
        if min(self.burnin_transitions, self.selected_transitions, self.reconnect_transitions) < 1:
            raise ValueError("all R3.7C phases require >=1 transition")
        if self.optimum_amplitude <= 0 or self.exchange_rate < 0 or self.exchange_rate >= 0.5:
            raise ValueError("invalid R3.7C optimum/exchange")
        if not self.selection_variances or any((not np.isfinite(x) or x <= 0) for x in self.selection_variances):
            raise ValueError("selection variances must be finite positive values")
        if self.recombination_rate < 0 or self.recombination_rate > 0.5 or self.mutation_rate < 0:
            raise ValueError("invalid recombination/mutation")


def _sym_exchange_connected(rate: float = 0.03) -> np.ndarray:
    x = np.zeros((4, 4), float)
    for i, j in ((0, 1), (1, 2), (2, 3)):
        x[i, j] = x[j, i] = float(rate)
    return x


def _sym_exchange_fragmented(rate: float = 0.03) -> np.ndarray:
    x = np.zeros((4, 4), float)
    for i, j in ((0, 1), (2, 3)):
        x[i, j] = x[j, i] = float(rate)
    return x


def r37c_exchange_matrix(phase: str, protocol: R37CSelectionProtocol | None = None) -> np.ndarray:
    p = protocol or R37CSelectionProtocol()
    key = str(phase).upper()
    if key == "COMMON_BURNIN" or key == "RECONNECTED_RELAXED":
        return _sym_exchange_connected(p.exchange_rate)
    if key in ("FRAGMENTED_DIVERGENT_SELECTION", "FRAGMENTED_MATCHED_NEUTRAL"):
        return _sym_exchange_fragmented(p.exchange_rate)
    raise ValueError(f"unknown R3.7C phase {phase!r}")


def r37c_nemo_transition(exchange: np.ndarray) -> np.ndarray:
    g = np.asarray(exchange, float)
    if g.shape != (4, 4) or np.max(np.abs(np.diag(g))) > 1e-15 or np.any(g < -1e-15):
        raise ValueError("R3.7C exchange must be 4x4, non-negative, zero-diagonal")
    p = g.copy()
    np.fill_diagonal(p, 1.0 - g.sum(axis=1))
    if np.min(p) < -1e-12 or not np.allclose(p.sum(axis=1), 1, atol=1e-12, rtol=0):
        raise ValueError("invalid transition")
    if not np.allclose(p, p.T, atol=1e-12, rtol=0) or not np.allclose(p.sum(axis=0), 1, atol=1e-12, rtol=0):
        raise ValueError("R3.7C reference requires symmetric/doubly-stochastic transition")
    return p


def r37c_local_optima(optimum_amplitude: float) -> np.ndarray:
    a = float(optimum_amplitude)
    if not np.isfinite(a) or a <= 0:
        raise ValueError("optimum amplitude must be positive")
    return np.asarray([[-a], [-a], [a], [a]], float)


def render_r37c_phase_ini(
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
        raise ValueError("R3.7C requires 4 patches and locus-matched frequency state")
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
    filename = f"arcana_r37c_{chain_id}_{phase.lower()}"
    ini = root / "Nemo2_ARCANA_R37C.ini"
    half = 0.5 * effects

    lifecycle = ["quanti_init             1"]
    if selection_enabled:
        lifecycle.append("viability_selection     2")
        lifecycle.append("breed_disperse          3")
        lifecycle.append("save_stats              4")
        lifecycle.append("save_files              5")
    else:
        lifecycle.append("breed_disperse          2")
        lifecycle.append("save_stats              3")
        lifecycle.append("save_files              4")

    selection_block = ""
    if selection_enabled:
        selection_block = f"""
selection_trait         quant
selection_model         gaussian
selection_fitness_model relative_local
selection_trait_dimension 1
selection_variance      {float(selection_variance):.17g}
selection_local_optima  {_nemo_matrix(r37c_local_optima(optimum_amplitude))}
"""

    text = f"""## ARCANA WorldSim v0.6D1-R3.7C -- NEMO 2.4.2 directional-selection oracle
logfile                 arcana_nemo242_r37c.log
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
        "schema": "ARCANA_R37C_NEMO_SELECTION_PHASE_BINDING_V1",
        "stage": "v0.6D1-R3.7C",
        "chain_id": str(chain_id),
        "phase": str(phase),
        "transitions": int(transitions),
        "nemo_generations_parameter": generations,
        "population_size": int(population_size),
        "seed": int(seed),
        "nemo_required_version": NEMO_REQUIRED_VERSION,
        "nemo_required_executable": NEMO_REQUIRED_EXECUTABLE,
        "selection_enabled": bool(selection_enabled),
        "selection_model": "gaussian" if selection_enabled else None,
        "selection_fitness_model": "relative_local" if selection_enabled else None,
        "selection_variance": float(selection_variance) if selection_enabled else None,
        "selection_local_optimum_amplitude": float(optimum_amplitude) if selection_enabled else None,
        "mutation_rate": 0.0,
        "recombination_rate": 0.5,
        "phase_boundary_semantics": "QFREQ_ALLELE_FREQUENCIES_REINITIALIZED__HARDY_WEINBERG_AND_LD_RESET_AT_BOUNDARY",
        "observable_authority": "TRAIT_MEAN_AND_SEGREGATION_POTENTIAL_FROM_ALLELE_FREQUENCIES",
        "canonical_write_allowed": False,
        "automatic_calibration_allowed": False,
        "production_selection_mapping_authorized": False,
        "ini_file": ini.name,
        "ini_sha256": file_sha256(ini),
    }
    (root / "R3_7C_PHASE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest
