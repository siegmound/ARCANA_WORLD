"""R6 INT10K E1: noncanonical short (3/10-year) direct-vs-restart reference.

This reuses existing regional/unified physics unchanged and retains all legacy
records. This is NOT a streaming runtime or 10,000-year implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from time import perf_counter
from typing import Any, Mapping

from .geological_surface_microdomain import SUPPORTS
from .regional_geological_evolution import RegionalConfig, run_regional_segment


class ShortReferenceError(ValueError):
    pass


@dataclass(frozen=True)
class ShortReferenceConfig:
    years: int
    split_at: int
    abs_tol: float = 1e-8
    rel_tol: float = 2e-14

    def validate(self) -> None:
        if type(self.years) is not int or self.years not in (3, 10):
            raise ShortReferenceError("SHORT_REFERENCE_ONLY_3_OR_10_YEARS")
        if type(self.split_at) is not int or not 0 < self.split_at < self.years:
            raise ShortReferenceError("SHORT_REFERENCE_SPLIT_OUT_OF_RANGE")
        if any(not math.isfinite(x) or x < 0 for x in (self.abs_tol, self.rel_tol)):
            raise ShortReferenceError("SHORT_REFERENCE_TOLERANCE_INVALID")


def compare_reference(left: Any, right: Any, *, path: str = "root",
                      abs_tol: float = 1e-8, rel_tol: float = 2e-14) -> None:
    """Whole-tree strict identity for metadata/events, toleranced finite numerics."""
    if isinstance(left, bool) or isinstance(right, bool):
        if type(left) is not type(right) or left != right:
            raise ShortReferenceError(f"REFERENCE_MISMATCH:{path}")
    elif isinstance(left, Mapping) and isinstance(right, Mapping):
        if left.keys() != right.keys():
            raise ShortReferenceError(f"REFERENCE_KEY_MISMATCH:{path}")
        for key in left:
            compare_reference(left[key], right[key], path=f"{path}.{key}",
                              abs_tol=abs_tol, rel_tol=rel_tol)
    elif isinstance(left, (tuple, list)) and isinstance(right, (tuple, list)):
        if len(left) != len(right):
            raise ShortReferenceError(f"REFERENCE_LENGTH_MISMATCH:{path}")
        for index, (a, b) in enumerate(zip(left, right)):
            compare_reference(a, b, path=f"{path}[{index}]",
                              abs_tol=abs_tol, rel_tol=rel_tol)
    elif isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if not (math.isfinite(left) and math.isfinite(right)):
            raise ShortReferenceError(f"REFERENCE_NONFINITE:{path}")
        if type(left) is int and type(right) is int:
            if left != right:
                raise ShortReferenceError(f"REFERENCE_INTEGER_MISMATCH:{path}")
        elif not math.isclose(left, right, abs_tol=abs_tol, rel_tol=rel_tol):
            raise ShortReferenceError(f"REFERENCE_NUMERIC_MISMATCH:{path}")
    elif type(left) is not type(right) or left != right:
        raise ShortReferenceError(f"REFERENCE_MISMATCH:{path}")


def _validate_regional_coverage(state: Mapping[str, Any], years: int) -> None:
    """Require annual records and snapshots including the initial year-zero state."""
    if type(state.get("time_years")) is not int or state["time_years"] != years:
        raise ShortReferenceError("SHORT_REFERENCE_COVERAGE_INVALID")

    def sequence(rows: Any) -> list[int]:
        if not isinstance(rows, (list, tuple)):
            raise ShortReferenceError("SHORT_REFERENCE_COVERAGE_INVALID")
        values: list[int] = []
        for row in rows:
            if not isinstance(row, Mapping) or type(row.get("time_year")) is not int:
                raise ShortReferenceError("SHORT_REFERENCE_COVERAGE_INVALID")
            values.append(row["time_year"])
        return values

    expected_records = list(range(1, years + 1))
    expected_snapshots = list(range(0, years + 1))
    if (sequence(state.get("records")) != expected_records or
            sequence(state.get("snapshots")) != expected_snapshots):
        raise ShortReferenceError("SHORT_REFERENCE_COVERAGE_INVALID")


def run_short_reference(states_by_support: Mapping[str, Any],
                        source_identity: Mapping[str, Any], *,
                        config: ShortReferenceConfig,
                        regional_config: RegionalConfig | None = None
                        ) -> dict[str, Any]:
    """Run fixed-plan direct and split; fail closed on any compared difference."""
    config.validate()
    if set(states_by_support) != set(SUPPORTS) or not source_identity:
        raise ShortReferenceError("SHORT_REFERENCE_INPUT_IDENTITY_INVALID")
    regional = regional_config or RegionalConfig(duration_years=config.years)
    if regional.duration_years != config.years:
        raise ShortReferenceError("SHORT_REFERENCE_PLANNED_DURATION_MISMATCH")
    regional.validate()

    start = perf_counter()
    direct = run_regional_segment(states_by_support, source_identity,
                                  config=regional, segment_years=config.years)
    direct_s = perf_counter() - start

    start = perf_counter()
    first = run_regional_segment(states_by_support, source_identity,
                                 config=regional, segment_years=config.split_at)
    split = run_regional_segment(states_by_support, source_identity,
                                 config=regional, segment_years=config.years-config.split_at,
                                 checkpoint=first["checkpoint"])
    split_s = perf_counter() - start

    direct_ref = {
        "regional_state": direct["state"],
        "subsurface_final": direct["subsurface_unified_result"]["final"],
        "domain_balances": direct["balances"],
    }
    split_ref = {
        "regional_state": split["state"],
        "subsurface_final": split["subsurface_unified_result"]["final"],
        "domain_balances": split["balances"],
    }
    compare_reference(direct_ref, split_ref,
                      abs_tol=config.abs_tol, rel_tol=config.rel_tol)
    for value in (direct_ref, split_ref):
        _validate_regional_coverage(value["regional_state"], config.years)

    return {
        "schema": "ARCANA_R6_INT10K_SHORT_REFERENCE_V1",
        "status": "PASS_SHORT_REFERENCE_IN_MEMORY_PARITY",
        "authority": "NONCANONICAL_SYNTHETIC_ENGINEERING_ONLY",
        "years": config.years,
        "split_at": config.split_at,
        "numeric_tolerance": {"abs": config.abs_tol, "rel": config.rel_tol},
        "wall_seconds": {"direct": direct_s, "split": split_s},
        "direct": direct_ref,
        "split": split_ref,
        "limitations": [
            "Existing full-history legacy checkpoint; NOT compact streaming.",
            "Only 3/10 simulated years; NOT a 10000-year benchmark.",
            "No surface-to-subsurface or Deep energy feedback.",
        ],
    }
