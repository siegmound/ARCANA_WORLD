"""Explicit authorially ratified annual forcing for the REC1 synthetic lane."""
from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from .geological_surface_microdomain import SUPPORTS


@dataclass(frozen=True)
class AnnualUpliftPlan:
    planned_years: int
    annual_by_support: Mapping[str, float]

    def __post_init__(self):
        if type(self.planned_years) is not int or self.planned_years < 1:
            raise ValueError("PLAN_HORIZON_INVALID")
        if set(self.annual_by_support) != set(SUPPORTS):
            raise ValueError("PLAN_SUPPORT_MAPPING_INVALID")
        values = {}
        for support, expected in zip(SUPPORTS, (0.0001, 0.0)):
            value = self.annual_by_support[support]
            if type(value) not in (int, float) or not math.isfinite(value) or value != expected:
                raise ValueError("PLAN_UNRATIFIED_ANNUAL_UPLIFT")
            values[support] = float(value)
        object.__setattr__(self, "annual_by_support", MappingProxyType(values))

    def totals_by_support(self):
        return {s: self.annual_by_support[s] * self.planned_years for s in SUPPORTS}

    def to_dict(self):
        return {"schema": "ARCANA_R6_ANNUAL_UPLIFT_PLAN_REC1_V1",
                "decision_id": "R6_INT10K_KEEP_1000Y_ANNUAL_UPLIFT",
                "planned_years": self.planned_years, "external_step_years": 1,
                "annual_uplift_m_by_support": dict(self.annual_by_support),
                "total_uplift_m_by_support": self.totals_by_support()}
