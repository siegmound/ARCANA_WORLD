from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from hashlib import sha256
import json

import numpy as np

from .contracts import ScientificExperiment
from .registry import NEMO_242


@dataclass(frozen=True)
class ExchangePhase:
    name: str
    start_generation: int
    end_generation: int
    exchange_matrix: np.ndarray

    def __post_init__(self) -> None:
        m = np.asarray(self.exchange_matrix, dtype=float)
        if m.ndim != 2 or m.shape[0] != m.shape[1]:
            raise ValueError("exchange_matrix must be square")
        if np.any(m < -1e-15) or np.any(m.sum(axis=1) > 1.0 + 1e-12):
            raise ValueError("exchange matrix must be non-negative with row sums <=1")
        if np.max(np.abs(np.diag(m))) > 1e-15:
            raise ValueError("ARCANA exchange matrices use zero diagonal; NEMO self-retention is derived")
        if self.start_generation < 0 or self.end_generation <= self.start_generation:
            raise ValueError("invalid generation interval")
        object.__setattr__(self, "exchange_matrix", m.copy())
        self.exchange_matrix.setflags(write=False)


@dataclass(frozen=True)
class NemoBenchmarkScenario:
    name: str
    normalized_trait_means: np.ndarray
    normalized_additive_variance: np.ndarray
    population_individuals: np.ndarray
    phases: tuple[ExchangePhase, ...]
    generation_time_years: float = 5.0
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        z = np.asarray(self.normalized_trait_means, dtype=float)
        q = np.asarray(self.normalized_additive_variance, dtype=float)
        n = np.asarray(self.population_individuals, dtype=int)
        if z.ndim != 2 or q.shape != z.shape:
            raise ValueError("means/q must have patch x trait shape")
        if n.shape != (z.shape[0],) or np.any(n < 20):
            raise ValueError("population_individuals must have >=20 per patch")
        if not self.phases:
            raise ValueError("at least one exchange phase is required")
        if any(p.exchange_matrix.shape != (z.shape[0], z.shape[0]) for p in self.phases):
            raise ValueError("phase exchange shape mismatch")
        object.__setattr__(self, "normalized_trait_means", z.copy()); self.normalized_trait_means.setflags(write=False)
        object.__setattr__(self, "normalized_additive_variance", q.copy()); self.normalized_additive_variance.setflags(write=False)
        object.__setattr__(self, "population_individuals", n.copy()); self.population_individuals.setflags(write=False)
        object.__setattr__(self, "notes", tuple(str(x) for x in self.notes))

    @property
    def generations(self) -> int:
        return max(p.end_generation for p in self.phases)


def _zero(n: int) -> np.ndarray:
    return np.zeros((n, n), dtype=float)


def _symmetric_exchange(n: int, pairs: Iterable[tuple[int, int, float]]) -> np.ndarray:
    m = np.zeros((n, n), dtype=float)
    for i, j, x in pairs:
        m[i, j] = float(x); m[j, i] = float(x)
    if np.any(m.sum(axis=1) > 1.0 + 1e-12):
        raise ValueError("exchange exceeds row budget")
    return m


def canonical_r36b_scenarios(q_star: float = 0.045, n_individuals: int = 2000) -> tuple[NemoBenchmarkScenario, ...]:
    q2 = np.full((2, 2), q_star, dtype=float)
    q4 = np.full((4, 2), q_star, dtype=float)
    return (
        NemoBenchmarkScenario(
            name="B0_EQUILIBRIUM_NO_FLOW",
            normalized_trait_means=np.zeros((2, 2)),
            normalized_additive_variance=q2,
            population_individuals=np.full(2, n_individuals, dtype=int),
            phases=(ExchangePhase("NO_FLOW", 0, 1000, _zero(2)),),
            notes=("Control for mutation/selection/drift homeostasis without admixture",),
        ),
        NemoBenchmarkScenario(
            name="B1_TWO_DEME_ADMIXTURE",
            normalized_trait_means=np.array([[-0.50, 0.35], [0.50, -0.35]], dtype=float),
            normalized_additive_variance=q2,
            population_individuals=np.full(2, n_individuals, dtype=int),
            phases=(ExchangePhase("CONSTANT_ADMIXTURE", 0, 1000, _symmetric_exchange(2, [(0, 1, 0.05)])),),
            notes=("Persistent two-deme admixture with genetically encoded mean separation",),
        ),
        NemoBenchmarkScenario(
            name="B2_FRAGMENTATION_RECONNECTION",
            normalized_trait_means=np.array([[-0.60, -0.20], [-0.20, 0.20], [0.20, -0.20], [0.60, 0.20]], dtype=float),
            normalized_additive_variance=q4,
            population_individuals=np.full(4, n_individuals, dtype=int),
            phases=(
                ExchangePhase("CONNECTED_BURNIN", 0, 250, _symmetric_exchange(4, [(0,1,0.03),(1,2,0.03),(2,3,0.03)])),
                ExchangePhase("FRAGMENTED", 250, 650, _symmetric_exchange(4, [(0,1,0.03),(2,3,0.03)])),
                ExchangePhase("RECONNECTED", 650, 1200, _symmetric_exchange(4, [(0,1,0.03),(1,2,0.03),(2,3,0.03)])),
            ),
            notes=("Controlled connected-fragmented-reconnected metapopulation", "No ARCANA speciation authority is delegated"),
        ),
        NemoBenchmarkScenario(
            name="B3_HIGH_ADMIXTURE_STRESS",
            normalized_trait_means=np.array([[-0.90, 0.70], [-0.30, 0.25], [0.30, -0.25], [0.90, -0.70]], dtype=float),
            normalized_additive_variance=q4,
            population_individuals=np.full(4, n_individuals, dtype=int),
            phases=(ExchangePhase("HIGH_EXCHANGE", 0, 1000, _symmetric_exchange(4, [(0,1,0.07),(1,2,0.07),(2,3,0.07),(0,3,0.03)])),),
            notes=("Stress-envelope benchmark designed to expose between-deme variance injection",),
        ),
    )


def scenario_to_experiment(s: NemoBenchmarkScenario, *, seed: int, replicate_id: int) -> ScientificExperiment:
    nd, nt = s.normalized_trait_means.shape
    # R3.6B uses normalized traits/scales=1 so target q is numerically identical
    # to additive variance in the bridge. This prevents arbitrary unit mapping.
    h = sha256()
    h.update(s.name.encode("utf-8"))
    h.update(np.ascontiguousarray(s.normalized_trait_means).tobytes())
    h.update(np.ascontiguousarray(s.normalized_additive_variance).tobytes())
    h.update(np.ascontiguousarray(s.population_individuals).tobytes())
    for p in s.phases:
        h.update(p.name.encode("utf-8")); h.update(str(p.start_generation).encode("ascii")); h.update(str(p.end_generation).encode("ascii")); h.update(np.ascontiguousarray(p.exchange_matrix).tobytes())
    scenario_sha = h.hexdigest()
    return ScientificExperiment(
        experiment_id=f"R36B-{s.name}-r{replicate_id:03d}",
        arcana_stage="v0.6D1-R3.6B",
        age_ma=191.0,
        engine=NEMO_242,
        source_state_sha256=scenario_sha,
        random_seed=int(seed),
        replicate_id=int(replicate_id),
        metadata={
            "purpose": "CONTROLLED_NEMO_QTL_REFERENCE_MICROBENCHMARK",
            "scenario": s.name,
            "normalized_trait_space": True,
            "q_star": 0.045,
            "generation_count": s.generations,
            "phase_count": len(s.phases),
        },
        arrays={
            "component_ids": np.array([f"P{i:03d}" for i in range(nd)]),
            "component_species": np.array(["REFERENCE_SPECIES"] * nd),
            "population_total": s.population_individuals.astype(float),
            "trait_mean": np.column_stack([s.normalized_trait_means, np.zeros(nd)]) if nt == 2 else s.normalized_trait_means,
            "additive_variance": np.column_stack([s.normalized_additive_variance, np.full(nd, 0.045)]) if nt == 2 else s.normalized_additive_variance,
            "generation_time_years": np.full(nd, s.generation_time_years, dtype=float),
            "exchange_matrix": s.phases[0].exchange_matrix,
        },
        assumptions=(
            "Normalized benchmark axes use trait scale 1.0 so q equals VA numerically",
            "NEMO is reference evidence only and cannot alter ARCANA canonical state",
            "No NEMO-derived species identity/speciation decision is authoritative",
        ),
        requested_outputs=("trait_mean", "additive_variance", "allele_frequencies", "heterozygosity", "population_per_patch"),
    )


def write_scenario(s: NemoBenchmarkScenario, outdir: str | Path) -> None:
    root = Path(outdir); root.mkdir(parents=True, exist_ok=True)
    phases = []
    for i, p in enumerate(s.phases):
        fn = f"exchange_phase_{i:02d}_{p.name}.tsv"
        np.savetxt(root / fn, p.exchange_matrix, delimiter="\t", fmt="%.17g")
        phases.append({"name": p.name, "start_generation": p.start_generation, "end_generation": p.end_generation, "exchange_file": fn})
    payload = {
        "schema": "ARCANA_NEMO_R36B_BENCHMARK_SCENARIO_V1",
        "name": s.name,
        "generation_time_years": s.generation_time_years,
        "generations": s.generations,
        "population_individuals": s.population_individuals.tolist(),
        "normalized_trait_means": s.normalized_trait_means.tolist(),
        "normalized_additive_variance": s.normalized_additive_variance.tolist(),
        "phases": phases,
        "notes": list(s.notes),
        "authority": {"canonical_write_allowed": False, "speciation_authority": False},
    }
    (root / "scenario.json").write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
