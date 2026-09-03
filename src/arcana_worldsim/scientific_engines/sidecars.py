from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from .base import EngineExecutionRecord, PreparedEngineRun, ScientificEngineAdapter
from .contracts import EngineDescriptor, ScientificEvidenceBundle, ScientificExperiment
from .registry import MADINGLEY, GEONOMICS, CDMETAPOP, RANGESHIFTER


@dataclass(frozen=True)
class SidecarSpec:
    command: tuple[str, ...] | None = None
    adapter_protocol_version: str = "ARCANA_SCIENTIFIC_SIDECAR_V1"


class ManifestSidecarAdapter(ScientificEngineAdapter):
    descriptor: EngineDescriptor

    def __init__(self, descriptor: EngineDescriptor, spec: SidecarSpec = SidecarSpec()):
        self.descriptor = descriptor
        self.spec = spec

    def prepare(self, experiment: ScientificExperiment, workdir: str | Path) -> PreparedEngineRun:
        root = Path(workdir); root.mkdir(parents=True, exist_ok=True)
        manifest = {
            "schema": self.spec.adapter_protocol_version,
            "engine": {"name": self.descriptor.name, "version": self.descriptor.version, "role": self.descriptor.role.value},
            "experiment_sha256": experiment.semantic_sha256,
            "source_state_sha256": experiment.source_state_sha256,
            "authority": {"canonical_write_allowed": False, "promotion": "REVIEW_REQUIRED"},
            "input_arrays": {k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in experiment.arrays.items()},
            "requested_outputs": list(experiment.requested_outputs),
            "assumptions": list(experiment.assumptions),
        }
        (root / "arcana_sidecar_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        command = self.spec.command or ("python", "-c", f"print('ARCANA_{self.descriptor.name.upper()}_SIDECAR_PREPARED')")
        return PreparedEngineRun(command=tuple(command), cwd=root)

    def parse(self, experiment: ScientificExperiment, workdir: str | Path, execution: EngineExecutionRecord) -> ScientificEvidenceBundle:
        return ScientificEvidenceBundle(
            experiment_sha256=experiment.semantic_sha256, engine=self.descriptor,
            engine_run_id=f"{experiment.experiment_id}:{self.descriptor.name}:rep{experiment.replicate_id}",
            status="SIDECAR_INTERFACE_PREPARED" if self.spec.command is None else ("ENGINE_COMPLETED" if execution.returncode == 0 else "ENGINE_FAILED"),
            metrics={"returncode": execution.returncode, "execution_attempted": self.spec.command is not None},
            assumptions=experiment.assumptions,
            unsupported_mappings=("Engine-specific scientific state mapping must be validated in its dedicated integration stage.",),
            stdout_sha256=execution.stdout_sha256, stderr_sha256=execution.stderr_sha256,
        )


class MadingleyAdapter(ManifestSidecarAdapter):
    def __init__(self, spec: SidecarSpec = SidecarSpec()): super().__init__(MADINGLEY, spec)


class GeonomicsAdapter(ManifestSidecarAdapter):
    def __init__(self, spec: SidecarSpec = SidecarSpec()): super().__init__(GEONOMICS, spec)


class CDMetaPOPAdapter(ManifestSidecarAdapter):
    def __init__(self, spec: SidecarSpec = SidecarSpec()): super().__init__(CDMETAPOP, spec)


class RangeShifterAdapter(ManifestSidecarAdapter):
    def __init__(self, spec: SidecarSpec = SidecarSpec()): super().__init__(RANGESHIFTER, spec)
