#!/usr/bin/env python3
"""Source-faithful, non-executing comparison of R6 and legacy ShellSet columns."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
from typing import Any

import numpy as np

from arcana_worldsim.r6.pre_orbdata_runtime_package import FIELDS
from arcana_worldsim.r6.shellset_mesh.adapter import load_canonical_mesh


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_NAME = "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat"
PHYSICAL_NAME = "R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz"
INPUT = Path("external/ShellSet-v1.1.0/INPUT/iEarth5-049.in")
GRID = Path("external/ShellSet-v1.1.0/INPUT/GridInput.in")
SHELLS = Path("external/ShellSet-v1.1.0/src/MOD_Shells.f90")
ORBDATA = Path("external/ShellSet-v1.1.0/src/MOD_Data.f90")

# MOD_Data.f90 BLOCK DATA BD1, COMMON /S1S2S3/, source lines 1424-1440.
IP_WEIGHTS = np.asarray([
    [1/3, 1/3, 1/3],
    [0.0597158733333333, 0.4701420633333333, 0.4701420633333333],
    [0.4701420633333333, 0.0597158733333333, 0.4701420633333333],
    [0.4701420633333333, 0.4701420633333333, 0.0597158733333333],
    [0.7974269866666667, 0.1012865066666667, 0.1012865066666667],
    [0.1012865066666667, 0.7974269866666667, 0.1012865066666667],
    [0.1012865066666667, 0.1012865066666667, 0.7974269866666667],
], dtype=np.float64)
IDX = {name: i for i, name in enumerate(FIELDS)}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _parameter(text: str, name: str) -> list[float]:
    for line in text.splitlines():
        left = line.split("!", 1)[0].strip()
        if re.search(r"\b" + re.escape(name) + r"\s*[=,]", line) is None:
            continue
        token = left.split()[0].rstrip(",")
        if not re.fullmatch(r"[+\-0-9.eEdD,]+", token):
            continue
        return [float(x.replace("D", "E").replace("d", "e")) for x in token.split(",")]
    raise ValueError(f"SHELLSET_PARAMETER_NOT_FOUND:{name}")


def read_shell_parameters(root: Path) -> dict[str, Any]:
    text = (root / INPUT).read_text(encoding="utf-8")
    grid = (root / GRID).read_text(encoding="utf-8")
    values = {k: _parameter(text, k) for k in (
        "aCreep", "bCreep", "cCreep", "eCreep", "tAdiab", "gradie",
        "zBAsth", "rhoH2O", "rhoBar", "rhoAst", "gMean", "oneKm",
        "alphaT", "conduc", "radio", "tSurf", "temLim")}
    adiabat_pair = values["tAdiab"]
    if len(adiabat_pair) != 2:
        raise ValueError("SHELLSET_ADIABAT_PARAMETER_PAIR_INVALID")
    values["tAdiab"] = [adiabat_pair[0]]
    values["gradie"] = [adiabat_pair[1]]
    rows = [line.strip() for line in grid.splitlines()]
    pos = next(i for i, line in enumerate(rows) if line.startswith("rhoBar_C"))
    values["rhoBar_C_grid_range"] = [float(rows[pos + 1].split("!",1)[0]), float(rows[pos + 2].split("!",1)[0])]
    values["rhoBar_C_grid_num_models"] = int(rows[pos + 3].split("!",1)[0])
    return values


def load_runtime(root: Path) -> tuple[dict[str, Any], np.ndarray, np.ndarray]:
    manifest = json.loads((root / "R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json").read_text(encoding="utf-8"))
    path = root / RUNTIME_NAME
    digest = sha(path)
    if digest != manifest["runtime_data_sha256"]:
        raise ValueError("RUNTIME_PACKAGE_SHA256_MISMATCH")
    rows = np.loadtxt(path, skiprows=1, dtype=np.float64)
    if rows.shape != (64_442, len(FIELDS)):
        raise ValueError("RUNTIME_PACKAGE_SHAPE_MISMATCH")
    if not np.array_equal(rows[:, 0], np.arange(1, 64_443)):
        raise ValueError("RUNTIME_PACKAGE_NODE_ORDER_INVALID")
    return manifest, rows, np.load(root / PHYSICAL_NAME, allow_pickle=False)


def _poly(v: np.ndarray, z: np.ndarray, start: str) -> np.ndarray:
    i = IDX
    x = z - v[..., i[f"{start}_z0_m"]]
    return (((v[..., i[f"{start}_c3_k_m3"]] * x + v[..., i[f"{start}_c2_k_m2"]]) * x
             + v[..., i[f"{start}_c1_k_m"]]) * x + v[..., i[f"{start}_c0_k"]])


def arc_node_temperature(nodes: np.ndarray, z: float) -> np.ndarray:
    z = np.asarray(z, dtype=np.float64)
    i = IDX
    crust = nodes[:, i["crust_thickness_m"]]
    lab = nodes[:, i["lab_depth_m"]]
    t1 = _poly(nodes, np.full(len(nodes), z), "layer1")
    t2 = _poly(nodes, np.full(len(nodes), z), "layer2")
    alpha = nodes[:, i["mantle_expansivity_k_1"]]
    cp = nodes[:, i["mantle_cp_j_kg_k"]]
    tlab = nodes[:, i["lab_temperature_k"]]
    adiabat = tlab * np.exp(alpha * 9.82 * (z - lab) / cp)
    return np.where(z <= crust, t1, np.where(z <= lab, t2, adiabat))


def legacy_fillin_coefficients(nodes: np.ndarray, weights: np.ndarray,
                                p: dict[str, Any]) -> tuple[np.ndarray, ...]:
    """Port of MOD_Shells.F90 FillIn lines 3897-3961, including IP curvature fit."""
    i = IDX
    q = np.einsum("ej,ij->ei", nodes[:, :, i["surface_heat_flow_w_m2"]], weights)
    hc = np.einsum("ej,ij->ei", nodes[:, :, i["crust_thickness_m"]], weights)
    hm = np.einsum("ej,ij->ei", nodes[:, :, i["mantle_lithosphere_thickness_m"]], weights)
    kc, km = p["conduc"]
    rc, rm = p["radio"]
    surface = p["tSurf"][0]
    target = p["tAdiab"][0] + p["gradie"][0] * 100_000.0
    c2base = -0.5 * rc / kc
    moho_trial = surface + (q / kc) * hc + c2base * hc**2
    slope_m = (q / kc + 2*c2base*hc) * kc/km
    m2base = -0.5 * rm / km
    test = np.where(hm > 0, moho_trial + slope_m*hm + m2base*hm**2, moho_trial)
    total = hc + hm
    if np.any(total <= 0):
        raise ValueError("LEGACY_FILLIN_NONPOSITIVE_TOTAL_LITHOSPHERE")
    delta = -(test-target) / total**2
    c2 = c2base + delta
    tmoho = surface + (q/kc)*hc + c2*hc**2
    sm = ((q/kc) + 2*c2*hc) * kc/km
    m2 = m2base + delta
    return q, hc, hm, surface, q/kc, c2, tmoho, sm, m2, target


def legacy_fillin_temperature(coeff: tuple[np.ndarray, ...], z: float) -> np.ndarray:
    _q, hc, _hm, surface, slope_c, c2, tmoho, slope_m, m2, _target = coeff
    crust = surface + slope_c*z + c2*z*z
    mantle_depth = z-hc
    mantle = tmoho + slope_m*mantle_depth + m2*mantle_depth*mantle_depth
    return np.where(z <= hc, crust, mantle)


def legacy_squeez_temperature(nodes: np.ndarray, z: float, p: dict[str, Any]) -> np.ndarray:
    """Port of OrbData5 ARCANA FEG inputs + MOD_Shells Squeez, curvature=0."""
    i = IDX
    q = nodes[:, i["surface_heat_flow_w_m2"]]
    hc = nodes[:, i["crust_thickness_m"]]
    kc, km = p["conduc"]
    rc, rm = p["radio"]
    ts = p["tSurf"][0]
    g1 = ts
    g2 = q/kc
    g3 = -0.5*rc/kc  # cooling_curvature written by S1A OrbData is exactly zero
    tmoho = g1 + g2*hc + g3*hc**2
    g6 = (g2 + 2*g3*hc) * kc/km
    g7 = -0.5*rm/km
    raw = np.where(z <= hc, g1+g2*z+g3*z*z, tmoho+g6*(z-hc)+g7*(z-hc)**2)
    limits = np.where(z <= hc, p["temLim"][0], p["temLim"][1])
    return np.minimum(limits, raw)


def stats(values: np.ndarray) -> dict[str, float | int | None]:
    a = np.asarray(values, dtype=np.float64)
    a = a[np.isfinite(a)]
    if not len(a):
        return {"count": 0, "median_abs_k": None, "p90_abs_k": None,
                "p95_abs_k": None, "p99_abs_k": None, "max_abs_k": None, "rms_k": None}
    absolute = np.abs(a)
    return {"count": int(len(a)), "median_abs_k": float(np.median(absolute)),
            "p90_abs_k": float(np.quantile(absolute, .90)),
            "p95_abs_k": float(np.quantile(absolute, .95)),
            "p99_abs_k": float(np.quantile(absolute, .99)),
            "max_abs_k": float(absolute.max()), "rms_k": float(np.sqrt(np.mean(a*a)))}


def stats_value(values: np.ndarray) -> dict[str, float | int | None]:
    return {key.replace("_k", ""): value for key, value in stats(values).items()}


def _ip_values(tri_nodes: np.ndarray, field: str) -> np.ndarray:
    return np.einsum("enj,pj->ep", tri_nodes[:, :, IDX[field]], IP_WEIGHTS)


def evaluate_population(tri_nodes: np.ndarray, p: dict[str, Any]) -> dict[str, Any]:
    coeff = legacy_fillin_coefficients(tri_nodes, IP_WEIGHTS, p)
    _q, hc, hm, *_tail = coeff
    lab = hc + hm
    errors: list[np.ndarray] = []
    point_errors: dict[str, list[np.ndarray]] = {k: [] for k in (
        "mid_crust", "moho", "mid_mantle", "lab")}
    clips = {"layer1": 0, "layer2": 0, "samples": 0}
    squeeze_density_differences: list[float] = []
    squeeze_clip_count = 0
    squeeze_sample_count = 0
    zmax = int(np.ceil(float(lab.max())/1000.0))*1000
    for z in range(0, zmax+1, 1000):
        valid = z <= lab
        if not valid.any():
            continue
        arc_nodes = np.asarray([[arc_node_temperature(node[None, :], float(z))[0]
                                 for node in element] for element in tri_nodes])
        arc = np.einsum("ej,pj->ep", arc_nodes, IP_WEIGHTS)
        legacy = legacy_fillin_temperature(coeff, float(z))
        errors.append((legacy-arc)[valid].ravel())
        clip1 = valid & (z <= hc) & (legacy >= p["temLim"][0])
        clip2 = valid & (z > hc) & (legacy >= p["temLim"][1])
        clips["layer1"] += int(clip1.sum())
        clips["layer2"] += int(clip2.sum())
        clips["samples"] += int(valid.sum())
    depth_specs = {
        "mid_crust": .5*hc,
        "moho": hc,
        "mid_mantle": hc+.5*hm,
        "lab": lab,
    }
    for name, depths in depth_specs.items():
        for e in range(len(tri_nodes)):
            for ip in range(7):
                z = float(depths[e, ip])
                arc = float(np.dot(IP_WEIGHTS[ip], arc_node_temperature(tri_nodes[e], z)))
                legacy = float(legacy_fillin_temperature(coeff, z)[e, ip])
                point_errors[name].append(legacy-arc)
    all_errors = np.concatenate(errors) if errors else np.asarray([])

    # Squeez is nodal; its actual S1A FEG carries cooling_curvature=0.
    node_records = {int(row[IDX["node_id"]]): row
                    for row in tri_nodes.reshape(-1, len(FIELDS))}
    node_array = np.asarray(list(node_records.values()))
    i = IDX
    lab_nodes = node_array[:, i["lab_depth_m"]]
    crust_nodes = node_array[:, i["crust_thickness_m"]]
    max_lab = int(np.ceil(lab_nodes.max()/1000.0))*1000
    nodal_t_errors = []
    squeeze_clip_count = 0
    squeeze_sample_count = 0
    for z in range(0, max_lab+1, 1000):
        valid = lab_nodes >= z
        if not valid.any():
            continue
        arc_t = arc_node_temperature(node_array, float(z))
        old_t = legacy_squeez_temperature(node_array, float(z), p)
        nodal_t_errors.extend((old_t[valid]-arc_t[valid]).tolist())
        limits = np.where(z <= crust_nodes, p["temLim"][0], p["temLim"][1])
        squeeze_clip_count += int(np.count_nonzero(valid & (old_t >= limits)))
        squeeze_sample_count += int(valid.sum())
    # Include the exact nodal LAB endpoint in profile diagnostics.
    arc_lab = arc_node_temperature(node_array, lab_nodes)
    old_lab = legacy_squeez_temperature(node_array, lab_nodes, p)
    nodal_t_errors.extend((old_lab-arc_lab).tolist())

    rho_legacy = np.asarray(p["rhoBar"])
    alpha_legacy = np.asarray(p["alphaT"])
    def nodal_density(z_values: np.ndarray, arcana: bool) -> np.ndarray:
        crust_active = z_values <= crust_nodes
        if arcana:
            temp = arc_node_temperature(node_array, z_values)
            rho = np.where(crust_active, node_array[:, i["crust_density_kg_m3"]],
                           node_array[:, i["mantle_density_kg_m3"]])
            alpha = np.where(crust_active, node_array[:, i["crust_expansivity_k_1"]],
                             node_array[:, i["mantle_expansivity_k_1"]])
        else:
            temp = legacy_squeez_temperature(node_array, z_values, p)
            rho = np.where(crust_active, rho_legacy[0], rho_legacy[1])
            alpha = np.where(crust_active, alpha_legacy[0], alpha_legacy[1])
        return rho*(1.0-alpha*temp)
    floor_depth = np.floor(lab_nodes/1000.0)*1000.0
    previous_z = np.zeros_like(lab_nodes)
    prev_arc = nodal_density(previous_z, True)
    prev_old = nodal_density(previous_z, False)
    column_delta = np.zeros_like(lab_nodes)
    for z in range(1000, max_lab+1, 1000):
        active = floor_depth >= z
        if not active.any():
            continue
        cur_arc = nodal_density(np.full_like(lab_nodes, float(z)), True)
        cur_old = nodal_density(np.full_like(lab_nodes, float(z)), False)
        column_delta[active] += .5*((prev_old[active]-prev_arc[active])+
                                    (cur_old[active]-cur_arc[active]))*1000.0
        prev_arc[active] = cur_arc[active]
        prev_old[active] = cur_old[active]
        previous_z[active] = z
    resid = lab_nodes-previous_z
    end_arc = nodal_density(lab_nodes, True)
    end_old = nodal_density(lab_nodes, False)
    column_delta += .5*((prev_old-prev_arc)+(end_old-end_arc))*resid
    squeeze_density_differences.extend(column_delta.tolist())

    # Source OneBar samples cell-centres every oneKm through zBAsth and uses
    # geothM with absolute z (legacy coordinate mismatch is intentionally kept).
    zbo = float(p["zBAsth"][0]); dz = float(p["oneKm"][0])
    levels = np.arange(dz*.5, zbo, dz)
    if len(levels) > 0:
        onebar_effective = []
        flips = 0
        changed_ips = np.zeros((len(tri_nodes), 7), dtype=bool)
        arc_200k_count = 0
        legacy_200k_count = 0
        v_arc = np.zeros((len(tri_nodes), 7)); v_leg = np.zeros_like(v_arc)
        _q, hci, _hmi, surface, slope_c, c2, tm, slope_m, _m2, _target = coeff
        creep_a = np.asarray(p["aCreep"]); creep_b = np.asarray(p["bCreep"])
        creep_c = np.asarray(p["cCreep"]); ex = float(p["eCreep"][0]); ec = -1.0/ex
        for z in levels:
            node_t = arc_node_temperature(tri_nodes.reshape(-1, len(FIELDS)), float(z)).reshape(len(tri_nodes),3)
            arc_t = np.einsum("ej,pj->ep", node_t, IP_WEIGHTS)
            legacy_tg = np.where(z < hci, surface+slope_c*z+c2*z*z,
                                 tm+slope_m*z)  # source zeroes geothM quadratic/cubic
            ta = p["tAdiab"][0]+p["gradie"][0]*z
            arc_eff = np.maximum(200.0,np.minimum(arc_t,ta))
            legacy_eff = np.maximum(200.0,np.minimum(legacy_tg,ta))
            arc_200k_count += int(np.count_nonzero(arc_eff == 200.0))
            legacy_200k_count += int(np.count_nonzero(legacy_eff == 200.0))
            onebar_effective.append((legacy_eff-arc_eff).ravel())
            different = (legacy_tg < ta) != (arc_t < ta)
            flips += int(different.sum()); changed_ips |= different
            layer = (z >= hci).astype(int)
            aa, bb, cc = creep_a[layer], creep_b[layer], creep_c[layer]
            base = np.log(aa)*ec
            term = (bb+cc*z)*ec
            v_arc += dz*np.exp(np.maximum(base+term/arc_eff,-87.0))
            v_leg += dz*np.exp(np.maximum(base+term/legacy_eff,-87.0))
        glue_delta = 1.0/np.power(v_leg,ex)-1.0/np.power(v_arc,ex)
        onebar = {"effective_temperature_difference_legacy_minus_arcana_k": stats(np.asarray(onebar_effective)),
                  "glue_difference_legacy_minus_arcana_source_default": stats_value(glue_delta.ravel()),
                  "adiabat_intersection_source_branch_flip_depth_samples": flips,
                  "integration_points_with_any_intersection_branch_flip": int(changed_ips.sum()),
                  "integration_points_evaluated": len(tri_nodes)*7,
                  "arcana_200k_floor_samples": arc_200k_count,
                  "legacy_200k_floor_samples": legacy_200k_count,
                  "sampling_spacing_m": dz, "zBAsth_m": zbo}
    else:
        onebar = {"status": "SOURCE_PARAMETERS_INVALID"}

    # iConve=5 FillIn predicate compares baseT < 1273 K. FillIn's correction
    # targets tAdiab + gradie*100 km; calculate both source expressions.
    target = coeff[-1]
    legacy_base = coeff[2]  # hm controls the branch but target is its exact endpoint
    legacy_base = np.where(coeff[2] > 0, target, coeff[6])
    arc_base = np.empty_like(lab)
    for e in range(len(tri_nodes)):
        for ip in range(7):
            z = float(lab[e, ip])
            arc_base[e, ip] = np.dot(IP_WEIGHTS[ip], arc_node_temperature(tri_nodes[e], z))
    legacy_pred = legacy_base < 1273.0
    arc_pred = arc_base < 1273.0
    def temperature_range(a: np.ndarray) -> dict[str,float]:
        return {"min_k":float(np.min(a)),"median_k":float(np.median(a)),"max_k":float(np.max(a))}
    threshold = {"threshold_k": 1273.0, "legacy_pulled_true_count": int(legacy_pred.sum()),
                 "arcana_pulled_true_count": int(arc_pred.sum()),
                 "classification_flip_integration_points": int(np.count_nonzero(legacy_pred != arc_pred)),
                 "evaluated_integration_points": int(legacy_pred.size),
                 "legacy_base_temperature_k": temperature_range(legacy_base),
                 "arcana_base_temperature_k": temperature_range(arc_base)}
    return {"thermal_error_over_1km_lithosphere_grid": stats(all_errors),
            "thermal_error_at_representative_depths": {k: stats(np.asarray(v)) for k,v in point_errors.items()},
            "legacy_fillin_raw_profile_above_temLim_grid_samples": clips,
            "squeez_nodal_thermal_profile_error_over_1km_grid": stats(np.asarray(nodal_t_errors)),
            "squeez_nodal_legacy_temLim_clipping": {"clipped_samples": squeeze_clip_count,
                                                       "sample_count": squeeze_sample_count},
            "squeez_thermal_density_column_integral_difference_legacy_minus_arcana_kg_m2":
                stats_value(np.asarray(squeeze_density_differences)),
            "iConve5_threshold": threshold,
            "onebar": onebar,
            "profile_samples": int(len(all_errors))}


def material_comparison(nodes: np.ndarray, p: dict[str, Any]) -> dict[str, Any]:
    i = IDX
    branch = nodes[:, i["runtime_branch_code"]].astype(int)
    codes = nodes[:, i["crust_material_code"]].astype(int)
    result: dict[str, Any] = {}
    global_crust = p["rhoBar_C_grid_range"]
    for code, name in ((1, "continental_crust"), (2, "oceanic_crust")):
        selected = codes == code
        if not selected.any():
            continue
        key = "crust" if code == 1 else "crust"
        rho = nodes[selected, i["crust_density_kg_m3"]]
        k = nodes[selected, i["crust_conductivity_w_m_k"]]
        alpha = nodes[selected, i["crust_expansivity_k_1"]]
        radio = nodes[selected, i["crust_heat_production_w_m3"]]
        cp = nodes[selected, i["crust_cp_j_kg_k"]]
        result[name] = {"node_count": int(selected.sum()),
            "arcana_values": {"density_kg_m3": sorted(set(map(float,rho))),
                              "conductivity_w_m_k": sorted(set(map(float,k))),
                              "expansivity_k_1": sorted(set(map(float,alpha))),
                              "radiogenic_heat_w_m3": sorted(set(map(float,radio))),
                              "heat_capacity_j_kg_k": sorted(set(map(float,cp)))},
            "legacy_global_density_range_kg_m3": global_crust,
            "legacy_density_difference_range_kg_m3": [float(global_crust[0]-rho[0]),float(global_crust[1]-rho[0])],
            "legacy_conductivity_w_m_k": float(p["conduc"][0]),
            "legacy_alpha_k_1": float(p["alphaT"][0]),
            "legacy_radiogenic_heat_w_m3": float(p["radio"][0]),
            "legacy_heat_capacity": "not represented in ShellSet parameter vector"}
    m = nodes[:, i["mantle_density_kg_m3"]]
    mk = nodes[:, i["mantle_conductivity_w_m_k"]]
    ma = nodes[:, i["mantle_expansivity_k_1"]]
    mr = nodes[:, i["mantle_heat_production_w_m3"]]
    mcp = nodes[:, i["mantle_cp_j_kg_k"]]
    result["mantle_all_nodes"] = {"node_count": int(len(nodes)),
        "arcana_values": {"density_kg_m3": sorted(set(map(float,m))),
                          "conductivity_w_m_k": sorted(set(map(float,mk))),
                          "expansivity_k_1": sorted(set(map(float,ma))),
                          "radiogenic_heat_w_m3": sorted(set(map(float,mr))),
                          "heat_capacity_j_kg_k": sorted(set(map(float,mcp)))},
        "legacy_density_kg_m3": float(p["rhoBar"][1]),
        "legacy_density_difference_range_kg_m3": [float(p["rhoBar"][1]-m.max()),float(p["rhoBar"][1]-m.min())],
        "legacy_conductivity_w_m_k": float(p["conduc"][1]),
        "legacy_alpha_k_1": float(p["alphaT"][1]),
        "legacy_radiogenic_heat_w_m3": float(p["radio"][1]),
        "legacy_heat_capacity": "not represented in ShellSet parameter vector"}
    return result


def run(root: Path, homogeneous_sample: int) -> dict[str, Any]:
    root = root.resolve()
    manifest, records, physical = load_runtime(root)
    mesh = load_canonical_mesh(root)
    params = read_shell_parameters(root)
    triangles = mesh.triangles.astype(np.int64)-1
    tri_nodes = records[triangles]
    branch_sets = [set(row.astype(int)) for row in tri_nodes[:, :, IDX["runtime_branch_code"]]]
    crust_sets = [set(row.astype(int)) for row in tri_nodes[:, :, IDX["crust_material_code"]]]
    categories = {
        "continental_homogeneous": np.asarray([s == {1} for s in branch_sets]),
        "positive_age_ocean_homogeneous": np.asarray([s == {3} for s in branch_sets]),
        "ridge_homogeneous": np.asarray([s == {2} for s in branch_sets]),
        "continent_ocean_mixed": np.asarray([s == {1,2} for s in crust_sets]),
        "ridge_positive_ocean_mixed": np.asarray([2 in s and 3 in s for s in branch_sets]),
    }
    if int(categories["continent_ocean_mixed"].sum()) != 1816:
        raise ValueError("CONTINENT_OCEAN_MIXED_COUNT_MISMATCH")
    if int(categories["ridge_positive_ocean_mixed"].sum()) != 325:
        raise ValueError("RIDGE_POSITIVE_OCEAN_MIXED_COUNT_MISMATCH")
    populations: dict[str, Any] = {}
    for name, mask in categories.items():
        all_ids = np.flatnonzero(mask)
        if not len(all_ids):
            chosen = all_ids
        elif name.endswith("_mixed") or len(all_ids) <= homogeneous_sample:
            chosen = all_ids
        else:
            chosen = all_ids[np.linspace(0, len(all_ids)-1, homogeneous_sample, dtype=int)]
        populations[name] = {"element_population_count": int(len(all_ids)),
                             "sampled_element_count": int(len(chosen)),
                             "sample_rule": "ALL_MIXED" if name.endswith("_mixed") else f"DETERMINISTIC_EVEN_INDEX_{homogeneous_sample}",
                             "diagnostics": evaluate_population(tri_nodes[chosen], params)}
    # Source-faithful node Squeez thermal-density column is available, but full
    # stress anomaly needs exact FEG nodal elevation plus runtime execution.
    all_branch = records[:, IDX["runtime_branch_code"]].astype(int)
    material = material_comparison(records, params)
    physical_hash = sha(root / PHYSICAL_NAME)
    shell_sources = {str(path): sha(root / path) for path in (INPUT, GRID, SHELLS, ORBDATA)}
    decision = "INCONCLUSIVE__SPECIFIC_RUNTIME_METRIC_REQUIRED"
    total_flips = sum(v["diagnostics"]["iConve5_threshold"]["classification_flip_integration_points"]
                      for v in populations.values())
    onebar_branch_flips = sum(v["diagnostics"]["onebar"].get("adiabat_intersection_source_branch_flip_depth_samples", 0)
                              for v in populations.values())
    if total_flips or onebar_branch_flips:
        decision = "LEGACY_COMPATIBILITY_PATH_HAS_MATERIAL_DISCREPANCY__FULL_S1B_OR_ALTERNATIVE_SOLVER_REQUIRED"
    covered = np.zeros(len(triangles), dtype=bool)
    for mask in categories.values():
        covered |= mask
    return {
        "decision": decision,
        "diagnostic_only": True,
        "stock_shellset_execution_modified": False,
        "arcana_marker_enabled": False,
        "input_identity": {"runtime_package_sha256": sha(root/RUNTIME_NAME),
            "runtime_manifest_sha256": sha(root/"R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.json"),
            "physical_field_package_sha256": physical_hash,
            "mesh_normalized_sha256": mesh.normalized_sha256,
            "mesh_node_count": mesh.audit["node_count"],
            "mesh_triangle_count": mesh.audit["triangle_count"],
            "projection_replay_sha256": manifest["projection_replay_sha256"],
            "shellset_source_sha256": shell_sources,
            "physical_field_keys": sorted(physical.files)},
        "population_counts": {name: int(mask.sum()) for name,mask in categories.items()},
        "decision_sensitive_totals": {"iConve5_classification_flipped_integration_points": total_flips,
                                      "onebar_adiabat_intersection_branch_flipped_depth_samples": onebar_branch_flips},
        "ridge_related_any_element_count": int(sum(2 in s for s in branch_sets)),
        "unclassified_element_count": int((~covered).sum()),
        "populations": populations,
        "global_shellset_parameter_values": params,
        "material_difference_vs_global_shellset_parameters": material,
        "mechanical_sensitivity": {
            "squeez_temperature_profile": "SOURCE_FORMULA_PORTED; S1A OrbData writes cooling_curvature=0 and chemical_delta_rho=0",
            "squeez_full_sigZZB_tauZZ": "REQUIRES_UBUNTU_RUNTIME_AB_TEST: exact nodal FEG elevation/loading and runtime execution are not bound in this checkout",
            "squeez_thermal_density_column_integral": "CALCULATED: governed solid-column 1-km trapezoidal density integral difference; excludes water/topographic pressure-reference terms and is not full Squeez stress",
            "onebar_glue": "diagnostic source-default reference calculated; exact model-specific continuum rheology assignment requires FAIR input/model binding",
            "diamnd_viscos_stress": "REQUIRES_UBUNTU_RUNTIME_AB_TEST: strain-rate, stress, active rheology and brittle transition are runtime state",
            "iConve5": "source threshold classification directly compared at sampled IPs"
        },
        "runtime_only_unresolved_tests": [
            "SQUEEZ_SIGZZB_TAUZZ_AB_COMPARISON_WITH_EXACT_FAIR_FEG_ELEVATION",
            "ONEBAR_MODEL_BOUND_GLUE_AND_INTERSECTION_RUNTIME_AB_COMPARISON",
            "DIAMND_VISCOS_STRESS_AND_ZTRANC_RUNTIME_AB_COMPARISON",
            "FAIR_NVHPC_BUILD_AND_SHELLS_EXECUTION"
        ],
        "source_formulas": [
            {"routine":"FillIn","path":str(SHELLS),"lines":"3897-3961","meaning":"IP q/geometry interpolation and quadratic adjustment to tAdiab+gradie*100km"},
            {"routine":"Squeez","path":str(SHELLS),"lines":"9053-9230","meaning":"1-km trapezoidal stress integration, layerwise temperature and MIN(temLim,T)"},
            {"routine":"OneBar","path":str(SHELLS),"lines":"6229-6312","meaning":"1-km midpoint integral; legacy global-depth geothM selection, min with linear adiabat, 200K floor"},
            {"routine":"Diamnd","path":str(SHELLS),"lines":"2250-2885","meaning":"temperature at layer quadrature points, temLim clipping; stress integral requires runtime state"},
            {"routine":"Assign","path":str(ORBDATA),"lines":"579-735","meaning":"S1A writes governed q/geometry, cooling_curvature=0 and chemical_delta_rho=0"},
            {"routine":"iConve=5","path":str(SHELLS),"lines":"4024-4032","meaning":"pulled = (FillIn baseT < 1273 K)"},
            {"routine":"integration_point_shape_functions","path":"external/ShellSet-v1.1.0/src/MOD_Data.f90","lines":"1424-1440","meaning":"seven exact Gaussian integration points"}
        ],
        "limits": [
            "This compares the stock legacy reconstruction against the governed package as numerical fields; it is not ShellSet execution or scientific qualification.",
            "Homogeneous groups are deterministic samples; all classified mixed elements are evaluated.",
            "A missing selected FAIR model binding prevents a compatibility PASS; no arbitrary closeness tolerance is imposed."
        ],
        "preserved_gates": {"PRE_ORBDATA_ready":False,"t0_orbdata_executed":False,
            "shellset_mechanics_authorized":False,"dt_selected":False,"t1_created":False,
            "forward_evolution_authorized":False}
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--homogeneous-sample", type=int, default=128)
    parser.add_argument("--output", type=Path, default=ROOT/"R6_PRE_ORBDATA_S1B_NUMERICAL_ADEQUACY.json")
    args = parser.parse_args()
    report = run(args.root, args.homogeneous_sample)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+"\n", encoding="utf-8")
    print(json.dumps({"decision":report["decision"],"output":str(args.output),
                      "population_counts":report["population_counts"]},sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
