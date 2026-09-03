from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Iterable, Sequence
import json
import re
import shutil
import subprocess

import numpy as np

from .cadence_validation import (
    CadenceNormalizationSpec,
    embeddable_reference_exchange_from_edge_targets,
    interval_exchange_to_nemo_generation,
)
from .contracts import ScientificEvidenceBundle
from .nemo_benchmarks import ExchangePhase, NemoBenchmarkScenario, canonical_r36b_scenarios
from .nemo_qtl_ensemble import NemoQTLRealization
from .registry import NEMO_242
from .serialization import file_sha256


NEMO_REQUIRED_EXECUTABLE = "nemo2.4.2"
NEMO_REQUIRED_VERSION = "2.4.2"


@dataclass(frozen=True)
class Nemo242ExecutableReferenceSpec:
    """R3.6D executable reference protocol.

    The primary protocol deliberately disables mutation and selection. That
    isolates the admixture/recombination/drift contribution, which is the
    quantity needed to test ARCANA's gene-flow second-moment injection without
    inventing a mapping from ARCANA's phenomenological mu/b terms to NEMO QTL
    mutation/selection parameters.
    """

    executable: str = NEMO_REQUIRED_EXECUTABLE
    arcana_interval_years: float = 125_000.0
    macro_intervals: int = 1
    mutation_rate_per_locus: float = 0.0
    recombination_rate: float = 0.5
    quanti_freq_logtime: int | None = None
    run_mode: str = "overwrite"

    def __post_init__(self) -> None:
        if Path(self.executable).name != NEMO_REQUIRED_EXECUTABLE:
            raise ValueError(f"R3.6D requires executable basename {NEMO_REQUIRED_EXECUTABLE!r}")
        if self.arcana_interval_years <= 0 or self.macro_intervals < 1:
            raise ValueError("interval must be positive and macro_intervals >=1")
        if self.mutation_rate_per_locus != 0.0:
            raise ValueError("R3.6D primary admixture-injection reference locks NEMO mutation rate to 0")
        if abs(self.recombination_rate - 0.5) > 1e-15:
            raise ValueError("R3.6D primary reference locks free recombination at 0.5")
        if self.run_mode != "overwrite":
            raise ValueError("R3.6D reproducible sidecar uses run_mode overwrite")


@dataclass(frozen=True)
class Nemo242Preflight:
    available: bool
    executable: str
    resolved_path: str | None
    exact_version_name: bool
    reason: str

    @property
    def pass_exact_242(self) -> bool:
        return self.available and self.exact_version_name


def preflight_nemo242(executable: str = NEMO_REQUIRED_EXECUTABLE) -> Nemo242Preflight:
    resolved = shutil.which(executable)
    exact = Path(executable).name == NEMO_REQUIRED_EXECUTABLE
    if not exact:
        return Nemo242Preflight(False, executable, resolved, False, "WRONG_EXECUTABLE_BASENAME")
    if resolved is None:
        return Nemo242Preflight(False, executable, None, True, "EXECUTABLE_NOT_FOUND")
    return Nemo242Preflight(True, executable, str(Path(resolved).resolve()), True, "PASS_EXECUTABLE_BINDING")


def _nemo_matrix(a: np.ndarray, *, precision: int = 17) -> str:
    x = np.asarray(a, dtype=float)
    if x.ndim != 2:
        raise ValueError("NEMO matrix renderer requires 2-D array")
    rows = []
    for row in x:
        rows.append("{" + ", ".join(format(float(v), f".{precision}g") for v in row) + "}")
    return "{" + "\n                         ".join(rows) + "}"


def _nemo_vector(v: Sequence[float | int], *, precision: int = 17) -> str:
    vals = []
    for x in v:
        if isinstance(x, (int, np.integer)):
            vals.append(str(int(x)))
        else:
            vals.append(format(float(x), f".{precision}g"))
    return "{{" + ", ".join(vals) + "}}"


def canonical_r36d_scenarios(*, n_individuals: int = 2000, q_star: float = 0.045) -> tuple[NemoBenchmarkScenario, ...]:
    """B0/B1 plus a CTMC-embeddable high-admixture C3 reference.

    Historical R3.6B B3 remains untouched and is never silently projected.
    """
    suite = canonical_r36b_scenarios(q_star=q_star, n_individuals=n_individuals)
    b0, b1, b3 = suite[0], suite[1], suite[3]
    g2 = embeddable_reference_exchange_from_edge_targets(b3.phases[0].exchange_matrix, 125_000.0)
    c3 = NemoBenchmarkScenario(
        name="C3_EMBEDDABLE_HIGH_ADMIXTURE_STRESS",
        normalized_trait_means=np.array(b3.normalized_trait_means, copy=True),
        normalized_additive_variance=np.array(b3.normalized_additive_variance, copy=True),
        population_individuals=np.full_like(b3.population_individuals, int(n_individuals)),
        phases=(ExchangePhase("EMBEDDABLE_HIGH_EXCHANGE", 0, 1, g2),),
        generation_time_years=b3.generation_time_years,
        notes=b3.notes + ("R3.6D CTMC-embeddable cross-engine reference; not canonical replay exchange",),
    )
    return b0, b1, c3


def _validate_realization_for_scenario(realization: NemoQTLRealization, scenario: NemoBenchmarkScenario) -> None:
    if realization.allele_frequencies.shape[:2] != scenario.normalized_trait_means.shape:
        raise ValueError("QTL realization patch/trait shape does not match scenario")
    if realization.effect_sizes.shape[0] != scenario.normalized_trait_means.shape[1]:
        raise ValueError("QTL realization trait count mismatch")
    if not np.allclose(realization.target_means, scenario.normalized_trait_means, atol=2e-7, rtol=0):
        raise ValueError("QTL realization target means mismatch scenario")
    if not np.allclose(realization.target_variances, scenario.normalized_additive_variance, atol=2e-7, rtol=0):
        raise ValueError("QTL realization target variances mismatch scenario")


def render_nemo242_axis_ini(
    scenario: NemoBenchmarkScenario,
    realization: NemoQTLRealization,
    *,
    trait_local_index: int,
    seed: int,
    output_dir: str | Path,
    spec: Nemo242ExecutableReferenceSpec = Nemo242ExecutableReferenceSpec(),
) -> dict:
    """Render an upstream-source-bound NEMO 2.4.2 one-trait reference config.

    One ARCANA trait is executed per NEMO job. This avoids inventing a
    pleiotropic mapping between independent ARCANA thermal/aridity QTL sets.
    """
    _validate_realization_for_scenario(realization, scenario)
    ti = int(trait_local_index)
    if ti < 0 or ti >= realization.effect_sizes.shape[0]:
        raise ValueError("trait_local_index out of range")
    if len(scenario.phases) != 1:
        raise ValueError("R3.6D executable reference currently requires single-phase scenario")
    root = Path(output_dir)
    root.mkdir(parents=True, exist_ok=True)

    gtime = float(scenario.generation_time_years)
    transitions_per_interval = spec.arcana_interval_years / gtime
    rounded = int(round(transitions_per_interval))
    if abs(transitions_per_interval - rounded) > 1e-10:
        raise ValueError("ARCANA interval must map to an integer number of NEMO generations")
    transitions = rounded * int(spec.macro_intervals)
    # NEMO generation 1 is the initialized generation; request one additional
    # generation so the requested number of breed/disperse transitions is not
    # silently shortened by the initialization origin convention.
    nemo_generations = transitions + 1

    pergen = interval_exchange_to_nemo_generation(
        scenario.phases[0].exchange_matrix,
        spec.arcana_interval_years,
        gtime,
    )
    if not np.allclose(pergen.sum(axis=1), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("per-generation NEMO matrix is not row-stochastic")
    # R3.6D deliberately uses NEMO's composite breed_disperse Wright-Fisher
    # operator. Upstream implements this as backward/gametic migration and
    # therefore validates columns, not rows. The authorized B0/B1/C3 reference
    # scenarios are symmetric, so the same transition matrix is doubly
    # stochastic and can be used without transposition or reinterpretation of
    # coefficients. Non-symmetric matrices are refused rather than silently
    # projected into a different biological operator.
    if not np.allclose(pergen, pergen.T, atol=1e-12, rtol=0.0):
        raise ValueError("R3.6D executable reference requires a symmetric migration matrix")
    if not np.allclose(pergen.sum(axis=0), 1.0, atol=1e-12, rtol=0.0):
        raise ValueError("R3.6D breed_disperse matrix must be column-stochastic")

    # ARCANA's realization uses genotype contribution a*(g-1), values
    # {-a,0,+a}. NEMO's additive genotype sums two allelic values; therefore
    # alleles {-a/2,+a/2} exactly reproduce the same genotype contributions.
    arcana_effect = np.asarray(realization.effect_sizes[ti], dtype=float)
    nemo_half_effect = 0.5 * arcana_effect
    p = np.asarray(realization.allele_frequencies[:, ti, :], dtype=float)
    n = np.asarray(scenario.population_individuals, dtype=int)
    if np.any(p <= 0) or np.any(p >= 1):
        raise ValueError("R3.6D requires strictly interior allele frequencies")

    # Initial frequencies in NEMO's symmetrical diallelic model refer to the
    # trait-increasing (+a) allele; this matches R3.6B's p convention.
    #
    # NEMO 2.4.2 TTQFreqExtractor persists the .qfreq file only when its
    # periodic callback is invoked at the final generation.  Therefore the
    # default R3.6D schedule requests one final-only observation.  A custom
    # logtime is accepted only when it divides the final generation exactly;
    # otherwise a successful engine run could silently produce no .qfreq.
    freq_logtime = int(spec.quanti_freq_logtime or nemo_generations)
    if freq_logtime < 1:
        raise ValueError("R3.6D quanti_freq_logtime must be >= 1")
    if nemo_generations % freq_logtime != 0:
        raise ValueError(
            "R3.6D quanti_freq_logtime must divide the NEMO generations parameter "
            "so TTQFreqExtractor is invoked at the final generation"
        )
    filename = f"arcana_r36d_{scenario.name.lower()}_t{ti}_s{int(seed)}"
    ini = root / "Nemo2_ARCANA_R36D.ini"
    text = f"""## ARCANA WorldSim v0.6D1-R3.6D -- governed NEMO 2.4.2 reference
## Upstream-bound parameter names; one ARCANA trait per NEMO job.
logfile                 arcana_nemo242.log
run_mode                {spec.run_mode}
random_seed             {int(seed)}
root_dir                .
filename                {filename}
replicates              1
generations             {nemo_generations}

## POPULATION -- one-sex/hermaphrodite Wright-Fisher reference
patch_number            {len(n)}
patch_nbfem             {_nemo_vector(n.tolist())}
patch_nbmal             0

## LIFE CYCLE EVENTS
quanti_init             1
breed_disperse          2
save_stats              3
save_files              4

## MATING / WRIGHT-FISHER
mating_system           6
mating_isWrightFisher

## BACKWARD/GAMETIC PARENT-SOURCE MIGRATION
## Numeric matrix is the symmetric, cadence-normalized R3.6C per-generation
## transition; symmetry makes it both row- and column-stochastic.
breed_disperse_matrix   {_nemo_matrix(pergen)}

## ONE DIALLELIC ADDITIVE QUANTITATIVE TRAIT
quanti_traits           1
quanti_loci             {arcana_effect.size}
quanti_allele_model     diallelic
quanti_diallele_datatype byte
quanti_allele_value     {_nemo_vector(nemo_half_effect.tolist())}
quanti_init_freq        {_nemo_matrix(p)}
quanti_mutation_rate    {format(spec.mutation_rate_per_locus, '.17g')}
quanti_recombination_rate {format(spec.recombination_rate, '.17g')}

## OUTPUT / EVIDENCE
stat                    adlt.demography adlt.quanti
stat_log_time           {freq_logtime}
quanti_freq_output      1
quanti_freq_logtime     {freq_logtime}
quanti_dir              .
"""
    ini.write_text(text, encoding="utf-8")

    np.savetxt(root / "nemo_per_generation_dispersal.tsv", pergen, delimiter="\t", fmt="%.17g")
    np.savetxt(root / "nemo_initial_allele_frequencies.tsv", p, delimiter="\t", fmt="%.17g")
    np.savetxt(root / "nemo_allele_half_effects.tsv", nemo_half_effect[None, :], delimiter="\t", fmt="%.17g")
    manifest = {
        "schema": "ARCANA_R36D_NEMO_2_4_2_EXECUTABLE_BINDING_V1",
        "scenario": scenario.name,
        "trait_local_index": ti,
        "arcana_trait_axis": int(realization.trait_axes[ti]),
        "seed": int(seed),
        "nemo_required_version": NEMO_REQUIRED_VERSION,
        "nemo_required_executable": NEMO_REQUIRED_EXECUTABLE,
        "generation_time_years": gtime,
        "arcana_interval_years": spec.arcana_interval_years,
        "macro_intervals": spec.macro_intervals,
        "nemo_transitions": transitions,
        "nemo_generations_parameter": nemo_generations,
        "quanti_freq_logtime": freq_logtime,
        "qfreq_persistence_semantics": "FINAL_GENERATION_CALLBACK_REQUIRED_BY_NEMO_2_4_2_TTQFREQEXTRACTOR",
        "qtl_loci": int(arcana_effect.size),
        "protocol": "ADMIXTURE_RECOMBINATION_DRIFT_ONLY",
        "mutation_rate_per_locus": 0.0,
        "selection_enabled": False,
        "recombination_rate": 0.5,
        "effect_mapping": "NEMO_ALLELES_MINUS_PLUS_A_OVER_2_REPRODUCE_ARCANA_A_TIMES_G_MINUS_1",
        "initial_frequency_semantics": "TRAIT_INCREASING_ALLELE_FREQUENCY",
        "dispersal_semantics": "NEMO_BREED_DISPERSE_BACKWARD_GAMETIC__R3_6C_SYMMETRIC_CADENCE_NORMALIZED_PER_GENERATION",
        "matrix_symmetry_required": True,
        "matrix_row_stochastic": True,
        "matrix_column_stochastic": True,
        "population_semantics": "PATCH_NBFEM_N_INDIVIDUAL_HERMAPHRODITE__PATCH_NBMAL_ZERO",
        "life_cycle": "QUANTI_INIT__BREED_DISPERSE_WRIGHT_FISHER__SAVE_STATS__SAVE_FILES",
        "ini_file": ini.name,
        "ini_sha256": file_sha256(ini),
        "canonical_write_allowed": False,
        "automatic_calibration_allowed": False,
        "unsupported_mapping": "ARCANA mu/b homeostasis is intentionally not mapped to NEMO mutation/selection in R3.6D",
    }
    mpath = root / "R3_6D_NEMO_BINDING_MANIFEST.json"
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return manifest


def parse_qfreq(path: str | Path, *, arcana_effect_a: Sequence[float]) -> dict:
    """Parse NEMO 2.4.x .qfreq output and reconstruct one-trait moments.

    Upstream qfreq rows are: pop trait locus allele g<generation> ... and for
    the symmetric diallelic model the stored frequency is the trait-increasing
    allele frequency.
    """
    pth = Path(path)
    lines = [ln.strip() for ln in pth.read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise ValueError("empty qfreq file")
    header = lines[0].split()
    if header[:4] != ["pop", "trait", "locus", "allele"] or not all(x.startswith("g") for x in header[4:]):
        raise ValueError("unrecognized NEMO qfreq header")
    generations = [int(x[1:]) for x in header[4:]]
    effects = np.asarray(arcana_effect_a, dtype=float)
    rows = []
    for ln in lines[1:]:
        tok = ln.split()
        if len(tok) != len(header):
            raise ValueError("qfreq row width mismatch")
        pop, trait, locus = map(int, tok[:3])
        allele = float(tok[3])
        vals = [float(x) for x in tok[4:]]
        rows.append((pop, trait, locus, allele, vals))
    if not rows:
        raise ValueError("qfreq contains no locus rows")
    pops = sorted({r[0] for r in rows})
    loci = sorted({r[2] for r in rows})
    if loci != list(range(1, len(effects) + 1)):
        raise ValueError("qfreq loci do not match supplied effects")
    freq = np.full((len(generations), len(pops), len(effects)), np.nan, dtype=float)
    pop_index = {p: i for i, p in enumerate(pops)}
    for pop, trait, locus, allele, vals in rows:
        if trait != 1:
            raise ValueError("R3.6D parser expects one NEMO quantitative trait per job")
        freq[:, pop_index[pop], locus - 1] = np.asarray(vals, dtype=float)
    if np.any(~np.isfinite(freq)) or np.any(freq < -1e-12) or np.any(freq > 1 + 1e-12):
        raise ValueError("invalid or incomplete qfreq frequencies")
    freq = np.clip(freq, 0.0, 1.0)
    mean = np.einsum("gpl,l->gp", 2.0 * freq - 1.0, effects)
    va = np.einsum("gpl,l->gp", 2.0 * freq * (1.0 - freq), effects * effects)
    return {
        "generations": np.asarray(generations, dtype=np.int64),
        "patch_ids_1based": np.asarray(pops, dtype=np.int64),
        "allele_frequencies": freq,
        "trait_mean": mean,
        "additive_variance": va,
    }


def collect_nemo242_evidence(
    *,
    experiment_sha256: str,
    run_id: str,
    workdir: str | Path,
    arcana_effect_a: Sequence[float],
    execution_returncode: int,
    stdout: str = "",
    stderr: str = "",
) -> ScientificEvidenceBundle:
    root = Path(workdir)
    qfreqs = sorted(root.glob("*.qfreq"))
    arrays: dict[str, np.ndarray] = {}
    metrics: dict[str, object] = {
        "returncode": int(execution_returncode),
        "qfreq_file_count": len(qfreqs),
        "execution_attempted": True,
    }
    status = "ENGINE_FAILED"
    unsupported = [
        "R3.6D does not map ARCANA mu/b Riccati homeostasis to NEMO mutation-selection parameters.",
        "NEMO breed_disperse is a backward/gametic migration reference; it is not asserted to be ontologically identical to ARCANA deme exchange.",
        "NEMO evidence cannot define ARCANA species identity/speciation or write canonical state.",
    ]
    if execution_returncode == 0 and qfreqs:
        parsed = parse_qfreq(qfreqs[0], arcana_effect_a=arcana_effect_a)
        arrays.update(parsed)
        metrics.update({
            "qfreq_sha256": file_sha256(qfreqs[0]),
            "final_max_va": float(np.max(parsed["additive_variance"][-1])),
            "final_mean_va": float(np.mean(parsed["additive_variance"][-1])),
            "final_trait_spread": float(np.max(parsed["trait_mean"][-1]) - np.min(parsed["trait_mean"][-1])),
        })
        status = "ENGINE_COMPLETED_QFREQ_PARSED"
    elif execution_returncode == 0:
        status = "ENGINE_COMPLETED_OUTPUT_MISSING_QFREQ"
    return ScientificEvidenceBundle(
        experiment_sha256=experiment_sha256,
        engine=NEMO_242,
        engine_run_id=run_id,
        status=status,
        metrics=metrics,
        arrays=arrays,
        assumptions=(
            "Primary R3.6D NEMO reference isolates admixture/recombination/drift with mutation=0 and no selection.",
            "Cross-engine inference uses matched no-flow controls and population-size sensitivity.",
        ),
        unsupported_mappings=tuple(unsupported),
        stdout_sha256=sha256(stdout.encode("utf-8", errors="replace")).hexdigest(),
        stderr_sha256=sha256(stderr.encode("utf-8", errors="replace")).hexdigest(),
    )


def run_nemo242_ini(ini_path: str | Path, *, executable: str = NEMO_REQUIRED_EXECUTABLE, timeout_s: float | None = None) -> subprocess.CompletedProcess[str]:
    pre = preflight_nemo242(executable)
    if not pre.pass_exact_242:
        raise FileNotFoundError(f"NEMO 2.4.2 preflight failed: {pre.reason}")
    ini = Path(ini_path).resolve()
    return subprocess.run([pre.resolved_path or executable, ini.name], cwd=ini.parent, text=True, capture_output=True, check=False, timeout=timeout_s)


def matched_no_flow_scenario(scenario: NemoBenchmarkScenario, *, name_suffix: str = "MATCHED_NO_FLOW") -> NemoBenchmarkScenario:
    if len(scenario.phases) != 1:
        raise ValueError("matched no-flow helper requires single-phase scenario")
    z = np.array(scenario.normalized_trait_means, copy=True)
    q = np.array(scenario.normalized_additive_variance, copy=True)
    n = np.array(scenario.population_individuals, copy=True)
    zero = np.zeros_like(scenario.phases[0].exchange_matrix)
    return NemoBenchmarkScenario(
        name=f"{scenario.name}__{name_suffix}",
        normalized_trait_means=z,
        normalized_additive_variance=q,
        population_individuals=n,
        phases=(ExchangePhase("NO_FLOW_MATCHED_CONTROL", 0, 1, zero),),
        generation_time_years=scenario.generation_time_years,
        notes=scenario.notes + ("Matched no-flow control: identical starting QTL moments/population, only dispersal removed",),
    )


def simulate_arcana_admixture_only_probe(
    scenario: NemoBenchmarkScenario,
    *,
    macro_intervals: int = 1,
    substeps_per_interval: int = 1,
) -> dict:
    """Run only ARCANA's moment-mixing operator, without Riccati homeostasis.

    This is the like-for-like comparator for the primary R3.6D NEMO protocol,
    which has mutation=0 and no selection. A matched no-flow NEMO control then
    removes finite-N drift/recombination from the cross-engine contrast.
    """
    from arcana_worldsim.post_cha1 import additive_variance as av
    from .cadence_validation import CadenceNormalizationSpec, edge_hazard_substep_exchange, _variance_cfg

    if len(scenario.phases) != 1:
        raise ValueError("admixture-only probe requires single-phase scenario")
    if macro_intervals < 1 or substeps_per_interval not in (1, 5):
        raise ValueError("authorized probe is 1x125k or 5x25k")
    spec = CadenceNormalizationSpec()
    z2 = np.asarray(scenario.normalized_trait_means, dtype=float).copy()
    q2 = np.asarray(scenario.normalized_additive_variance, dtype=float).copy()
    nd = z2.shape[0]
    z = np.column_stack([z2, np.zeros(nd)])
    va = np.column_stack([q2, np.full(nd, spec.q_star)])
    pop = np.asarray(scenario.population_individuals, dtype=float)
    ri = np.zeros((nd, nd), dtype=float)
    roots = np.zeros(nd, dtype=int)
    cfg = _variance_cfg(spec)
    base = np.asarray(scenario.phases[0].exchange_matrix, dtype=float)
    g = base if substeps_per_interval == 1 else edge_hazard_substep_exchange(base, 5)
    for _ in range(macro_intervals):
        for _ in range(substeps_per_interval):
            z, va, _flow = av.gene_flow_moment_mix(z, va, pop, g, ri, roots, cfg)
    return {
        "schema": "ARCANA_R36D_ADMIXTURE_ONLY_PROBE_V1",
        "scenario": scenario.name,
        "macro_intervals": int(macro_intervals),
        "substeps_per_interval": int(substeps_per_interval),
        "final_trait_mean": z[:, :2].tolist(),
        "final_additive_variance": va[:, :2].tolist(),
        "final_mean_va": float(np.mean(va[:, :2])),
        "final_max_va": float(np.max(va[:, :2])),
        "homeostasis_applied": False,
        "mutation_applied": False,
        "canonical_write_allowed": False,
    }
