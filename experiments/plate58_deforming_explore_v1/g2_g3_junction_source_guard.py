"""Source-original regional junction gate, not physical fault mechanics.

A parent identifier is a global identity.  Its presence in a 8x8 source
footprint does *not* imply a local three-plate junction.  The authenticated
G3 interface provider owns region-local incident-plate topology.

This module has no solver, material, traction, HistoryStore or IO effects.
"""
from __future__ import annotations

SCHEMA = "ARCANA_R6_G2_G3_ORIGINAL_REGIONAL_JUNCTION_INCIDENCE_V1"


class SourceJunctionError(ValueError):
    pass


def require(ok: bool, code: str) -> None:
    if not ok:
        raise SourceJunctionError(code)


def certify_regional_junction(parent_ids: list[int], interface_scope: dict,
                              extent: int) -> dict:
    """Validate source-provider junction incidence; never invent fault DOFs.

    The provider MUST already have been authenticated via its SHA-chained
    upstream manifest.  It can include global node 34587 in 8x8 even when
    that local crop has exactly zero three-plate incidences.
    """
    require(type(extent) is int and extent in (8, 16),
            "G2_G3_JUNCTION_EXTENT_UNSUPPORTED")
    require(type(parent_ids) is list and len(parent_ids) == (extent + 1) ** 2
            and all(type(n) is int and n > 0 for n in parent_ids)
            and len(set(parent_ids)) == len(parent_ids),
            "G2_G3_JUNCTION_PARENT_SOURCE_IDS_INVALID")
    require(type(interface_scope) is dict
            and int(interface_scope.get("extent_cells_per_side", -1)) == extent
            and type(interface_scope.get("actual_3plus_plate_junctions")) is list
            and type(interface_scope.get("triple_plate_junction_exists")) is bool,
            "G2_G3_JUNCTION_INTERFACE_PROVIDER_MISSING")
    records = interface_scope["actual_3plus_plate_junctions"]
    need = []
    for row in records:
        require(type(row) is dict
                and set(row) == {"parent_node_id", "incident_plates"},
                "G2_G3_JUNCTION_PROVIDER_RECORD_INVALID")
        parent = row["parent_node_id"]
        plates = row["incident_plates"]
        require(type(parent) is int and parent in parent_ids
                and type(plates) is list and len(plates) >= 3
                and all(type(n) is int and n > 0 for n in plates)
                and plates == sorted(set(plates)),
                "G2_G3_JUNCTION_PROVIDER_INCIDENCE_INVALID")
        need.append({"parent_node_id": parent,
                     "incident_plates": list(plates)})
    require(len({r["parent_node_id"] for r in need}) == len(need)
            and (bool(need) == interface_scope["triple_plate_junction_exists"]),
            "G2_G3_JUNCTION_PROVIDER_FLAG_OR_DUPLICATES_INVALID")
    if extent == 8:
        require(need == [], "G2_G3_JUNCTION_8X8_NO_TRIPLE_EXPECTED")
    else:
        require(need == [{"parent_node_id": 34587,
                          "incident_plates": [5, 8, 11]}],
                "G2_G3_JUNCTION_16X16_ORIGINAL_TRIPLE_REQUIRED")
    return {
        "schema": SCHEMA,
        "extent_cells": extent,
        "source_parent_34587_in_footprint": 34587 in parent_ids,
        "source_actual_3plus_plate_junctions": need,
        "local_triple_parent_id": 34587 if need else None,
        "source_junction_is_not_fault_slip_dof": True,
        "physical_fault_transmission_law_qualified": False,
        "mechanical_solve_authorized": False,
        "physical_T1": None,
        "D_024": "ACTIVE",
    }
