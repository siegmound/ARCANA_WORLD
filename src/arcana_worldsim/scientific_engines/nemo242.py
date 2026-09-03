from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Mapping
import csv
import json
import shlex

import numpy as np

from .base import EngineExecutionRecord, PreparedEngineRun, ScientificEngineAdapter
from .contracts import ScientificEvidenceBundle, ScientificExperiment
from .registry import NEMO_242
from .serialization import file_sha256


@dataclass(frozen=True)
class Nemo242MappingSpec:
    population_units_to_individuals: float
    carrying_capacity_multiplier: float
    quantitative_trait_axes: tuple[int, ...] = (0, 1)
    loci_per_trait: int = 64
    generations: int = 1000
    exchange_matrix_array: str = "exchange_matrix"
    template_path: str | None = None
    executable: str = "nemo2.4.2"

    def __post_init__(self) -> None:
        if self.population_units_to_individuals <= 0:
            raise ValueError("population_units_to_individuals must be >0")
        if self.carrying_capacity_multiplier < 1:
            raise ValueError("carrying_capacity_multiplier must be >=1")
        if self.loci_per_trait <= 0 or self.generations <= 0:
            raise ValueError("loci_per_trait and generations must be positive")


class Nemo242Adapter(ScientificEngineAdapter):
    descriptor = NEMO_242

    def __init__(self, spec: Nemo242MappingSpec):
        self.spec = spec

    def _validate(self, exp: ScientificExperiment) -> None:
        required = {"component_ids", "component_species", "population_total", "trait_mean", "additive_variance", "generation_time_years", self.spec.exchange_matrix_array}
        missing = sorted(required - set(exp.arrays))
        if missing:
            raise ValueError(f"NEMO bridge missing required arrays: {missing}")
        n = len(exp.arrays["component_ids"])
        G = np.asarray(exp.arrays[self.spec.exchange_matrix_array], dtype=float)
        if G.shape != (n, n):
            raise ValueError("exchange matrix must be NxN for selected ARCANA demes")
        if np.any(G < -1e-15):
            raise ValueError("exchange matrix may not contain negative entries")
        if np.any(G.sum(axis=1) > 1.0 + 1e-12):
            raise ValueError("exchange row sums must be <=1")
        trait = np.asarray(exp.arrays["trait_mean"])
        va = np.asarray(exp.arrays["additive_variance"])
        if trait.ndim != 2 or va.shape != trait.shape:
            raise ValueError("trait_mean and additive_variance must have same 2D shape")
        if any(ax < 0 or ax >= trait.shape[1] for ax in self.spec.quantitative_trait_axes):
            raise ValueError("quantitative_trait_axes out of range")

    def _write_bridge_files(self, exp: ScientificExperiment, root: Path) -> None:
        ids = np.asarray(exp.arrays["component_ids"]).astype(str)
        species = np.asarray(exp.arrays["component_species"]).astype(str)
        pop = np.asarray(exp.arrays["population_total"], dtype=float)
        gen = np.asarray(exp.arrays["generation_time_years"], dtype=float)
        trait = np.asarray(exp.arrays["trait_mean"], dtype=float)
        va = np.asarray(exp.arrays["additive_variance"], dtype=float)
        exchange = np.asarray(exp.arrays[self.spec.exchange_matrix_array], dtype=float)

        with (root / "arcana_patches.tsv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["patch_index", "arcana_component_id", "arcana_current_species", "initial_individuals", "carrying_capacity", "generation_time_years"])
            for i in range(len(ids)):
                n0 = max(2, int(round(pop[i] * self.spec.population_units_to_individuals)))
                K = max(n0, int(round(n0 * self.spec.carrying_capacity_multiplier)))
                w.writerow([i, ids[i], species[i], n0, K, f"{gen[i]:.17g}"])

        with (root / "arcana_quantitative_traits.tsv").open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f, delimiter="\t")
            w.writerow(["patch_index", "axis", "arcana_mean", "arcana_additive_variance", "loci_per_trait"])
            for i in range(len(ids)):
                for ax in self.spec.quantitative_trait_axes:
                    w.writerow([i, ax, f"{trait[i, ax]:.17g}", f"{va[i, ax]:.17g}", self.spec.loci_per_trait])

        np.savetxt(root / "arcana_exchange_matrix.tsv", exchange, delimiter="\t", fmt="%.17g")
        bridge = {
            "schema": "ARCANA_NEMO_2_4_2_REFERENCE_BRIDGE_V1",
            "experiment_sha256": exp.semantic_sha256,
            "source_state_sha256": exp.source_state_sha256,
            "nemo_version_required": "2.4.2",
            "replicate_id": exp.replicate_id,
            "random_seed": exp.random_seed,
            "generations": self.spec.generations,
            "mapping": {
                "population_units_to_individuals": self.spec.population_units_to_individuals,
                "carrying_capacity_multiplier": self.spec.carrying_capacity_multiplier,
                "quantitative_trait_axes": list(self.spec.quantitative_trait_axes),
                "loci_per_trait": self.spec.loci_per_trait,
                "exchange_matrix_semantics": "ARCANA_EFFECTIVE_EXCHANGE_INPUT_EXPLICITLY_SUPPLIED_FOR_REFERENCE_EXPERIMENT",
            },
            "authority": {
                "arcana_canonical_write_allowed": False,
                "nemo_species_identity_authority": False,
                "nemo_speciation_authority": False,
                "purpose": "INDEPENDENT_QUANTITATIVE_GENETICS_REFERENCE",
            },
        }
        (root / "arcana_nemo_bridge.json").write_text(json.dumps(bridge, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    def _render_template(self, exp: ScientificExperiment, root: Path) -> Path:
        if self.spec.template_path is None:
            # Deliberately do not guess NEMO parameter names. The bridge is fully
            # materialized, but executable promotion requires a version-validated
            # NEMO 2.4.2 template in the next calibration substage.
            marker = root / "NEMO_TEMPLATE_REQUIRED.txt"
            marker.write_text(
                "ARCANA R3.6A prepared the NEMO 2.4.2 neutral bridge files.\n"
                "Provide a NEMO 2.4.2-validated .ini template before executable reference runs.\n"
                "No inferred/guessed NEMO parameter names are permitted by the reuse-first policy.\n",
                encoding="utf-8",
            )
            return marker
        template_path = Path(self.spec.template_path)
        text = template_path.read_text(encoding="utf-8")
        replacements = {
            "{{ARCANA_RANDOM_SEED}}": str(exp.random_seed),
            "{{ARCANA_GENERATIONS}}": str(self.spec.generations),
            "{{ARCANA_PATCH_FILE}}": str((root / "arcana_patches.tsv").resolve()),
            "{{ARCANA_TRAIT_FILE}}": str((root / "arcana_quantitative_traits.tsv").resolve()),
            "{{ARCANA_EXCHANGE_MATRIX_FILE}}": str((root / "arcana_exchange_matrix.tsv").resolve()),
            "{{ARCANA_EXPERIMENT_SHA256}}": exp.semantic_sha256,
        }
        for key, value in replacements.items():
            text = text.replace(key, value)
        unresolved = [k for k in replacements if k in text]
        if unresolved:
            raise ValueError(f"Unresolved ARCANA template placeholders: {unresolved}")
        out = root / "Nemo2_ARCANA.ini"
        out.write_text(text, encoding="utf-8")
        return out

    def prepare(self, experiment: ScientificExperiment, workdir: str | Path) -> PreparedEngineRun:
        self._validate(experiment)
        root = Path(workdir)
        root.mkdir(parents=True, exist_ok=True)
        self._write_bridge_files(experiment, root)
        ini = self._render_template(experiment, root)
        if self.spec.template_path is None:
            # Preparation-only mode; use a portable Python no-op so that generic
            # orchestration can still validate the bridge without NEMO installed.
            return PreparedEngineRun(command=("python", "-c", "print('ARCANA_NEMO_PREPARED_NO_EXECUTION')"), cwd=root)
        return PreparedEngineRun(command=(self.spec.executable, str(ini.name)), cwd=root)

    def parse(self, experiment: ScientificExperiment, workdir: str | Path, execution: EngineExecutionRecord) -> ScientificEvidenceBundle:
        root = Path(workdir)
        bridge_sha = file_sha256(root / "arcana_nemo_bridge.json")
        status = "PREPARED_REFERENCE_INPUTS" if self.spec.template_path is None else ("ENGINE_COMPLETED" if execution.returncode == 0 else "ENGINE_FAILED")
        return ScientificEvidenceBundle(
            experiment_sha256=experiment.semantic_sha256,
            engine=self.descriptor,
            engine_run_id=f"{experiment.experiment_id}:rep{experiment.replicate_id}",
            status=status,
            metrics={
                "returncode": execution.returncode,
                "bridge_manifest_sha256": bridge_sha,
                "deme_count": int(len(experiment.arrays["component_ids"])),
                "quantitative_trait_axes": list(self.spec.quantitative_trait_axes),
                "execution_attempted": self.spec.template_path is not None,
            },
            arrays={},
            assumptions=experiment.assumptions,
            unsupported_mappings=(
                "ARCANA moment state does not uniquely determine a NEMO genome/QTL realization; executable R3.6B must use a governed ensemble mapping.",
                "NEMO output never defines ARCANA species identity or speciation events.",
            ),
            stdout_sha256=execution.stdout_sha256,
            stderr_sha256=execution.stderr_sha256,
        )
