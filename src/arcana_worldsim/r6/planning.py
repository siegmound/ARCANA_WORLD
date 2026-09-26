"""Executable, non-scientific registries and deterministic causal-cone planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable


class Availability(str, Enum):
    SOFTWARE_INTERFACE_ONLY = "SOFTWARE_INTERFACE_ONLY"
    NOT_MATERIALIZED = "NOT_MATERIALIZED"
    UNKNOWN = "UNKNOWN"


class BindingStatus(str, Enum):
    NOT_REGISTERED = "NOT_REGISTERED"
    ADAPTER_PRESENT_UNBOUND = "ADAPTER_PRESENT_UNBOUND"
    IMPORT_BOUNDARY_ONLY = "IMPORT_BOUNDARY_ONLY"
    INTERFACE_FROZEN_INPUT_GAPS = "INTERFACE_FROZEN_INPUT_GAPS"
    CANDIDATE_NOT_AUTHORIZED = "CANDIDATE_NOT_AUTHORIZED"


class RetentionClass(str, Enum):
    RETAIN_ALWAYS = "RETAIN_ALWAYS"
    RETAIN_EVENT = "RETAIN_EVENT"
    RETAIN_CHECKPOINT = "RETAIN_CHECKPOINT"
    RETAIN_QUERY_VIEW = "RETAIN_QUERY_VIEW"
    RECOMPUTABLE = "RECOMPUTABLE"
    EPHEMERAL = "EPHEMERAL"


class DependencyKind(str, Enum):
    REQUIRED = "REQUIRED"
    CONDITIONAL = "CONDITIONAL"


class FeedbackTiming(str, Enum):
    NONE = "NONE"
    WITHIN_STEP = "WITHIN_STEP"
    INTER_STEP = "INTER_STEP"
    SLOW_STATE = "SLOW_STATE"
    UNRESOLVED_LAW_DECLARED = "UNRESOLVED_LAW_DECLARED"


@dataclass(frozen=True, slots=True)
class DomainDescriptor:
    domain_id: str
    history_id: str
    dependencies: tuple[str, ...]
    history_availability: Availability
    engine_binding_status: BindingStatus
    authority_status: str
    query_available: bool
    refinement_eligible: bool


@dataclass(frozen=True, slots=True)
class DependencyEdge:
    prerequisite: str
    consumer: str
    kind: DependencyKind = DependencyKind.REQUIRED
    feedback_timing: FeedbackTiming = FeedbackTiming.NONE
    condition: str | None = None


class DomainRegistry:
    """Read-only lookup facade over the versioned architecture descriptors."""

    def __init__(self, descriptors: Iterable[DomainDescriptor] = ()):
        rows = tuple(descriptors) or DOMAIN_REGISTRY
        self._by_id = {row.domain_id: row for row in rows}
        if len(self._by_id) != len(rows):
            raise ValueError("domain identifiers must be unique")

    def get(self, domain_id: str) -> DomainDescriptor:
        try:
            return self._by_id[domain_id]
        except KeyError as exc:
            raise KeyError(f"unknown R6 domain: {domain_id}") from exc

    def all(self) -> tuple[DomainDescriptor, ...]:
        return tuple(self._by_id[key] for key in sorted(self._by_id))


def _domain(domain_id: str, *, dependencies: tuple[str, ...] = (),
            binding: BindingStatus = BindingStatus.NOT_REGISTERED,
            availability: Availability = Availability.NOT_MATERIALIZED) -> DomainDescriptor:
    history_ids = {
        "physical_world": "PHYSICAL_HISTORY", "climate": "CLIMATE_HISTORY",
        "hydrology_freshwater": "HYDROLOGY_HISTORY",
        "parent_material_soil": "PARENT_MATERIAL_HISTORY+SOIL_HISTORY",
        "deep": "DEEP_HISTORY", "flora": "FLORA_HISTORY", "fauna": "FAUNA_HISTORY",
        "aquatic_ecology": "FRESHWATER_ECOLOGY_HISTORY+MARINE_ECOLOGY_HISTORY",
        "resources": "RESOURCE_HISTORY", "human_demography": "HUMAN_HISTORY",
        "settlement_trade": "SETTLEMENT_HISTORY+TRADE_HISTORY",
        "technology_infrastructure": "TECHNOLOGY_HISTORY+INFRASTRUCTURE_HISTORY",
        "polity_conflict_civilization": "POLITY_HISTORY+CONFLICT_HISTORY+CIVILIZATION_HISTORY",
    }
    return DomainDescriptor(domain_id, history_ids[domain_id], dependencies,
                            availability, binding,
                            "SCIENTIFIC_AUTHORITY_NOT_BOUND", True, False)


DOMAIN_REGISTRY: tuple[DomainDescriptor, ...] = (
    _domain("physical_world", binding=BindingStatus.CANDIDATE_NOT_AUTHORIZED),
    _domain("climate", dependencies=("physical_world",),
            binding=BindingStatus.ADAPTER_PRESENT_UNBOUND),
    _domain("hydrology_freshwater", dependencies=("physical_world", "climate"),
            binding=BindingStatus.IMPORT_BOUNDARY_ONLY),
    _domain("parent_material_soil", dependencies=("climate", "hydrology_freshwater")),
    _domain("deep"),
    _domain("flora", dependencies=("climate", "hydrology_freshwater", "parent_material_soil"),
            binding=BindingStatus.INTERFACE_FROZEN_INPUT_GAPS),
    _domain("fauna", dependencies=("flora",)),
    _domain("aquatic_ecology", dependencies=("hydrology_freshwater", "physical_world", "climate")),
    _domain("resources", dependencies=("physical_world", "flora", "fauna", "aquatic_ecology")),
    _domain("human_demography", dependencies=("resources", "deep", "settlement_trade")),
    _domain("settlement_trade", dependencies=("resources", "human_demography", "technology_infrastructure")),
    _domain("technology_infrastructure", dependencies=("settlement_trade",)),
    _domain("polity_conflict_civilization", dependencies=("human_demography", "settlement_trade")),
)

_DOMAIN_IDS = frozenset(item.domain_id for item in DOMAIN_REGISTRY)
DOMAIN_REGISTRY_SERVICE = DomainRegistry(DOMAIN_REGISTRY)

RECORD_RETENTION: dict[str, RetentionClass] = {
    "canonical_state": RetentionClass.RETAIN_ALWAYS,
    "event": RetentionClass.RETAIN_EVENT,
    "provenance": RetentionClass.RETAIN_ALWAYS,
    "authority_input": RetentionClass.RETAIN_ALWAYS,
    "checkpoint": RetentionClass.RETAIN_CHECKPOINT,
    "query_view": RetentionClass.RETAIN_QUERY_VIEW,
    "derived_cache": RetentionClass.RECOMPUTABLE,
    "temporary_work": RetentionClass.EPHEMERAL,
}

# Edges point from prerequisite to consumer. Feedback is explicit and conditional;
# it is never flattened into an invented scientific law or a single linear DAG.
DEPENDENCY_EDGES: tuple[DependencyEdge, ...] = (
    DependencyEdge("physical_world", "climate"),
    DependencyEdge("physical_world", "hydrology_freshwater"),
    DependencyEdge("physical_world", "resources"),
    DependencyEdge("climate", "hydrology_freshwater"),
    DependencyEdge("hydrology_freshwater", "climate", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("climate", "parent_material_soil"),
    DependencyEdge("hydrology_freshwater", "parent_material_soil"),
    DependencyEdge("parent_material_soil", "flora"),
    DependencyEdge("climate", "flora"),
    DependencyEdge("hydrology_freshwater", "flora"),
    DependencyEdge("flora", "fauna", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("fauna", "flora", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("deep", "flora", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared"),
    DependencyEdge("deep", "fauna", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared"),
    DependencyEdge("flora", "resources"),
    DependencyEdge("fauna", "resources"),
    DependencyEdge("hydrology_freshwater", "aquatic_ecology"),
    DependencyEdge("physical_world", "aquatic_ecology"),
    DependencyEdge("climate", "aquatic_ecology"),
    DependencyEdge("resources", "human_demography", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("deep", "human_demography", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("human_demography", "resources", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_delayed_or_slow_state"),
    DependencyEdge("technology_infrastructure", "resources", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_accessibility_effect"),
    DependencyEdge("resources", "settlement_trade"),
    DependencyEdge("human_demography", "settlement_trade"),
    DependencyEdge("settlement_trade", "human_demography", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("technology_infrastructure", "settlement_trade", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_accessibility_effect"),
    DependencyEdge("settlement_trade", "technology_infrastructure", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_delayed_or_slow_state"),
    DependencyEdge("human_demography", "polity_conflict_civilization"),
    DependencyEdge("settlement_trade", "polity_conflict_civilization"),
    DependencyEdge("polity_conflict_civilization", "human_demography", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_same_step_or_delayed"),
    DependencyEdge("polity_conflict_civilization", "resources", DependencyKind.CONDITIONAL,
                   FeedbackTiming.UNRESOLVED_LAW_DECLARED, "law_declared_delayed_or_slow_state"),
)

for _edge in DEPENDENCY_EDGES:
    if _edge.prerequisite not in _DOMAIN_IDS or _edge.consumer not in _DOMAIN_IDS:
        raise RuntimeError(f"dependency edge references unknown domain: {_edge}")


@dataclass(frozen=True, slots=True)
class EngineRole:
    engine_id: str
    role: str
    status: str
    scientific_authority: str = "ARCANA"
    capabilities: tuple[str, ...] = ()


ENGINE_ROLE_REGISTRY: tuple[EngineRole, ...] = (
    EngineRole("ARCANA", "scientific semantics, authority and canonicalization",
               "AUTHORITATIVE"),
    EngineRole("pyGPlates", "bounded geometry/topology/deformation solver",
               "CANDIDATE_NOT_BOUND", capabilities=("STATIC_GEOMETRY_TOPOLOGY_SUFFICIENT",
                                                       "SYNTHETIC_DEFORMING_NETWORK_SUFFICIENT",
                                                       "CANONICAL_DYNAMIC_DEFORMATION_NOT_YET_VALIDATED")),
    EngineRole("BIOME4", "bounded vegetation/productivity calculation",
               "INTERFACE_FROZEN_INPUT_GAPS_PRODUCTION_UNAUTHORIZED"),
    EngineRole("RangeShiftR", "bounded external calculation", "NOT_BOUND"),
    EngineRole("NEMO", "bounded external calculation", "NOT_BOUND"),
    EngineRole("SLiM", "bounded external calculation", "NOT_BOUND"),
    EngineRole("CDMetaPOP", "bounded external calculation", "NOT_BOUND"),
)

if any(item.scientific_authority != "ARCANA" for item in ENGINE_ROLE_REGISTRY):
    raise RuntimeError("external engines must not acquire scientific authority")


@dataclass(frozen=True, slots=True)
class CausalCone:
    requested_domains: tuple[str, ...]
    required_domains: tuple[str, ...]
    included_edges: tuple[DependencyEdge, ...]
    feedback_groups: tuple[tuple[str, ...], ...]
    region: str | None
    time_interval: tuple[str, str] | None
    refinement_mode: str

    def to_dict(self) -> dict[str, object]:
        return {
            "requested_domains": list(self.requested_domains),
            "required_domains": list(self.required_domains),
            "included_edges": [
                {"prerequisite": edge.prerequisite, "consumer": edge.consumer,
                 "kind": edge.kind.value, "feedback_timing": edge.feedback_timing.value,
                 "condition": edge.condition}
                for edge in self.included_edges
            ],
            "feedback_groups": [list(group) for group in self.feedback_groups],
            "region": self.region,
            "time_interval": list(self.time_interval) if self.time_interval else None,
            "refinement_mode": self.refinement_mode,
            "scientific_execution": False,
        }


def _strong_components(nodes: set[str], edges: Iterable[DependencyEdge]) -> tuple[tuple[str, ...], ...]:
    edges = tuple(edges)
    adjacency = {node: [] for node in nodes}
    for edge in edges:
        if edge.prerequisite in nodes and edge.consumer in nodes:
            adjacency[edge.prerequisite].append(edge.consumer)
    for targets in adjacency.values():
        targets.sort()
    index = 0
    indices: dict[str, int] = {}
    lowlinks: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    groups: list[tuple[str, ...]] = []

    def visit(node: str) -> None:
        nonlocal index
        indices[node] = lowlinks[node] = index
        index += 1
        stack.append(node)
        on_stack.add(node)
        for target in adjacency[node]:
            if target not in indices:
                visit(target)
                lowlinks[node] = min(lowlinks[node], lowlinks[target])
            elif target in on_stack:
                lowlinks[node] = min(lowlinks[node], indices[target])
        if lowlinks[node] == indices[node]:
            component: list[str] = []
            while True:
                target = stack.pop()
                on_stack.remove(target)
                component.append(target)
                if target == node:
                    break
            if len(component) > 1 or any(edge.prerequisite == node and edge.consumer == node for edge in edges):
                groups.append(tuple(sorted(component)))

    for node in sorted(nodes):
        if node not in indices:
            visit(node)
    return tuple(sorted(groups))


def required_dependencies(requested_domains: Iterable[str], *, region: str | None = None,
                          time_interval: tuple[str, str] | None = None,
                          refinement_mode: str = "GLOBAL_BASE_HISTORY",
                          include_conditional: bool = True) -> CausalCone:
    """Return deterministic transitive dependencies without executing any science.

    Region and interval are retained as query scope. No resolution or authority
    pruning is inferred because those support contracts are not bound here.
    Cycles are returned as feedback groups, not linearized.
    """
    requested = tuple(sorted(set(str(item) for item in requested_domains)))
    if not requested:
        raise ValueError("at least one requested domain is required")
    unknown = set(requested) - _DOMAIN_IDS
    if unknown:
        raise ValueError(f"unknown R6 domains: {sorted(unknown)}")
    if time_interval is not None and (len(time_interval) != 2 or not all(time_interval)):
        raise ValueError("time interval must contain two nonempty support keys")
    active_edges = tuple(edge for edge in DEPENDENCY_EDGES
                         if include_conditional or edge.kind is DependencyKind.REQUIRED)
    needed = set(requested)
    changed = True
    while changed:
        changed = False
        for edge in active_edges:
            if edge.consumer in needed and edge.prerequisite not in needed:
                needed.add(edge.prerequisite)
                changed = True
    included = tuple(sorted((edge for edge in active_edges
                             if edge.prerequisite in needed and edge.consumer in needed),
                            key=lambda item: (item.prerequisite, item.consumer,
                                             item.kind.value, item.feedback_timing.value,
                                             item.condition or "")))
    return CausalCone(requested, tuple(sorted(needed)), included,
                      _strong_components(needed, included), region, time_interval,
                      refinement_mode)
