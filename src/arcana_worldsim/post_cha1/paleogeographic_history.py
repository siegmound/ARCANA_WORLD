from __future__ import annotations

from collections import deque, defaultdict
import math
import numpy as np

STATUS = "PASS_PALEOGEOGRAPHIC_EVENT_RECONSTRUCTION_CANDIDATE"

_CACHE: dict[tuple, dict] = {}


def _multi_source_grid_distance(target: np.ndarray) -> np.ndarray:
    """8-neighbour grid distance with periodic longitude and closed latitude."""
    target = np.asarray(target, dtype=bool)
    ny, nx = target.shape
    inf = np.iinfo(np.int32).max
    dist = np.full((ny, nx), inf, dtype=np.int32)
    q = deque()
    ys, xs = np.where(target)
    for y, x in zip(ys.tolist(), xs.tolist()):
        dist[y, x] = 0
        q.append((y, x))
    if not q:
        return np.full((ny, nx), float(ny + nx), dtype=float)
    nbr = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
    while q:
        y, x = q.popleft(); nd = dist[y, x] + 1
        for dy, dx in nbr:
            yy = y + dy
            if yy < 0 or yy >= ny:
                continue
            xx = (x + dx) % nx
            if nd < dist[yy, xx]:
                dist[yy, xx] = nd
                q.append((yy, xx))
    return dist.astype(float)


def build_transition_schedule(a1, older_ma: float = 60.0, younger_ma: float = 30.0,
                              phase_min: float = 0.05, phase_max: float = 0.95) -> dict:
    ages = np.asarray(a1["age_ma"], dtype=float)
    io = int(np.where(np.isclose(ages, older_ma, atol=1e-12))[0][0])
    iy = int(np.where(np.isclose(ages, younger_ma, atol=1e-12))[0][0])
    l0 = np.asarray(a1["land_mask"][io], dtype=bool)
    l1 = np.asarray(a1["land_mask"][iy], dtype=bool)
    p0 = np.asarray(a1["plate_code"][io], dtype=np.int16)
    p1 = np.asarray(a1["plate_code"][iy], dtype=np.int16)
    persistent = l0 & l1
    drowning = l0 & ~l1
    emerging = ~l0 & l1
    phase = np.full(l0.shape, np.nan, dtype=float)
    kind = np.zeros(l0.shape, dtype=np.int8)  # -1 drowning, +1 emerging
    plate = np.zeros(l0.shape, dtype=np.int16)
    kind[drowning] = -1; kind[emerging] = 1
    plate[drowning] = p0[drowning]; plate[emerging] = p1[emerging]

    # First build a plate-core-relative event-order score in [0,1].  This
    # preserves the physically motivated spatial ordering while the second pass
    # below rank-balances emergence and drowning, preventing creation/removal of
    # large amounts of intermediate land area merely from unequal event timing.
    order = np.full(l0.shape, np.nan, dtype=float)
    all_plates = sorted(set(np.unique(plate[kind != 0]).tolist()))
    for pid in all_plates:
        stable_old = persistent & (p0 == pid)
        stable_new = persistent & (p1 == pid)
        for mask, stable, mode in ((drowning & (p0 == pid), stable_old, -1),
                                   (emerging & (p1 == pid), stable_new, +1)):
            if not np.any(mask):
                continue
            target = stable if np.any(stable) else persistent
            d = _multi_source_grid_distance(target)
            vals = d[mask]
            lo, hi = float(np.min(vals)), float(np.max(vals))
            norm = np.full(vals.shape, 0.5, dtype=float) if hi-lo < 1e-12 else (vals-lo)/(hi-lo)
            # emergence: core-near first; drowning: core-far first
            order[mask] = norm if mode > 0 else (1.0 - norm)

    span = max(float(phase_max)-float(phase_min), 1e-12)
    ny, nx = l0.shape
    for k, mask in ((1, emerging), (-1, drowning)):
        ys, xs = np.where(mask)
        if not len(ys):
            continue
        # Spatial coordinates are used only as deterministic tie breakers for
        # equal graph-distance ranks; they do not alter non-tied ordering.
        rows = sorted(zip(ys.tolist(), xs.tolist()), key=lambda q: (float(order[q]), int(plate[q]), q[0], q[1]))
        n = len(rows)
        for rank, (y, x) in enumerate(rows):
            quantile = (rank + 0.5) / n
            phase[y, x] = phase_min + span * quantile

    duration = float(older_ma-younger_ma)
    event_rows=[]; groups=defaultdict(list)
    ys,xs=np.where(kind!=0)
    for y,x in zip(ys.tolist(),xs.tolist()):
        event_age=older_ma-float(phase[y,x])*duration
        bin_index=int(math.floor((older_ma-event_age)/2.0+1e-12))
        groups[(int(plate[y,x]),int(kind[y,x]),bin_index)].append((y,x,event_age))
    for (pid,k,b),cells in sorted(groups.items()):
        ages_evt=[c[2] for c in cells]
        event_rows.append({
            "event_id":f"PGE_{int(older_ma)}_{int(younger_ma)}_P{pid:02d}_{'EMERGE' if k>0 else 'DROWN'}_B{b:02d}",
            "plate_code":pid,"transition":"EMERGENCE" if k>0 else "DROWNING",
            "cell_count":len(cells),"event_age_ma_mean":float(np.mean(ages_evt)),
            "event_age_ma_min":float(np.min(ages_evt)),"event_age_ma_max":float(np.max(ages_evt)),
            "semantic_status":"DERIVED_ENDPOINT_CONSTRAINED_EVENT_CLUSTER_NOT_INDEPENDENT_GEOLOGICAL_OBSERVATION",
        })
    return {"older_ma":float(older_ma),"younger_ma":float(younger_ma),"older_index":io,"younger_index":iy,
            "land_older":l0,"land_younger":l1,"phase":phase,"kind":kind,"plate":plate,
            "persistent_land":persistent,"event_catalog":event_rows,
            "diagnostics":{"persistent_land_cells":int(np.sum(persistent)),"persistent_ocean_cells":int(np.sum(~l0&~l1)),
              "drowning_cells":int(np.sum(drowning)),"emerging_cells":int(np.sum(emerging)),
              "phase_min_realized":float(np.nanmin(phase[kind!=0])) if np.any(kind!=0) else None,
              "phase_max_realized":float(np.nanmax(phase[kind!=0])) if np.any(kind!=0) else None,
              "event_cluster_count":len(event_rows),"temporal_balance_semantics":"SEPARATE_UNIFORM_QUANTILE_SCHEDULES_PRESERVE_NET_LAND_AREA_TREND"}}


def _schedule(a1, older_ma, younger_ma, phase_min, phase_max):
    ages = tuple(np.asarray(a1["age_ma"], dtype=float).tolist())
    key = (ages, tuple(a1["land_mask"].shape), float(older_ma), float(younger_ma), float(phase_min), float(phase_max))
    if key not in _CACHE:
        _CACHE[key] = build_transition_schedule(a1, older_ma, younger_ma, phase_min, phase_max)
    return _CACHE[key]


def event_reconstructed_land_support(a1, age_ma: float, older_ma: float = 60.0, younger_ma: float = 30.0,
                                     phase_min: float = 0.05, phase_max: float = 0.95,
                                     transition_width_years: float = 1_000_000.0):
    sched = _schedule(a1, older_ma, younger_ma, phase_min, phase_max)
    l0 = sched["land_older"].astype(float); l1 = sched["land_younger"].astype(float)
    if age_ma >= older_ma - 1e-12:
        return l0.copy(), sched
    if age_ma <= younger_ma + 1e-12:
        return l1.copy(), sched
    alpha = (older_ma - float(age_ma)) / max(older_ma - younger_ma, 1e-15)
    phase = sched["phase"]; kind = sched["kind"]
    width_phase = max(float(transition_width_years) / 1_000_000.0 / max(older_ma - younger_ma, 1e-15), 1e-9)
    x = np.clip((alpha - (phase - 0.5 * width_phase)) / width_phase, 0.0, 1.0)
    smooth = x * x * (3.0 - 2.0 * x)
    support = l0.copy()
    emerge = kind > 0; drown = kind < 0
    support[emerge] = smooth[emerge]
    support[drown] = 1.0 - smooth[drown]
    return np.clip(support, 0.0, 1.0), sched


def reconstructed_substrate(a1, relative_year: float, linear_provider,
                            residual_temp_anomaly_c: float = 0.0,
                            older_ma: float = 60.0, younger_ma: float = 30.0,
                            phase_min: float = 0.05, phase_max: float = 0.95,
                            transition_width_years: float = 1_000_000.0):
    sub = linear_provider(a1, relative_year, residual_temp_anomaly_c)
    age = float(sub["age_ma"])
    if younger_ma - 1e-12 <= age <= older_ma + 1e-12:
        land, sched = event_reconstructed_land_support(
            a1, age, older_ma, younger_ma, phase_min, phase_max, transition_width_years)
        sub["land_support"] = land
        sub["accessible"] = land > 1e-9
        sub["paleogeographic_history_provider"] = "PLATE_CORE_CONSTRAINED_ENDPOINT_EVENT_RECONSTRUCTION"
        sub["paleogeographic_event_schedule_status"] = STATUS
        sub["paleogeographic_event_diagnostics"] = sched["diagnostics"]
    return sub
