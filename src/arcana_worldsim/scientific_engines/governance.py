from __future__ import annotations

from typing import Any, Mapping, Sequence
from .contracts import CalibrationCandidate, ScientificEvidenceBundle


class CanonicalWriteDenied(RuntimeError):
    pass


def deny_direct_canonical_write(*_args, **_kwargs) -> None:
    raise CanonicalWriteDenied(
        "External scientific-engine output is evidence only. Create a reviewed CalibrationCandidate; "
        "canonical WorldSim state may only be changed by an ARCANA-governed stage."
    )


def calibration_candidate(
    candidate_id: str,
    evidence: Sequence[ScientificEvidenceBundle],
    proposed_change: Mapping[str, Any],
    rationale: str,
) -> CalibrationCandidate:
    if not evidence:
        raise ValueError("At least one evidence bundle is required")
    return CalibrationCandidate(
        candidate_id=candidate_id,
        evidence_sha256=tuple(e.semantic_sha256 for e in evidence),
        proposed_change=proposed_change,
        rationale=rationale,
    )
