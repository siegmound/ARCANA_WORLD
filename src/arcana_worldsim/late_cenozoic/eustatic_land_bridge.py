from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
import numpy as np

STATUS = "PASS_RELATIVE_EUSTATIC_SHORELINE_ANOMALY_A1_EFFECTIVE_LAND_BRIDGE_CANDIDATE"
AUTHORITY = "A1_TECTONIC_TOPOLOGY_PLUS_v0.6.1_RELATIVE_EUSTATIC_ANOMALY"


@dataclass(frozen=True)
class EustaticLandBridgeResult:
    effective_land_support: np.ndarray
    book_fraction: np.ndarray
    target_fraction: np.ndarray
    relative_fraction_anomaly: np.ndarray
    emergence_activation: np.ndarray
    submergence_activation: np.ndarray
    emergence_scale: float
    submergence_scale: float
    diagnostics: dict[str, Any]


def spherical_cell_weights(lat: np.ndarray, nlon: int, normalize_mean: bool = False) -> np.ndarray:
    lat = np.asarray(lat, dtype=float)
    if lat.ndim != 1 or lat.size < 2:
        raise ValueError("lat must be a regular 1-D grid")
    d = np.diff(lat)
    if not np.allclose(d, d[0], atol=1e-12, rtol=0):
        raise ValueError("lat must be regular")
    step = float(d[0])
    edges = np.concatenate(([lat[0] - step / 2.0], lat + step / 2.0))
    band = np.sin(np.deg2rad(edges[1:])) - np.sin(np.deg2rad(edges[:-1]))
    w = np.repeat(band[:, None], int(nlon), axis=1)
    if normalize_mean:
        w = w / float(w.mean())
    return w


def _solve_scale_to_weighted_target(raw: np.ndarray, eligible: np.ndarray, weights: np.ndarray,
                                    target: float, tol: float = 1e-12) -> tuple[float, np.ndarray]:
    raw = np.clip(np.asarray(raw, float), 0.0, 1.0)
    eligible = np.asarray(eligible, bool)
    w = np.asarray(weights, float)
    target = float(target)
    if target <= tol:
        return 0.0, np.zeros_like(raw)
    capacity = float((eligible * w).sum())
    if target > capacity + max(tol, 1e-12 * capacity):
        raise ValueError(f"eustatic anomaly cannot fit A1 compatible support: target={target}, capacity={capacity}")
    if not np.any(eligible & (raw > 0)):
        raise ValueError("eustatic anomaly has no compatible A1 shoreline cells")

    def amount(scale: float) -> float:
        return float((np.minimum(scale * raw, 1.0) * eligible * w).sum())

    hi = 1.0
    while amount(hi) < target and hi < 1e12:
        hi *= 2.0
    if amount(hi) < target - tol:
        raise ValueError("eustatic anomaly cannot be conserved without inventing non-local support")
    lo = 0.0
    for _ in range(96):
        mid = 0.5 * (lo + hi)
        if amount(mid) < target:
            lo = mid
        else:
            hi = mid
    scale = hi
    activation = np.minimum(scale * raw, 1.0) * eligible
    return float(scale), activation


def bridge_relative_eustatic_anomaly(
    a1_book_land_support: np.ndarray,
    book_fraction: np.ndarray,
    target_fraction: np.ndarray,
    lat: np.ndarray,
    *,
    eps: float = 1e-12,
) -> EustaticLandBridgeResult:
    """Transfer only relative high-resolution shoreline change onto A1 topology.

    A1's book-era binary/coarse land support remains the topological authority.
    v0.6.1 contributes only the *change* from its own book-era high-resolution
    shoreline. Positive change activates fractional shelf support only in A1
    ocean cells; negative change removes support only from A1 land cells.
    Positive and negative area anomalies are conserved separately in spherical
    area, so no global exposed area is created or destroyed by the bridge.
    """
    base = np.asarray(a1_book_land_support, dtype=float)
    f0 = np.clip(np.asarray(book_fraction, dtype=float), 0.0, 1.0)
    ft = np.clip(np.asarray(target_fraction, dtype=float), 0.0, 1.0)
    if base.shape != f0.shape or base.shape != ft.shape:
        raise ValueError("A1 support and remapped shoreline fractions must have identical shapes")
    if np.any((base < -eps) | (base > 1.0 + eps)):
        raise ValueError("A1 book land support must lie in [0,1]")
    base = np.clip(base, 0.0, 1.0)
    w = spherical_cell_weights(np.asarray(lat, float), base.shape[1], normalize_mean=False)
    d = ft - f0
    pos = np.maximum(d, 0.0)
    neg = np.maximum(-d, 0.0)

    # Relative fraction of the locally available submerged/exposed sub-grid
    # reservoir that changes state. This uses v0.6.1 only as an anomaly field.
    emerge_raw = np.where(base < 0.5, pos / np.maximum(1.0 - f0, eps), 0.0)
    submerge_raw = np.where(base >= 0.5, neg / np.maximum(f0, eps), 0.0)

    pos_target = float((pos * w).sum())
    neg_target = float((neg * w).sum())
    escale, emerge = _solve_scale_to_weighted_target(emerge_raw, base < 0.5, w, pos_target)
    sscale, submerge = _solve_scale_to_weighted_target(submerge_raw, base >= 0.5, w, neg_target)

    effective = np.clip(base + emerge - submerge, 0.0, 1.0)
    effective_delta = effective - base
    pos_eff = float((np.maximum(effective_delta, 0.0) * w).sum())
    neg_eff = float((np.maximum(-effective_delta, 0.0) * w).sum())

    diagnostics = {
        "status": STATUS,
        "authority": AUTHORITY,
        "book_endpoint_exact_by_construction": True,
        "positive_highres_area_anomaly": pos_target,
        "negative_highres_area_anomaly": neg_target,
        "positive_effective_area_anomaly": pos_eff,
        "negative_effective_area_anomaly": neg_eff,
        "positive_conservation_error": abs(pos_eff - pos_target),
        "negative_conservation_error": abs(neg_eff - neg_target),
        "net_conservation_error": abs((pos_eff-neg_eff) - float((d*w).sum())),
        "emergence_scale": float(escale),
        "submergence_scale": float(sscale),
        "effective_support_min": float(effective.min()),
        "effective_support_max": float(effective.max()),
        "fractional_effective_cells": int(np.sum((effective > eps) & (effective < 1.0-eps))),
        "a1_ocean_cells_activated": int(np.sum((base < 0.5) & (effective > eps))),
        "a1_land_cells_reduced": int(np.sum((base >= 0.5) & (effective < 1.0-eps))),
        "absolute_v061_coastline_substituted": False,
        "canonical_events_added": 0,
        "biology_modified": False,
    }
    return EustaticLandBridgeResult(
        effective_land_support=effective,
        book_fraction=f0,
        target_fraction=ft,
        relative_fraction_anomaly=d,
        emergence_activation=emerge,
        submergence_activation=submerge,
        emergence_scale=float(escale),
        submergence_scale=float(sscale),
        diagnostics=diagnostics,
    )


def apply_effective_land_to_boundary(boundary: Any, effective_land_support: np.ndarray):
    """Return a RecentBoundaryState-like copy with A1-effective land support.

    Environmental forage fields are rescaled only by the change in land support
    relative to the boundary's previous fractional support; climate fields are
    untouched. This is a bridge operation, not a new flora model.
    """
    from dataclasses import replace
    old = np.clip(np.asarray(boundary.paleo_land_mask, float), 0.0, 1.0)
    new = np.clip(np.asarray(effective_land_support, float), 0.0, 1.0)
    if old.shape != new.shape:
        raise ValueError("effective support shape does not match boundary")
    ratio = np.zeros_like(new)
    positive = old > 1e-12
    ratio[positive] = new[positive] / old[positive]
    # Newly activated A1 shelf cells have no inherited A1 book forage in the
    # B1 bridge. They remain zero here; colonizable/resource support must be
    # supplied by the integrated flora provider, not invented by shoreline code.
    return replace(
        boundary,
        browse_forage=np.asarray(boundary.browse_forage, float) * ratio,
        low_forage=np.asarray(boundary.low_forage, float) * ratio,
        wetland_forage=np.asarray(boundary.wetland_forage, float) * ratio,
        total_edible_forage=np.asarray(boundary.total_edible_forage, float) * ratio,
        paleo_land_mask=new,
        provenance=str(boundary.provenance) + "+RELATIVE_EUSTATIC_A1_EFFECTIVE_LAND_SUPPORT_BRIDGE",
    )
