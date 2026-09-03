from __future__ import annotations

from pathlib import Path
from hashlib import sha256
import json
import numpy as np

from .contracts import EngineDescriptor, EngineRole, ScientificExperiment, ScientificEvidenceBundle


def file_sha256(path: str | Path) -> str:
    h = sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_experiment(exp: ScientificExperiment, directory: str | Path) -> Path:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    arrays_path = root / "arrays.npz"
    np.savez_compressed(arrays_path, **{k: np.asarray(v) for k, v in exp.arrays.items()})
    manifest = exp.manifest()
    manifest["arrays_file"] = arrays_path.name
    manifest["arrays_file_sha256"] = file_sha256(arrays_path)
    path = root / "experiment.json"
    path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def load_experiment(directory: str | Path) -> ScientificExperiment:
    root = Path(directory)
    manifest = json.loads((root / "experiment.json").read_text(encoding="utf-8"))
    arrays_path = root / manifest["arrays_file"]
    if file_sha256(arrays_path) != manifest["arrays_file_sha256"]:
        raise ValueError("Experiment array payload hash mismatch")
    with np.load(arrays_path, allow_pickle=False) as data:
        arrays = {k: data[k] for k in data.files}
    eng = manifest["engine"]
    descriptor = EngineDescriptor(
        name=eng["name"], version=eng["version"], role=EngineRole(eng["role"]),
        execution_mode=eng["execution_mode"], license_id=eng.get("license_id"),
        canonical_write_allowed=False, notes=tuple(eng.get("notes", [])),
    )
    exp = ScientificExperiment(
        experiment_id=manifest["experiment_id"], arcana_stage=manifest["arcana_stage"],
        age_ma=manifest["age_ma"], engine=descriptor, source_state_sha256=manifest["source_state_sha256"],
        random_seed=manifest["random_seed"], replicate_id=manifest["replicate_id"],
        spatial_domain=manifest.get("spatial_domain", {}), metadata=manifest.get("metadata", {}),
        arrays=arrays, assumptions=tuple(manifest.get("assumptions", [])),
        requested_outputs=tuple(manifest.get("requested_outputs", [])),
    )
    if exp.semantic_sha256 != manifest["semantic_sha256"]:
        raise ValueError("Experiment semantic hash mismatch")
    return exp


def save_evidence(bundle: ScientificEvidenceBundle, directory: str | Path) -> Path:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    arrays_path = root / "evidence_arrays.npz"
    np.savez_compressed(arrays_path, **{k: np.asarray(v) for k, v in bundle.arrays.items()})
    payload = {
        "schema": "ARCANA_SCIENTIFIC_EVIDENCE_V1",
        "semantic_sha256": bundle.semantic_sha256,
        "experiment_sha256": bundle.experiment_sha256,
        "engine": {"name": bundle.engine.name, "version": bundle.engine.version, "role": bundle.engine.role.value},
        "engine_run_id": bundle.engine_run_id,
        "status": bundle.status,
        "metrics": dict(bundle.metrics),
        "assumptions": list(bundle.assumptions),
        "unsupported_mappings": list(bundle.unsupported_mappings),
        "stdout_sha256": bundle.stdout_sha256,
        "stderr_sha256": bundle.stderr_sha256,
        "arrays_file": arrays_path.name,
        "arrays_file_sha256": file_sha256(arrays_path),
        "canonical_write_allowed": False,
        "promotion_status": "REVIEW_REQUIRED",
    }
    path = root / "evidence.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path
