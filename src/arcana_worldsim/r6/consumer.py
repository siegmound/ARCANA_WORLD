"""Typed upstream-state requests; requests never imply a provider timestamp."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from .state import AuthorityClass, DomainStateEnvelope, SupportClass


@dataclass(frozen=True, slots=True)
class ConsumerStateRequest:
    consumer_id: str
    upstream_domains: tuple[str, ...]
    time_key: str
    region_id: str
    grid_id: str
    cell_ids: tuple[str, ...]
    variables: tuple[str, ...]
    minimum_authority: AuthorityClass
    unknown_policy: str
    minimum_resolution: str
    reason: str
    event_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name in ("consumer_id", "time_key", "region_id", "grid_id",
                     "unknown_policy", "minimum_resolution", "reason"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"consumer request {name} is required")
        for name in ("upstream_domains", "cell_ids", "variables", "event_refs"):
            value = tuple(str(item) for item in getattr(self, name))
            if name != "event_refs" and not value:
                raise ValueError(f"consumer request {name} must not be empty")
            if len(value) != len(set(value)):
                raise ValueError(f"consumer request {name} must be unique")
            object.__setattr__(self, name, value)

    def validate_inputs(self, states: Iterable[DomainStateEnvelope]) -> None:
        rows = tuple(states)
        by_domain = {row.domain: row for row in rows}
        if len(by_domain) != len(rows):
            raise ValueError("consumer request received duplicate upstream domains")
        if set(by_domain) != set(self.upstream_domains):
            raise ValueError("consumer request upstream domain set mismatch")
        for domain, state in by_domain.items():
            if state.time_support.time_key != self.time_key:
                raise ValueError(f"{domain} time does not match consumer request")
            if state.spatial_support.grid_id != self.grid_id:
                raise ValueError(f"{domain} grid does not match consumer request")
            if state.spatial_support.cell_ids != self.cell_ids:
                raise ValueError(f"{domain} cells do not match consumer request")
            native_resolution = state.spatial_support.native_resolution
            if self.minimum_resolution in {"NATIVE", "NATIVE_OR_COARSER_EXPLICIT"}:
                if not native_resolution:
                    raise ValueError(f"{domain} native spatial support is undeclared")
            elif native_resolution != self.minimum_resolution:
                raise ValueError(f"{domain} native resolution does not meet exact request")
            variables = state.value.get("variables", {}) if isinstance(state.value, Mapping) else {}
            missing_variables = set(self.variables) - set(variables)
            if missing_variables:
                raise ValueError(f"{domain} lacks requested variables: {sorted(missing_variables)}")
            if state.authority_class not in _authority_floor(self.minimum_authority):
                raise ValueError(f"{domain} authority is below request minimum")
            if state.support_class in {SupportClass.UNKNOWN, SupportClass.NOT_APPLICABLE,
                                       SupportClass.OUTSIDE_SCOPE} and self.unknown_policy == "REJECT":
                raise ValueError(f"{domain} support violates UNKNOWN policy")
            if state.support_class is SupportClass.FIXTURE_ONLY and self.unknown_policy != "ALLOW_FIXTURE":
                raise ValueError(f"{domain} fixture support is not eligible")


def _authority_floor(value: AuthorityClass) -> set[AuthorityClass]:
    order = {
        AuthorityClass.NONE: {AuthorityClass.NONE, AuthorityClass.FIXTURE_ONLY,
                              AuthorityClass.SPARSE_AUTHORITY, AuthorityClass.DERIVED_AUTHORITY,
                              AuthorityClass.DIRECT_AUTHORITY},
        AuthorityClass.SPARSE_AUTHORITY: {AuthorityClass.SPARSE_AUTHORITY,
                                          AuthorityClass.DERIVED_AUTHORITY,
                                          AuthorityClass.DIRECT_AUTHORITY},
        AuthorityClass.DERIVED_AUTHORITY: {AuthorityClass.DERIVED_AUTHORITY,
                                           AuthorityClass.DIRECT_AUTHORITY},
        AuthorityClass.DIRECT_AUTHORITY: {AuthorityClass.DIRECT_AUTHORITY},
        AuthorityClass.FIXTURE_ONLY: {AuthorityClass.FIXTURE_ONLY},
    }
    return order[value]
