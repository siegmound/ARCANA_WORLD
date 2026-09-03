from __future__ import annotations

from .contracts import EngineDescriptor, EngineRole


NEMO_242 = EngineDescriptor(
    name="NEMO", version="2.4.2", role=EngineRole.REFERENCE_ORACLE,
    execution_mode="EXTERNAL_EXECUTABLE_SIDECAR", license_id="GPL-3.0-or-later",
    notes=("Quantitative-genetics/metapopulation independent reference", "Do not use NEMO 2.4.0/2.4.1 for quant free-recombination benchmarks"),
)

MADINGLEY = EngineDescriptor(
    name="Madingley", version="external-pinned-at-run", role=EngineRole.CALIBRATED_PROVIDER_CANDIDATE,
    execution_mode="R_OR_CPP_SIDECAR", license_id=None,
    notes=("Ecosystem/trophic opportunity provider candidate", "Never owns ARCANA species identity"),
)

GEONOMICS = EngineDescriptor(
    name="Geonomics", version="1.4.9", role=EngineRole.REGIONAL_BACKEND_CANDIDATE,
    execution_mode="ISOLATED_PYTHON_ENV", license_id="MIT",
    notes=("Regional individual/genomic spatial backend candidate", "Preferred for later high-resolution windows, not global deep-time authority"),
)

CDMETAPOP = EngineDescriptor(
    name="CDMetaPOP", version="3.08-reference", role=EngineRole.SECONDARY_ORACLE,
    execution_mode="ISOLATED_PYTHON_ENV_SIDECAR", license_id=None,
    notes=("Spatial demogenetic multispecies secondary oracle",),
)

RANGESHIFTER = EngineDescriptor(
    name="RangeShifter", version="3.0-reference", role=EngineRole.SPECIALIST_BACKEND_CANDIDATE,
    execution_mode="BATCH_OR_R_SIDECAR", license_id=None,
    notes=("Detailed dispersal/range-dynamics specialist", "Not a replacement for WorldSim multispecies authority"),
)

ENGINE_REGISTRY = {x.name: x for x in (NEMO_242, MADINGLEY, GEONOMICS, CDMETAPOP, RANGESHIFTER)}
