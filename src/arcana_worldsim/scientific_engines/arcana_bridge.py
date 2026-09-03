from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from typing import Any, Mapping, Sequence
import json
import numpy as np

from .contracts import EngineDescriptor, ScientificExperiment
from .serialization import file_sha256


def _semantic_state_hash(stage: str, arrays: Mapping[str, np.ndarray], labels: Mapping[str, Any]) -> str:
    h = sha256()
    h.update(stage.encode("utf-8"))
    h.update(json.dumps(labels, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8"))
    for name in sorted(arrays):
        arr = np.ascontiguousarray(arrays[name])
        h.update(name.encode("utf-8")); h.update(str(arr.dtype).encode("ascii")); h.update(str(arr.shape).encode("ascii")); h.update(arr.tobytes())
    return h.hexdigest()


def experiment_from_r3_state_npz(
    state_npz: str | Path,
    *,
    engine: EngineDescriptor,
    experiment_id: str,
    arcana_stage: str,
    age_ma: float,
    random_seed: int,
    replicate_id: int = 0,
    component_indices: Sequence[int] | None = None,
    include_spatial_population: bool = False,
    extra_arrays: Mapping[str, np.ndarray] | None = None,
    metadata: Mapping[str, Any] | None = None,
    assumptions: Sequence[str] = (),
    requested_outputs: Sequence[str] = (),
) -> ScientificExperiment:
    path = Path(state_npz)
    with np.load(path, allow_pickle=False) as src:
        n = int(len(src["component_ids"]))
        idx = np.arange(n, dtype=int) if component_indices is None else np.asarray(component_indices, dtype=int)
        if idx.ndim != 1 or np.any(idx < 0) or np.any(idx >= n):
            raise ValueError("Invalid component_indices")
        population = np.asarray(src["population"])[idx]
        arrays: dict[str, np.ndarray] = {
            "component_index": idx,
            "component_ids": np.asarray(src["component_ids"])[idx],
            "component_root_species": np.asarray(src["component_root_species"])[idx],
            "component_species": np.asarray(src["component_species"])[idx],
            "component_guild": np.asarray(src["component_guild"])[idx],
            "population_total": population.sum(axis=(1, 2)),
            "trait_mean": np.asarray(src["trait"])[idx],
            "additive_variance": np.asarray(src["va"])[idx],
            "generation_time_years": np.asarray(src["generation_time"])[idx],
            "ri": np.asarray(src["ri"])[np.ix_(idx, idx)],
            "isolation_clock_generations": np.asarray(src["clock"])[np.ix_(idx, idx)],
            "contact": np.asarray(src["contact"])[np.ix_(idx, idx)],
            "trait_distance": np.asarray(src["trait_distance"])[np.ix_(idx, idx)],
        }
        if include_spatial_population:
            arrays["population_grid"] = population
    for key, val in (extra_arrays or {}).items():
        arrays[str(key)] = np.asarray(val)
    source_hash = file_sha256(path)
    meta = {
        "bridge_schema": "ARCANA_R3_STATE_TO_SCIENTIFIC_ENGINE_V1",
        "source_state_file": path.name,
        "component_count": int(len(idx)),
        "full_source_component_count": n,
        **dict(metadata or {}),
    }
    return ScientificExperiment(
        experiment_id=experiment_id, arcana_stage=arcana_stage, age_ma=age_ma,
        engine=engine, source_state_sha256=source_hash, random_seed=random_seed,
        replicate_id=replicate_id, metadata=meta, arrays=arrays,
        assumptions=tuple(assumptions), requested_outputs=tuple(requested_outputs),
    )


def experiment_from_runtime_result(
    result: Mapping[str, Any], *, engine: EngineDescriptor, experiment_id: str,
    age_ma: float, random_seed: int, replicate_id: int = 0,
    component_indices: Sequence[int] | None = None,
    extra_arrays: Mapping[str, np.ndarray] | None = None,
    metadata: Mapping[str, Any] | None = None,
    assumptions: Sequence[str] = (), requested_outputs: Sequence[str] = (),
) -> ScientificExperiment:
    n = len(result["component_ids"])
    idx = np.arange(n, dtype=int) if component_indices is None else np.asarray(component_indices, dtype=int)
    pop = np.asarray(result["population"])[idx]
    arrays = {
        "component_index": idx,
        "component_ids": np.asarray(result["component_ids"])[idx],
        "component_root_species": np.asarray(result["component_root_species"])[idx],
        "component_species": np.asarray(result["component_species"])[idx],
        "component_guild": np.asarray(result["component_guild"])[idx],
        "population_total": pop.sum(axis=(1, 2)),
        "trait_mean": np.asarray(result["trait"])[idx],
        "additive_variance": np.asarray(result["va"])[idx],
        "generation_time_years": np.asarray(result["generation_time"])[idx],
        "ri": np.asarray(result["ri"])[np.ix_(idx, idx)],
        "isolation_clock_generations": np.asarray(result["clock"])[np.ix_(idx, idx)],
        "contact": np.asarray(result["contact"])[np.ix_(idx, idx)],
        "trait_distance": np.asarray(result["trait_distance"])[np.ix_(idx, idx)],
    }
    arrays.update({str(k): np.asarray(v) for k, v in (extra_arrays or {}).items()})
    stage = str(result.get("stage", "UNKNOWN_ARCANA_STAGE"))
    state_hash = _semantic_state_hash(stage, arrays, {"component_ids": [str(x) for x in np.asarray(result["component_ids"])[idx]]})
    return ScientificExperiment(
        experiment_id=experiment_id, arcana_stage=stage, age_ma=age_ma,
        engine=engine, source_state_sha256=state_hash, random_seed=random_seed,
        replicate_id=replicate_id, metadata={"bridge_schema": "ARCANA_RUNTIME_TO_SCIENTIFIC_ENGINE_V1", **dict(metadata or {})},
        arrays=arrays, assumptions=tuple(assumptions), requested_outputs=tuple(requested_outputs),
    )
