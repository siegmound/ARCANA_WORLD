"""Resolution-relative event significance policy for R6 WORLD_HISTORY.

This module classifies an already-authorized impact assessment. It does not
predict events, infer their absence, supply physical thresholds, or authorize
time integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
import json
from typing import Any, Mapping


POLICY_ID = "R6_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY_V1"
DIMENSIONS = (
    "spatial_footprint",
    "temporal_persistence",
    "reversibility",
    "resolution_relative_magnitude",
    "cross_domain_coupling",
    "topology_impact",
    "support_membership_impact",
    "causal_downstream_relevance",
)


class AuthorityClass(str, Enum):
    SOURCE_AUTHORITY_LIMIT = "SOURCE_AUTHORITY_LIMIT"
    MODEL_AUTHORITY_LIMIT = "MODEL_AUTHORITY_LIMIT"
    PHYSICAL_EVENT_UNCERTAINTY = "PHYSICAL_EVENT_UNCERTAINTY"
    SUPPORT_TOPOLOGY_UNCERTAINTY = "SUPPORT_TOPOLOGY_UNCERTAINTY"
    NUMERICAL_RESOLUTION_LIMIT = "NUMERICAL_RESOLUTION_LIMIT"
    MECHANICS_SCOPE_LIMIT = "MECHANICS_SCOPE_LIMIT"


class AuthorityStatus(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    NOT_AUTHORIZED = "NOT_AUTHORIZED"
    UNKNOWN = "UNKNOWN"


class EventOccurrence(str, Enum):
    OCCURRED = "OCCURRED"
    UNKNOWN = "UNKNOWN"


class ImpactBoundStatus(str, Enum):
    BOUNDED = "BOUNDED"
    UNKNOWN = "UNKNOWN"
    UNBOUNDED = "UNBOUNDED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ResolutionRelation(str, Enum):
    BELOW_REPRESENTED_RESOLUTION = "BELOW_REPRESENTED_RESOLUTION"
    STATE_SIGNIFICANT_AT_REPRESENTED_RESOLUTION = "STATE_SIGNIFICANT_AT_REPRESENTED_RESOLUTION"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class PropagationScope(str, Enum):
    NONE = "NONE"
    LOCAL = "LOCAL"
    DOMAIN = "DOMAIN"
    REGIONAL = "REGIONAL"
    TOPOLOGY = "TOPOLOGY"
    SYSTEMIC = "SYSTEMIC"
    GLOBAL = "GLOBAL"


class DependencyStatus(str, Enum):
    CLOSED = "CLOSED"
    ISOLATION_PROVEN = "ISOLATION_PROVEN"
    NOT_PROVEN = "NOT_PROVEN"


class SignificanceClass(str, Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    EVENT_ONLY = "EVENT_ONLY"
    LOCAL_CHECKPOINT_REQUIRED = "LOCAL_CHECKPOINT_REQUIRED"
    REGIONAL_STATE_REQUIRED = "REGIONAL_STATE_REQUIRED"
    SYSTEMIC_STATE_REQUIRED = "SYSTEMIC_STATE_REQUIRED"
    SUBRESOLUTION_UNKNOWN = "SUBRESOLUTION_UNKNOWN"
    LOCAL_REFINEMENT_UNKNOWN = "LOCAL_REFINEMENT_UNKNOWN"
    REGIONAL_STATE_SIGNIFICANT_UNKNOWN = "REGIONAL_STATE_SIGNIFICANT_UNKNOWN"
    SYSTEMIC_STATE_SIGNIFICANT_UNKNOWN = "SYSTEMIC_STATE_SIGNIFICANT_UNKNOWN"
    INSUFFICIENT_IMPACT_BOUND = "INSUFFICIENT_IMPACT_BOUND"
    AUTHORITY_BLOCKED = "AUTHORITY_BLOCKED"


@dataclass(frozen=True, slots=True)
class EventImpactAssessment:
    subject_id: str
    subject_kind: str
    authority_class: AuthorityClass
    authority_status: AuthorityStatus
    authority_basis: str | None
    occurrence: EventOccurrence | None
    impact_bound_status: ImpactBoundStatus
    dimension_relations: Mapping[str, ResolutionRelation]
    dimension_evidence: Mapping[str, str]
    spatial_resolution: str
    temporal_resolution: str
    represented_domains: tuple[str, ...]
    requested_outputs: tuple[str, ...]
    affected_domains: tuple[str, ...]
    authority_scope: PropagationScope
    impact_scope: PropagationScope
    dependency_status: DependencyStatus
    resolution_context_id: str

    def __post_init__(self) -> None:
        if not self.subject_id or not self.subject_kind:
            raise ValueError("assessment subject identity and kind are required")
        if not self.spatial_resolution or not self.temporal_resolution or not self.resolution_context_id:
            raise ValueError("spatial, temporal, and resolution-context identities are required")
        if not self.represented_domains or not self.requested_outputs or not self.affected_domains:
            raise ValueError("represented domains, requested outputs, and affected domains must be explicit")
        relations = {str(k): ResolutionRelation(v) for k, v in self.dimension_relations.items()}
        evidence = {str(k): str(v) for k, v in self.dimension_evidence.items()}
        if set(relations) != set(DIMENSIONS) or set(evidence) != set(DIMENSIONS):
            raise ValueError("every significance dimension requires a relation and evidence")
        if any(not evidence[key].strip() for key in DIMENSIONS):
            raise ValueError("dimension evidence must not be empty")
        if self.authority_status == AuthorityStatus.AUTHORIZED and not self.authority_basis:
            raise ValueError("authorized model use must cite its governing authority")
        object.__setattr__(self, "dimension_relations", relations)
        object.__setattr__(self, "dimension_evidence", evidence)
        object.__setattr__(self, "represented_domains", tuple(sorted(set(self.represented_domains))))
        object.__setattr__(self, "requested_outputs", tuple(sorted(set(self.requested_outputs))))
        object.__setattr__(self, "affected_domains", tuple(sorted(set(self.affected_domains))))

    def to_dict(self) -> dict[str, Any]:
        return {
            "subject_id": self.subject_id,
            "subject_kind": self.subject_kind,
            "authority_class": self.authority_class.value,
            "authority_status": self.authority_status.value,
            "authority_basis": self.authority_basis,
            "event_occurrence": self.occurrence.value if self.occurrence is not None else None,
            "impact_bound_status": self.impact_bound_status.value,
            "dimension_relations": {k: self.dimension_relations[k].value for k in DIMENSIONS},
            "dimension_evidence": {k: self.dimension_evidence[k] for k in DIMENSIONS},
            "resolution_context": {
                "id": self.resolution_context_id,
                "spatial_resolution": self.spatial_resolution,
                "temporal_resolution": self.temporal_resolution,
                "represented_domains": list(self.represented_domains),
                "requested_outputs": list(self.requested_outputs),
            },
            "affected_domains": list(self.affected_domains),
            "authority_scope": self.authority_scope.value,
            "impact_scope": self.impact_scope.value,
            "dependency_status": self.dependency_status.value,
        }


def _bounded_scope(scope: PropagationScope,
                   dependencies: DependencyStatus) -> PropagationScope:
    if dependencies == DependencyStatus.NOT_PROVEN:
        return PropagationScope.GLOBAL
    return scope


def adjudicate_event_impact(assessment: EventImpactAssessment) -> dict[str, Any]:
    """Return a deterministic, resolution-scoped classification.

    ``UNKNOWN`` event occurrence is never interpreted as absence. Authority is
    checked before impact, so a subresolution physical bound cannot supply
    missing source/model permission.
    """
    relations = tuple(assessment.dimension_relations.values())
    below = all(value in {
        ResolutionRelation.BELOW_REPRESENTED_RESOLUTION,
        ResolutionRelation.NOT_APPLICABLE,
    } for value in relations)
    non_event_not_applicable = (
        assessment.occurrence is None
        and assessment.impact_bound_status == ImpactBoundStatus.NOT_APPLICABLE
        and all(value == ResolutionRelation.NOT_APPLICABLE for value in relations)
    )
    incomplete_bound = (
        (assessment.impact_bound_status != ImpactBoundStatus.BOUNDED and not non_event_not_applicable)
        or any(value == ResolutionRelation.UNKNOWN for value in relations)
        or assessment.dependency_status == DependencyStatus.NOT_PROVEN
    )

    if assessment.authority_status != AuthorityStatus.AUTHORIZED:
        significance = SignificanceClass.AUTHORITY_BLOCKED
        state_action = "NO_CROSSING_WITHOUT_AUTHORITY"
        block_scope = _bounded_scope(assessment.authority_scope, assessment.dependency_status)
    elif incomplete_bound:
        significance = SignificanceClass.INSUFFICIENT_IMPACT_BOUND
        state_action = "NO_STATE_BOUNDARY_INFERRED; RESOLVE_OR_SCOPE_THE_IMPACT"
        block_scope = _bounded_scope(assessment.impact_scope, assessment.dependency_status)
    elif non_event_not_applicable:
        significance = SignificanceClass.NOT_APPLICABLE
        state_action = "NO_EVENT_IMPACT_ADJUDICATION_FOR_UNREQUESTED_SCOPE"
        block_scope = PropagationScope.NONE
    elif below and assessment.occurrence == EventOccurrence.UNKNOWN:
        significance = SignificanceClass.SUBRESOLUTION_UNKNOWN
        state_action = "EVENT_LEDGER_OR_ADJUDICATION_EVIDENCE_ONLY; NO_STATE_OR_CHECKPOINT"
        block_scope = PropagationScope.NONE
    elif below and assessment.occurrence == EventOccurrence.OCCURRED:
        significance = SignificanceClass.EVENT_ONLY
        state_action = "EVENT_LEDGER_ONLY; NO_STATE_OR_CHECKPOINT"
        block_scope = PropagationScope.NONE
    elif assessment.occurrence == EventOccurrence.UNKNOWN:
        if assessment.impact_scope == PropagationScope.LOCAL:
            significance = SignificanceClass.LOCAL_REFINEMENT_UNKNOWN
            state_action = "LOCAL_REFINEMENT_OR_CHECKPOINT_ADJUDICATION_REQUIRED"
        elif assessment.impact_scope in {PropagationScope.SYSTEMIC, PropagationScope.GLOBAL}:
            significance = SignificanceClass.SYSTEMIC_STATE_SIGNIFICANT_UNKNOWN
            state_action = "SYSTEMIC_CAUSAL_STATE_BOUNDARY_REQUIRED_BEFORE_CROSSING"
        else:
            significance = SignificanceClass.REGIONAL_STATE_SIGNIFICANT_UNKNOWN
            state_action = "REGIONAL_OR_DOMAIN_STATE_BOUNDARY_REQUIRED_BEFORE_CROSSING"
        block_scope = _bounded_scope(assessment.impact_scope, assessment.dependency_status)
    elif assessment.impact_scope == PropagationScope.LOCAL:
        significance = SignificanceClass.LOCAL_CHECKPOINT_REQUIRED
        state_action = "LOCAL_CHECKPOINT_OR_REFINEMENT_BRANCH_REQUIRED"
        block_scope = assessment.impact_scope
    elif assessment.impact_scope in {PropagationScope.SYSTEMIC, PropagationScope.GLOBAL}:
        significance = SignificanceClass.SYSTEMIC_STATE_REQUIRED
        state_action = "SYSTEMIC_CAUSAL_STATE_BOUNDARY_REQUIRED"
        block_scope = assessment.impact_scope
    else:
        significance = SignificanceClass.REGIONAL_STATE_REQUIRED
        state_action = "REGIONAL_OR_DOMAIN_STATE_BOUNDARY_REQUIRED"
        block_scope = assessment.impact_scope

    # This is a policy classification, never an execution authorization.
    scope_isolated = assessment.dependency_status == DependencyStatus.ISOLATION_PROVEN
    can_continue_elsewhere = (
        block_scope not in {PropagationScope.NONE, PropagationScope.GLOBAL}
        and scope_isolated
        and significance in {
            SignificanceClass.LOCAL_REFINEMENT_UNKNOWN,
            SignificanceClass.REGIONAL_STATE_SIGNIFICANT_UNKNOWN,
            SignificanceClass.INSUFFICIENT_IMPACT_BOUND,
        }
    )
    result = {
        "policy_id": POLICY_ID,
        "assessment": assessment.to_dict(),
        "significance_class": significance.value,
        "state_action": state_action,
        "blocking_scope": block_scope.value,
        "current_scope_crossing_policy": (
            "NOT_APPLICABLE_TO_REQUESTED_SCOPE"
            if significance == SignificanceClass.NOT_APPLICABLE
            else "NO_STATE_BOUNDARY_REQUIRED_AT_DECLARED_RESOLUTION_IF_OTHER_AUTHORITIES_ALLOW"
            if significance in {SignificanceClass.EVENT_ONLY, SignificanceClass.SUBRESOLUTION_UNKNOWN}
            else "BLOCKED_OR_BOUNDARY_REQUIRED_FOR_AFFECTED_SCOPE"
        ),
        "unaffected_scope_isolation_proven": scope_isolated,
        "unaffected_scopes_potentially_eligible": can_continue_elsewhere,
        "event_occurrence_remains": assessment.occurrence.value if assessment.occurrence is not None else None,
        "event_absence_asserted": False,
        "policy_authorizes_propagation": False,
        "policy_authorizes_dt_selection": False,
        "policy_authorizes_state_publication": False,
    }
    result["adjudication_sha256"] = sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")).hexdigest()
    return result
