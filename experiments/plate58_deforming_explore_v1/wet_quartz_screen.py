"""Source-bound P/T *screen* for alternate wet-quartz research, not a flow law.

The temperature window comes from Tokle et al. (2019) compiled wet-quartzite
experiments, while pressure group labels come from a DIFFERENT 2021
natural/experimental calibration. Their intersection is a triage measure only,
not empirical joint validation or authority to assign a material.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path

from experiments.plate58_deforming_explore_v1.check import verify as verify_stage
from experiments.plate58_deforming_explore_v1.prepare import _json, require, sha
from experiments.plate58_deforming_explore_v1.rheology_envelope import (
    STATUS as G2_STATUS, lithostatic_proxy_pa,
)

STATUS = "PASS_G2_ALTERNATE_WET_QUARTZ_PT_SCREEN__WATER_UNRESOLVED"
SCHEMA = "ARCANA_R6_PLATE58_ALTERNATE_QUARTZ_PT_SCREEN_V1"
WET_EXP_TEMPERATURE_WINDOW_K = (973.15, 1473.15)  # 700–1200 Celsius
LOW_PRESSURE_UPPER_EXCLUSIVE_PA = 560e6
HIGH_PRESSURE_LOWER_INCLUSIVE_PA = 700e6
HIGH_PRESSURE_UPPER_INCLUSIVE_PA = 1600e6


def screen_pt(temperature_k: float, lithostatic_pressure_pa: float) -> dict:
    """Cross-study screening labels, NOT a flow-law validity decision."""
    t = float(temperature_k)
    p = float(lithostatic_pressure_pa)
    require(math.isfinite(t) and t > 0 and math.isfinite(p) and p >= 0,
            "NONFINITE_OR_NONPHYSICAL_PT_SCREEN_INPUT")
    temp_in = WET_EXP_TEMPERATURE_WINDOW_K[0] <= t <= WET_EXP_TEMPERATURE_WINDOW_K[1]
    if p < LOW_PRESSURE_UPPER_EXCLUSIVE_PA:
        group = "LOW_LT_560MPA"
    elif HIGH_PRESSURE_LOWER_INCLUSIVE_PA <= p <= HIGH_PRESSURE_UPPER_INCLUSIVE_PA:
        group = "HIGH_700_TO_1600MPA"
    elif p < HIGH_PRESSURE_LOWER_INCLUSIVE_PA:
        group = "BETWEEN_REPORTED_PRESSURE_GROUPS"
    else:
        group = "ABOVE_REPORTED_PRESSURE_GROUPS"
    return {
        "temperature_in_Tokle2019_wet_experiment_window": temp_in,
        "pressure_group_in_2021_calibration": group,
        "cross_study_PT_window_overlap_for_screen_only":
            temp_in and group in ("LOW_LT_560MPA", "HIGH_700_TO_1600MPA"),
        "field_water_fugacity_known": False,
        "constitutive_law_validated": False,
    }


def scan(stage_dir: Path, g2_dir: Path, output: Path):
    require(not output.exists(), "OUTPUT_ALREADY_EXISTS")
    verify_stage(stage_dir)
    stage = json.loads((stage_dir/"CASE.json").read_text())
    require(not stage["readiness"]["mechanical_solve_authorized"] and
            stage["physical_deforming_t1"] is None, "SOURCE_STAGE_SOLVE_UNEXPECTED")
    manifest = json.loads((g2_dir/"MANIFEST.json").read_text())
    g2path = g2_dir/"G2_ENVELOPE.json"
    require(manifest["status"] == G2_STATUS and manifest["no_solver_run"]
            and manifest["no_T1"] and manifest["no_canonical_promotion"]
            and manifest["files"] == {"G2_ENVELOPE.json": sha(g2path)},
            "G2_SOURCE_MANIFEST_INVALID")
    g2 = json.loads(g2path.read_text())
    require(g2["status"] == G2_STATUS and
            g2["stage_case_sha256"] == manifest["prior_stage_case_sha256"]
            == sha(stage_dir/"CASE.json") and
            g2["mechanical_solve_authorized"] is False and
            g2["total_node_crust_T_samples"] == 81 and
            g2["total_node_crust_lab_T_window_samples"] == 0,
            "G2_FAIR_RESULT_OR_SOURCE_CHANGED")
    g2nodes = {int(row["parent_node_id"]): row for row in g2["source_pre_nodes"]}
    stage_nodes = {int(row["parent_id"]): row for row in stage["parent_node_PRE"]}
    require(len(g2nodes) == len(stage_nodes) == 9 and
            set(g2nodes) == set(stage_nodes), "G2_SOURCE_NODE_JOIN_MISMATCH")

    node_reports = []
    totals = Counter()
    min_t = math.inf
    max_t = -math.inf
    for parent in sorted(stage_nodes):
        pre = stage_nodes[parent]["PRE"]
        record = g2nodes[parent]
        depths = list(record["crust_sample_depths_m"])
        temps = list(record["crust_sample_temperature_k"])
        require(len(depths) == len(temps) == 9, "CRUST_SAMPLING_CHANGED")
        samples = []
        for z, t in zip(depths, temps, strict=True):
            z, t = float(z), float(t)
            p = lithostatic_proxy_pa(pre,z)
            label = screen_pt(t,p)
            totals["temperature_in_wet_experiment_window" if label[
                "temperature_in_Tokle2019_wet_experiment_window"] else
                "temperature_outside_wet_experiment_window"] += 1
            totals["pressure_" + label["pressure_group_in_2021_calibration"]] += 1
            if label["cross_study_PT_window_overlap_for_screen_only"]:
                totals["cross_study_overlap"] += 1
            min_t = min(min_t,t)
            max_t = max(max_t,t)
            samples.append({
                "depth_m":z,
                "PRE_temperature_k":t,
                "PRE_lithostatic_proxy_pa":p,
                **label,
            })
        node_reports.append({
            "parent_node_id":parent,
            "local_node_id":stage_nodes[parent]["local_id"],
            "samples":samples,
        })
    require(totals["temperature_in_wet_experiment_window"] +
            totals["temperature_outside_wet_experiment_window"] == 81,
            "PT_SCREEN_INVENTORY_INVALID")
    report = {
        "schema":SCHEMA, "status":STATUS,
        "scope":"CROSS_STUDY_PT_ELIGIBILITY_SCREEN_ONLY__NOT_LAW_VALIDATION",
        "source_stage_case_sha256":sha(stage_dir/"CASE.json"),
        "source_g2_report_sha256":sha(g2path),
        "literature_anchors":{
            "GT1995":"doi:10.1016/0040-1951(95)00011-B; G2 prior 0/81 in 900–1100C",
            "wet_quartz_experimental_T":"Tokle et al. (2019), doi:10.1016/j.epsl.2018.10.017; aggregated experimental range 700–1200C",
            "2021_pressure_grouping":"Natural and Experimental Constraints on a Flow Law for Dislocation-Dominated Creep in Wet Quartz, doi:10.1029/2020JB021302; <560MPa versus 700–1600MPa groups",
            "cross_study_warning":"Temperature and pressure ranges originate from distinct aggregations; their intersection is NOT an empirically validated flow law domain",
        },
        "screen_bounds":{
            "wet_quartz_experimental_temperature_k":list(WET_EXP_TEMPERATURE_WINDOW_K),
            "low_pressure_less_than_pa":LOW_PRESSURE_UPPER_EXCLUSIVE_PA,
            "high_pressure_inclusive_pa":[HIGH_PRESSURE_LOWER_INCLUSIVE_PA,
                                          HIGH_PRESSURE_UPPER_INCLUSIVE_PA],
        },
        "crust_sample_count":81,
        "minimum_PRE_temperature_k":min_t,
        "maximum_PRE_temperature_k":max_t,
        "counts":dict(sorted(totals.items())),
        "nodes":node_reports,
        "GT1995_temperature_samples_within_lab_window":0,
        "water_or_fugacity_known":False,
        "brittle_friction_and_pore_pressure_known":False,
        "full_depth_integrated_strength_validated":False,
        "G2_effective_constitutive_closure":None,
        "G3_external_continuation":None,
        "G3_basal_normal_support":None,
        "mechanical_solve_authorized":False,
        "solver_runs":0,
        "first_deforming_T1":None,
        "conclusion":"A PT cross-study overlap is not proof of a constitutive law; missing water, material identity, pressure normalization and brittle law prevent physical G2 closure",
    }
    output.mkdir(parents=True)
    (output/"PT_SCREEN.json").write_bytes(_json(report))
    (output/"MANIFEST.json").write_bytes(_json({
        "schema":"ARCANA_R6_PLATE58_WET_QUARTZ_PT_SCREEN_MANIFEST_V1",
        "status":STATUS,
        "source_stage_case_sha256":report["source_stage_case_sha256"],
        "source_g2_report_sha256":report["source_g2_report_sha256"],
        "files":{"PT_SCREEN.json":sha(output/"PT_SCREEN.json")},
        "no_solver_run":True,"no_T1":True,"no_canonical_promotion":True,
    }))
    return report


if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage_dir",type=Path)
    p.add_argument("prior_g2_dir",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    result=scan(a.stage_dir,a.prior_g2_dir,a.output)
    print(json.dumps({
        "status":result["status"],"crust_samples":result["crust_sample_count"],
        "min_temperature_k":result["minimum_PRE_temperature_k"],
        "max_temperature_k":result["maximum_PRE_temperature_k"],
        "counts":result["counts"],
        "water_or_fugacity_known":False,
        "G2_effective_constitutive_closure":None,
        "mechanical_solve_authorized":False,
    },indent=2))
