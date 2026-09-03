from __future__ import annotations

"""Engine-independent spatial reconstruction authority for R4.29+.

This module is deliberately not executed by R4.29.  R4.29 only validates and
hash-freezes its source/input authority so a later stage may execute it.
The construction never consumes Geonomics output, R3.15 coordinates, or R3.28
coordinates.  Spatial support comes from the canonical late-Cenozoic A1 land
provider, while population and deme-count constraints come from SEALED R3.27.
"""

from pathlib import Path
from typing import Any
import hashlib
import json
import numpy as np

AUTHORITY_ALGORITHM = "MINIMUM_DISPLACEMENT_MAXIMUM_ENTROPY_SPATIALIZATION"
STATE_VARIABLE_NAMES = ["population_proxy", "grid_row", "grid_col", "active"]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _grid_distance(a: tuple[int, int], b: tuple[int, int], nx: int) -> float:
    dy = abs(int(a[0]) - int(b[0]))
    dx0 = abs(int(a[1]) - int(b[1]))
    dx = min(dx0, nx - dx0)
    return float((dy * dy + dx * dx) ** 0.5)


def _accessible_cells(support: np.ndarray) -> np.ndarray:
    return np.argwhere(np.asarray(support, dtype=float) > 1e-9)


def maximum_entropy_seed(support: np.ndarray, n: int, seed: int) -> list[tuple[int, int]]:
    cells = _accessible_cells(support)
    if len(cells) == 0:
        raise ValueError("no accessible canonical land support")
    n = max(1, min(int(n), len(cells)))
    rng = np.random.default_rng(int(seed))
    # Deterministic seeded candidate pool.  The pool is bounded for runtime but
    # remains result-independent and samples only age-matched canonical support.
    pool_n = min(len(cells), 1024)
    if pool_n < len(cells):
        idx = np.sort(rng.choice(len(cells), size=pool_n, replace=False))
        pool = cells[idx]
    else:
        pool = cells.copy()
    first = int(rng.integers(0, len(pool)))
    chosen_idx = [first]
    ny, nx = support.shape
    while len(chosen_idx) < n:
        rr = pool[:, 0].astype(float)
        cc = pool[:, 1].astype(float)
        min_d2 = np.full(len(pool), np.inf, dtype=float)
        for ci in chosen_idx:
            dr = rr - float(pool[ci, 0])
            dc0 = np.abs(cc - float(pool[ci, 1]))
            dc = np.minimum(dc0, float(nx) - dc0)
            min_d2 = np.minimum(min_d2, dr * dr + dc * dc)
        min_d2[np.asarray(chosen_idx, dtype=int)] = -1.0
        nxt = int(np.argmax(min_d2))
        if min_d2[nxt] < 0:
            break
        chosen_idx.append(nxt)
    return [tuple(map(int, pool[i])) for i in chosen_idx]

def _nearest_accessible(cell: tuple[int, int], support: np.ndarray) -> tuple[int, int]:
    cells = _accessible_cells(support)
    if len(cells) == 0:
        raise ValueError("no accessible canonical land support")
    nx = int(support.shape[1])
    dr = cells[:, 0].astype(float) - float(cell[0])
    dc0 = np.abs(cells[:, 1].astype(float) - float(cell[1]))
    dc = np.minimum(dc0, float(nx) - dc0)
    d2 = dr * dr + dc * dc
    m = float(np.min(d2))
    cand = cells[np.isclose(d2, m)]
    order = np.lexsort((cand[:, 1], cand[:, 0]))
    q = cand[int(order[0])]
    return int(q[0]), int(q[1])


def advance_minimum_displacement(
    prior: list[tuple[int, int]], support: np.ndarray, target_demes: int, seed: int
) -> list[tuple[int, int]]:
    target_demes = max(1, int(target_demes))
    accessible = np.asarray(support, dtype=float) > 1e-9
    kept: list[tuple[int, int]] = []
    for p in prior:
        r, c = p
        if 0 <= r < accessible.shape[0] and 0 <= c < accessible.shape[1] and accessible[r, c]:
            q = (int(r), int(c))
        else:
            q = _nearest_accessible((int(r), int(c)), support)
        if q not in kept:
            kept.append(q)

    if len(kept) > target_demes:
        # Remove the most redundant cells first (smallest nearest-neighbour separation).
        nx = int(accessible.shape[1])
        while len(kept) > target_demes:
            score = []
            for i, p in enumerate(kept):
                others = kept[:i] + kept[i + 1 :]
                d = min((_grid_distance(p, q, nx) for q in others), default=float("inf"))
                score.append((d, p[0], p[1], i))
            score.sort()
            kept.pop(score[0][3])

    if len(kept) < target_demes:
        seeded = maximum_entropy_seed(support, min(target_demes, int(np.sum(accessible))), seed)
        for q in seeded:
            if q not in kept:
                kept.append(q)
            if len(kept) >= target_demes:
                break
    return kept[:target_demes]


def authority_input_spec(root: Path) -> dict[str, Path]:
    return {
        "r327_trajectory": root / "outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz",
        "r327_authority": root / "outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_AUTHORITY.json",
        "r327_checkpoint": root / "outputs/v0_6D1_R3_27/R3_27_HUMAN_200KA_CHECKPOINT.json",
        "r327_seal": root / "outputs/v0_6D1_R3_27_SEAL/R3_27_FINAL_SEAL_AUDIT.json",
        "a1_full": root / "references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz",
        "late_cenozoic_provider": root / "src/arcana_worldsim/late_cenozoic/paleogeography.py",
        "paleogeographic_history_provider": root / "src/arcana_worldsim/post_cha1/paleogeographic_history.py",
    }


def validate_authority_inputs(root: Path) -> dict[str, Any]:
    paths = authority_input_spec(root)
    present = {k: p.exists() for k, p in paths.items()}
    checks: dict[str, bool] = {"all_required_paths_present": all(present.values())}
    details: dict[str, Any] = {"paths": {k: str(v) for k, v in paths.items()}, "present": present}
    if not checks["all_required_paths_present"]:
        return {"ready": False, "checks": checks, "details": details, "hashes": {}}

    seal = load_json(paths["r327_seal"])
    auth = load_json(paths["r327_authority"])
    cp = load_json(paths["r327_checkpoint"])
    checks["r327_sealed"] = str(seal.get("status", "")).startswith("PASS_R327_") and seal.get("verdict") == "SEALED"
    window = auth.get("window") or {}
    checks["r327_window_exact_3ma_to_200ka"] = float(window.get("start_age_ma", -1)) == 3.0 and float(window.get("end_age_ma", -1)) == 0.2
    cohort = list(cp.get("candidate_cohort") or [])
    checks["r327_human_200ka_candidate_cohort_nonempty"] = len(cohort) >= 1

    with np.load(paths["r327_trajectory"], allow_pickle=False) as z:
        needed = {"candidate_ids", "age_ma", "variable_names", "state"}
        checks["r327_npz_required_keys"] = needed.issubset(set(z.files))
        ages = np.asarray(z["age_ma"], dtype=float)
        vars_ = [str(x) for x in np.asarray(z["variable_names"]).tolist()]
        cands = [str(x) for x in np.asarray(z["candidate_ids"]).tolist()]
        checks["r327_time_axis_exact_endpoints"] = len(ages) >= 2 and abs(float(ages[0]) - 3.0) < 1e-12 and abs(float(ages[-1]) - 0.2) < 1e-9
        checks["r327_required_macro_variables"] = {"effective_population", "deme_count"}.issubset(set(vars_))
        checks["checkpoint_candidates_exist_in_trajectory"] = all(c in cands for c in cohort)
        state_shape = tuple(np.asarray(z["state"]).shape)
        checks["r327_geometry_exact_96_members_and_141_times"] = len(state_shape) == 4 and state_shape[0] == 96 and state_shape[2] == 141 and state_shape[3] == len(vars_)
        checks["r327_time_axis_exact_141_states"] = len(ages) == 141
        checks["r327_checkpoint_candidate_cohort_exact"] = cohort == ["RPT_010_D02", "RPT_009_D02"]
        details["r327_geometry"] = list(state_shape)
        details["r327_age_count"] = int(len(ages))
        details["candidate_cohort"] = cohort

    with np.load(paths["a1_full"], allow_pickle=False) as z:
        needed = {"age_ma", "lat", "lon", "land_mask", "plate_code"}
        checks["a1_required_keys"] = needed.issubset(set(z.files))
        ages = np.asarray(z["age_ma"], dtype=float)
        checks["a1_has_30ma_and_0ma_endpoints"] = bool(np.any(np.isclose(ages, 30.0)) and np.any(np.isclose(ages, 0.0)))
        grid_shape = [int(len(z["lat"])), int(len(z["lon"]))]
        checks["a1_grid_exact_90x180"] = grid_shape == [90, 180]
        details["a1_grid_shape"] = grid_shape

    provider_text = paths["late_cenozoic_provider"].read_text(encoding="utf-8-sig")
    hist_text = paths["paleogeographic_history_provider"].read_text(encoding="utf-8-sig")
    checks["provider_is_canonical_late_cenozoic_land_support"] = "physical_paleogeography_state" in provider_text and "PLATE_CORE_CONSTRAINED_ENDPOINT_EVENT_RECONSTRUCTION" in (provider_text + hist_text)
    checks["no_geonomics_dependency"] = "import geonomics" not in provider_text.lower() and "import geonomics" not in hist_text.lower()

    hashes = {k: sha256(v) for k, v in paths.items()}
    return {"ready": all(checks.values()), "checks": checks, "details": details, "hashes": hashes}


def build_replay(root: Path, seed_base: int = 429290) -> dict[str, Any]:
    """Execute the new authority. Intended for R4.30+, not R4.29."""
    v = validate_authority_inputs(root)
    if not v["ready"]:
        raise RuntimeError(f"J14 spatial authority inputs not valid: {v['checks']}")

    from arcana_worldsim.late_cenozoic.paleogeography import physical_paleogeography_state

    p = authority_input_spec(root)
    with np.load(p["a1_full"], allow_pickle=False) as a1z:
        a1 = {k: np.asarray(a1z[k]) for k in a1z.files}
    cp = load_json(p["r327_checkpoint"])
    cohort = [str(x) for x in cp.get("candidate_cohort") or []]
    with np.load(p["r327_trajectory"], allow_pickle=False) as z:
        candidate_ids = [str(x) for x in np.asarray(z["candidate_ids"]).tolist()]
        ages = np.asarray(z["age_ma"], dtype=float)
        variable_names = [str(x) for x in np.asarray(z["variable_names"]).tolist()]
        state = np.asarray(z["state"], dtype=float)
    vix = {v: i for i, v in enumerate(variable_names)}
    cix = [candidate_ids.index(c) for c in cohort]
    ensemble_n = int(state.shape[0])
    max_demes = int(max(1, np.ceil(np.nanmax(state[:, cix, :, vix["deme_count"]]))))
    spatial = np.zeros((ensemble_n, len(cix), len(ages), max_demes, 4), dtype=np.float32)

    for e in range(ensemble_n):
        for jj, j in enumerate(cix):
            prior: list[tuple[int, int]] = []
            for t, age in enumerate(ages):
                land = np.asarray(physical_paleogeography_state(a1, float(age))["land_support"], dtype=float)
                n = int(np.clip(round(float(state[e, j, t, vix["deme_count"]])), 1, max_demes))
                seed = int(seed_base + e * 10007 + jj * 997 + t * 37)
                prior = maximum_entropy_seed(land, n, seed) if t == 0 else advance_minimum_displacement(prior, land, n, seed)
                total_n = max(0.0, float(state[e, j, t, vix["effective_population"]]))
                share = total_n / max(len(prior), 1)
                for d, (r, c) in enumerate(prior):
                    spatial[e, jj, t, d, :] = [share, float(r), float(c), 1.0]

    return {
        "authority_algorithm": AUTHORITY_ALGORITHM,
        "age_ma": ages,
        "candidate_ids": np.asarray(cohort),
        "state_variable_names": np.asarray(STATE_VARIABLE_NAMES),
        "spatial_state": spatial,
        "input_hashes": v["hashes"],
        "construction_semantics": "MODEL_DERIVED_ENGINE_INDEPENDENT_SPATIAL_AUTHORITY_NOT_OBSERVED_LOCATION_HISTORY",
        "future_spatial_anchor_used_in_construction": False,
        "external_engine_used_in_construction": False,
    }
