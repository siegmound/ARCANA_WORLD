"""Generic minimal-state retention and extraction validation for R6."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping, Protocol

from .identity import content_hash
from .state import DomainStateEnvelope


class RetentionAction(str, Enum):
    MATERIALIZE = "MATERIALIZE"
    DERIVE = "DERIVE"
    REFINE = "REFINE"
    STATIC = "STATIC"
    FORCING = "FORCING"
    DISCARD = "DISCARD"


class InformationRole(str, Enum):
    SYSTEM_MEMORY = "SYSTEM_MEMORY"
    QUERY_OUTPUT = "QUERY_OUTPUT"
    INPUT = "INPUT"
    DIAGNOSTIC = "DIAGNOSTIC"
    INTERMEDIATE = "INTERMEDIATE"


@dataclass(frozen=True, slots=True)
class RetentionItem:
    item_id: str
    action: RetentionAction
    role: InformationRole
    required: bool = True
    reconstruction_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.item_id or len(self.item_id) > 256:
            raise ValueError("retention item identity is required and bounded")
        object.__setattr__(self, "reconstruction_refs", tuple(self.reconstruction_refs))
        if len(self.reconstruction_refs) != len(set(self.reconstruction_refs)):
            raise ValueError("duplicate reconstruction reference")


@dataclass(frozen=True, slots=True)
class MinimalStateContract:
    producer_adapter_id: str
    items: tuple[RetentionItem, ...]
    contract_id: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "items", tuple(self.items))
        if not self.producer_adapter_id or not self.items:
            raise ValueError("adapter identity and retention items are required")
        ids = [item.item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate/conflicting retention classification")
        for item in self.items:
            if item.role is InformationRole.SYSTEM_MEMORY and item.action is RetentionAction.DISCARD:
                raise ValueError(f"required future system memory cannot be discarded: {item.item_id}")
            if item.action in {RetentionAction.DERIVE, RetentionAction.REFINE}:
                if not item.reconstruction_refs:
                    raise ValueError(f"{item.action.value} item lacks reconstruction references: {item.item_id}")
                if not any(ref.startswith(("recipe:", "parent:", "forcing:", "static:", "adapter:"))
                           for ref in item.reconstruction_refs):
                    raise ValueError(f"{item.action.value} item has no reconstructability anchor: {item.item_id}")
            if item.action is RetentionAction.STATIC and not any(
                    ref.startswith(("static:", "provider:")) for ref in item.reconstruction_refs):
                raise ValueError(f"STATIC item lacks authority reference: {item.item_id}")
            if item.action is RetentionAction.FORCING and not any(
                    ref.startswith("forcing:") for ref in item.reconstruction_refs):
                raise ValueError(f"FORCING item lacks forcing identity: {item.item_id}")
        payload = {"producer_adapter_id": self.producer_adapter_id,
                   "items": [{"item_id": i.item_id, "action": i.action.value,
                              "role": i.role.value, "required": i.required,
                              "reconstruction_refs": list(i.reconstruction_refs)} for i in self.items]}
        expected = "r6ret_" + content_hash(payload)
        if self.contract_id and self.contract_id != expected:
            raise ValueError("retention contract identity does not match content")
        object.__setattr__(self, "contract_id", expected)


@dataclass(frozen=True, slots=True)
class MinimalStateExtractionResult:
    contract_id: str
    materialized: Mapping[str, tuple[DomainStateEnvelope, ...]]
    forcing_identities: tuple[str, ...] = ()
    static_identities: tuple[str, ...] = ()
    reconstruction_identities: tuple[str, ...] = ()
    omitted_item_ids: tuple[str, ...] = ()
    validation_status: str = "UNVALIDATED"
    validation_errors: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        normalized = {str(key): tuple(value) for key, value in self.materialized.items()}
        object.__setattr__(self, "materialized", normalized)
        object.__setattr__(self, "forcing_identities", tuple(self.forcing_identities))
        object.__setattr__(self, "static_identities", tuple(self.static_identities))
        object.__setattr__(self, "reconstruction_identities", tuple(self.reconstruction_identities))
        object.__setattr__(self, "omitted_item_ids", tuple(self.omitted_item_ids))
        object.__setattr__(self, "validation_errors", tuple(self.validation_errors))

    @property
    def materialized_state_ids(self) -> tuple[str, ...]:
        return tuple(sorted(str(record.state_id) for records in self.materialized.values()
                            for record in records))


class DomainExtractor(Protocol):
    """Domain-specific code selects fields; core only validates its declaration."""

    adapter_id: str

    def extract(self, raw_output: Mapping[str, Any], contract: MinimalStateContract
                ) -> MinimalStateExtractionResult: ...


def validate_extraction(contract: MinimalStateContract, result: MinimalStateExtractionResult,
                        *, history_id: str | None = None, branch_id: str | None = None
                        ) -> MinimalStateExtractionResult:
    errors: list[str] = []
    if result.contract_id != contract.contract_id:
        errors.append("contract identity mismatch")
    declared = {item.item_id: item for item in contract.items}
    if set(result.materialized) - set(declared):
        errors.append("extraction materializes undeclared item")
    if set(result.omitted_item_ids) - set(declared):
        errors.append("extraction omits undeclared item")
    for item_id, records in result.materialized.items():
        if declared.get(item_id) and declared[item_id].action is not RetentionAction.MATERIALIZE:
            errors.append(f"non-MATERIALIZE item emitted as persistent state: {item_id}")
        if not records:
            errors.append(f"materialized item has no persistent record: {item_id}")
        for record in records:
            if history_id is not None and record.history_id != history_id:
                errors.append(f"history scope mismatch: {item_id}")
            if branch_id is not None and record.branch_id != branch_id:
                errors.append(f"branch scope mismatch: {item_id}")
    for item in contract.items:
        emitted = item.item_id in result.materialized
        omitted = item.item_id in result.omitted_item_ids
        if emitted and omitted:
            errors.append(f"item both materialized and omitted: {item.item_id}")
        if item.action is RetentionAction.MATERIALIZE and item.required and not emitted:
            errors.append(f"required persistent state missing: {item.item_id}")
        if item.action is not RetentionAction.MATERIALIZE and item.required and not omitted:
            errors.append(f"required non-materialized decision missing: {item.item_id}")
        if item.action is RetentionAction.FORCING:
            needed = {ref.removeprefix("forcing:") for ref in item.reconstruction_refs
                      if ref.startswith("forcing:")}
            if not needed.issubset(result.forcing_identities):
                errors.append(f"forcing dependency missing: {item.item_id}")
        if item.action is RetentionAction.STATIC:
            needed = {ref.removeprefix("static:") for ref in item.reconstruction_refs
                      if ref.startswith("static:")}
            if not needed.issubset(result.static_identities):
                errors.append(f"static authority reference missing: {item.item_id}")
        if item.action in {RetentionAction.DERIVE, RetentionAction.REFINE}:
            refs = item.reconstruction_refs
            for prefix, available in (("forcing:", result.forcing_identities),
                                      ("static:", result.static_identities)):
                required = {ref.removeprefix(prefix) for ref in refs if ref.startswith(prefix)}
                if not required.issubset(available):
                    errors.append(f"reconstruction dependency missing for {item.item_id}: {prefix}")
            for prefix in ("recipe:", "refinement:", "provider:"):
                required = {ref for ref in refs if ref.startswith(prefix)}
                if not required.issubset(result.reconstruction_identities):
                    errors.append(f"reconstruction identity missing for {item.item_id}: {prefix}")
            for ref in (ref for ref in refs if ref.startswith("parent:")):
                parent_item = ref.removeprefix("parent:")
                if parent_item not in result.materialized:
                    errors.append(f"retained parent state missing for {item.item_id}: {ref}")
            for ref in (ref for ref in refs if ref.startswith("adapter:")):
                if ref != f"adapter:{contract.producer_adapter_id}":
                    errors.append(f"adapter identity mismatch for {item.item_id}")
    return MinimalStateExtractionResult(
        result.contract_id, result.materialized, result.forcing_identities,
        result.static_identities, result.reconstruction_identities, result.omitted_item_ids,
        "PASS" if not errors else "FAIL", tuple(errors))


def extract_minimal_state(raw_output: Mapping[str, Any], contract: MinimalStateContract,
                          adapter: DomainExtractor, *, history_id: str | None = None,
                          branch_id: str | None = None) -> MinimalStateExtractionResult:
    if adapter.adapter_id != contract.producer_adapter_id:
        raise ValueError("extractor adapter identity does not match contract")
    return validate_extraction(contract, adapter.extract(raw_output, contract),
                                history_id=history_id, branch_id=branch_id)
