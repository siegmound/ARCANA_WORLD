from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
from typing import Mapping
import os
import subprocess

from .contracts import EngineDescriptor, ScientificEvidenceBundle, ScientificExperiment


@dataclass(frozen=True)
class PreparedEngineRun:
    command: tuple[str, ...]
    cwd: Path
    environment: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class EngineExecutionRecord:
    returncode: int
    stdout: str
    stderr: str

    @property
    def stdout_sha256(self) -> str:
        return sha256(self.stdout.encode("utf-8", errors="replace")).hexdigest()

    @property
    def stderr_sha256(self) -> str:
        return sha256(self.stderr.encode("utf-8", errors="replace")).hexdigest()


class ScientificEngineAdapter(ABC):
    descriptor: EngineDescriptor

    @abstractmethod
    def prepare(self, experiment: ScientificExperiment, workdir: str | Path) -> PreparedEngineRun:
        raise NotImplementedError

    @abstractmethod
    def parse(self, experiment: ScientificExperiment, workdir: str | Path, execution: EngineExecutionRecord) -> ScientificEvidenceBundle:
        raise NotImplementedError

    def execute(self, prepared: PreparedEngineRun, *, timeout_s: float | None = None) -> EngineExecutionRecord:
        env = os.environ.copy()
        env.update(dict(prepared.environment))
        proc = subprocess.run(
            list(prepared.command), cwd=str(prepared.cwd), env=env,
            text=True, capture_output=True, timeout=timeout_s, check=False,
        )
        return EngineExecutionRecord(returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)

    def run(self, experiment: ScientificExperiment, workdir: str | Path, *, timeout_s: float | None = None) -> ScientificEvidenceBundle:
        if experiment.engine.name != self.descriptor.name or experiment.engine.version != self.descriptor.version:
            raise ValueError("Experiment engine descriptor does not match adapter")
        prepared = self.prepare(experiment, workdir)
        execution = self.execute(prepared, timeout_s=timeout_s)
        return self.parse(experiment, workdir, execution)
