"""Small, storage-neutral R6 historical-state core.

This package provides records and fixture adapters only. It does not execute
scientific models, acquire providers, or depend on R5 world-state paths.
"""

from .identity import (
    BranchId, CheckpointId, DomainStateId, EventId, HistoryId, ProviderBindingId,
    ProvenanceRecordId, R6RunId,
)
from .state import (
    AuthorityClass, DomainStateEnvelope, SpatialSupport, SupportClass, TimeSupport,
)

__all__ = [
    "AuthorityClass", "BranchId", "CheckpointId", "DomainStateEnvelope",
    "DomainStateId", "EventId", "HistoryId", "ProviderBindingId",
    "ProvenanceRecordId", "R6RunId", "SpatialSupport", "SupportClass",
    "TimeSupport",
]
