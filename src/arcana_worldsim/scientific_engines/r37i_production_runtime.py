from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import hashlib
import json
import math

from .r37h_closed_loop_binding import (
    BRANCH_K,
    R37HClosedLoopConfig,
    run_closed_loop_branch,
)

STAGE = "v0.6D1-R3.7I"
PARENT_STAGE = "v0.6D1-R3.7H"
NOMINAL_K_LABEL = "K_CENTER"
NOMINAL_K_REFERENCE = BRANCH_K[NOMINAL_K_LABEL]
SEAL_SCHEMA = "ARCANA_R37I_PRODUCTION_PROMOTION_SEAL_V1"


@dataclass(frozen=True)
class R37IProductionConfig:
    """Canonical production wrapper, enabled only by a valid R3.7I seal.

    The nominal K value is an operational reduced-order coordinate reference,
    not a promoted physical World-1 constant.  LOW/HIGH remain mandatory
    validation sentinels at release gates.
    """

    start_age_ma: float = 210.0
    end_age_ma: float = 150.0
    diagnostic_smoke: bool = False
    nominal_k_reference: float = NOMINAL_K_REFERENCE

    def __post_init__(self) -> None:
        if abs(self.start_age_ma - 210.0) > 1e-12:
            raise ValueError("R3.7I canonical production runtime starts at 210 Ma")
        if self.diagnostic_smoke:
            if not (150.0 < self.end_age_ma < 210.0):
                raise ValueError("diagnostic smoke must stay inside 210->150 Ma")
        elif abs(self.end_age_ma - 150.0) > 1e-12:
            raise ValueError("governed canonical validation window is 210->150 Ma")
        if abs(float(self.nominal_k_reference) - NOMINAL_K_REFERENCE) > 1e-12:
            raise ValueError("R3.7I nominal reduced-order K reference is sealed to K_CENTER")


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_promotion_seal(seal_path: Path) -> dict[str, Any]:
    if not seal_path.exists():
        raise RuntimeError("R3.7I production promotion seal is missing")
    seal = json.loads(seal_path.read_text(encoding="utf-8"))
    if seal.get("schema") != SEAL_SCHEMA or seal.get("stage") != STAGE:
        raise RuntimeError("invalid R3.7I seal schema/stage")
    if seal.get("status") != "PASS_PRODUCTION_PROMOTION_SEAL":
        raise RuntimeError("R3.7I promotion seal is not PASS")
    auth = seal.get("authority", {})
    required_true = (
        "canonical_runtime_binding_authorized",
        "segregation_aware_gene_flow_variance_authorized",
        "segregation_aware_coalescence_pooling_authorized",
        "nominal_reduced_order_k_reference_authorized",
    )
    if not all(auth.get(k) is True for k in required_true):
        raise RuntimeError("R3.7I seal does not authorize all required runtime bindings")
    if auth.get("scalar_k_physical_constant_authorized") is not False:
        raise RuntimeError("R3.7I must not promote K as a physical constant")
    if auth.get("mu_b_or_ceiling_change_authorized") is not False:
        raise RuntimeError("R3.7I must not authorize mu/b/ceiling changes")
    ref = seal.get("nominal_reduced_order_reference", {})
    if ref.get("label") != NOMINAL_K_LABEL or abs(float(ref.get("K_eff")) - NOMINAL_K_REFERENCE) > 1e-12:
        raise RuntimeError("R3.7I seal nominal K reference mismatch")
    evidence = seal.get("r37h_full_closed_loop_evidence", {})
    if evidence.get("governed_closed_loop_pass") is not True:
        raise RuntimeError("R3.7H full closed-loop evidence was not sealed as PASS")
    return seal


def run_canonical_production(common, a1, metadata_rows, cfg: R37IProductionConfig, seal_path: Path) -> dict[str, Any]:
    seal = validate_promotion_seal(Path(seal_path))
    hcfg = R37HClosedLoopConfig(
        start_age_ma=cfg.start_age_ma,
        end_age_ma=cfg.end_age_ma,
        diagnostic_smoke=cfg.diagnostic_smoke,
        branch_label=NOMINAL_K_LABEL,
        adaptive_k_eff=NOMINAL_K_REFERENCE,
    )
    out = run_closed_loop_branch(common, a1, metadata_rows, hcfg)
    if not out.get("closed_loop_gate_pass", False):
        raise RuntimeError("sealed R3.7I canonical runtime failed closed-loop gate")
    promoted = dict(out)
    promoted.update({
        "schema": "ARCANA_R37I_CANONICAL_SEGREGATION_AWARE_RUNTIME_V1",
        "stage": STAGE,
        "parent_stage": PARENT_STAGE,
        "canonical_runtime_binding": True,
        "promotion_seal_sha256": _sha256(Path(seal_path)),
        "promotion_seal_status": seal["status"],
        "nominal_reduced_order_reference": {
            "label": NOMINAL_K_LABEL,
            "K_eff": NOMINAL_K_REFERENCE,
            "semantic_role": "OPERATIONAL_REDUCED_ORDER_COORDINATE_REFERENCE_NOT_PHYSICAL_CONSTANT",
        },
        "governance": {
            "production_runtime_replacement_authorized": True,
            "segregation_aware_gene_flow_variance_authorized": True,
            "segregation_aware_coalescence_pooling_authorized": True,
            "nominal_reduced_order_k_reference_authorized": True,
            "scalar_k_physical_constant_authorized": False,
            "k_low_high_release_sentinels_retained": True,
            "mu_b_or_ceiling_change_authorized": False,
        },
    })
    return promoted
