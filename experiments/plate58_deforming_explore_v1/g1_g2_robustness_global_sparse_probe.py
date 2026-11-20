"""R6 robustness sweep + 12-plate global sparse feasibility: ENGINEERING ONLY.

Regional: run the *existing genuine source-bound* 8x8/16x16 manufactured
G1<->G2 solver under controlled synthetic parameter changes.
Global: sparse graph preconditioned toy solve on all authentic plate-local
views. Its Laplacian is NOT the G2 spherical FEM or global deformation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from unittest.mock import patch

import numpy as np

from experiments.plate58_deforming_explore_v1 import g1_g2_manufactured_feedback as fb

STATUS = "PASS_REGIONAL_ENGINEERING_PARAMETER_ROBUSTNESS_AND_GLOBAL_SPARSE_GRAPH_PROBE__PHYSICS_OPEN"
SCHEMA = "ARCANA_R6_G1_G2_ROBUSTNESS_GLOBAL_SPARSE_PROBE_V1"
BASE = {
    "ETA_CRUST_PA_S": 1e20, "ETA_MANTLE_PA_S": 1e21,
    "TAU_YEARS": 200., "DASHPOT_TO_MEAN_TANGENT": .5
}
SCENARIOS = {
    "baseline": {},
    "uniform_viscosity_x10": {"ETA_CRUST_PA_S": 1e21, "ETA_MANTLE_PA_S": 1e22},
    "crust_viscosity_x10": {"ETA_CRUST_PA_S": 1e21},
    "mantle_viscosity_x10": {"ETA_MANTLE_PA_S": 1e22},
    "relaxation_half": {"TAU_YEARS": 100.},
    "relaxation_double": {"TAU_YEARS": 400.},
    "drive_dashpot_half": {"DASHPOT_TO_MEAN_TANGENT": .25},
    "drive_dashpot_double": {"DASHPOT_TO_MEAN_TANGENT": 1.},
}


def require(condition, code):
    if not condition:
        raise ValueError(code)


def sha(path: Path) -> str:
    with path.open("rb") as fh:
        return hashlib.file_digest(fh, "sha256").hexdigest()


def scenario_parameters(overrides):
    require(set(overrides).issubset(BASE), "ROBUSTNESS_UNKNOWN_PARAMETER")
    params = {**BASE, **overrides}
    require(all(math.isfinite(float(x)) and float(x) > 0
                for x in params.values()), "ROBUSTNESS_INVALID_PARAMETER")
    return params


def compare_regional(baseline, outcomes):
    base={s["extent"]:s for s in baseline["scales"]}
    require(set(base)=={8,16}, "ROBUSTNESS_EXPECTED_SOURCE_SCALES_MISSING")
    output={}
    for key,record in outcomes.items():
        items={}
        for item in record["scales"]:
            extent=item["extent"]
            ref=base[extent]
            require(extent not in items and
                    item["source_nodes"]==ref["source_nodes"] and
                    item["source_triangles"]==ref["source_triangles"],
                    "ROBUSTNESS_REGION_SOURCE_DRIFT")
            per_year={}
            for horizon in ("100","1000"):
                r=item["results"][horizon]
                b=ref["results"][horizon]
                a=float(r["max_displacement_m"])
                delta=a-float(b["max_displacement_m"])
                f=float(r["coupled_minus_g1_velocity_rms_m_per_year"])
                require(math.isfinite(a) and math.isfinite(delta) and
                        math.isfinite(f) and
                        r["manufactured_internal_force_balance_relative"]<1e-9,
                        "ROBUSTNESS_NONFINITE_OR_UNBALANCED_SOLUTION")
                per_year[horizon]={
                    "maximum_displacement_m":a,
                    "delta_max_displacement_vs_baseline_m":delta,
                    "rms_feedback_speed_m_per_year":f,
                    "relative_implicit_force_balance":
                        r["manufactured_internal_force_balance_relative"],
                    "max_area_J_minus_one":
                        r["area_and_mass"]["max_absolute_area_ratio_minus_one"],
                }
            items[str(extent)]=per_year
        require(set(items)=={"8","16"}, "ROBUSTNESS_SCALE_MISSING")
        output[key]=items
    invariant=output["uniform_viscosity_x10"]
    max_delta=max(abs(invariant[k][h]["delta_max_displacement_vs_baseline_m"])
                  for k in ("8","16") for h in ("100","1000"))
    require(max_delta < 1e-7,
            "ROBUSTNESS_UNIFORM_VISCOSITY_SCALE_NONINVARIANCE")
    return {
        "experiments":output,
        "uniform_scale_displacement_difference_m":max_delta,
        "uniform_scale_nonidentifiability_confirmed":True,
        "interpretation":"K and C scale together, so the absolute common viscosity scale is not identifiable in this manufactured model; no ARCANA viscosity calibrated."
    }


def subyear_exact_check():
    """Independent scalar constant-drive ODE check at 1, 1/2, 1/4 year."""
    lam=np.array([.2,2.])
    q=np.eye(2)
    driver=np.array([.1,.05])
    tau=200.
    horizon=100.
    exact=driver*tau/lam*(-np.expm1(-lam*horizon/(tau*(1+lam))))
    errors={}
    for dt in (1.,.5,.25):
        steps=int(round(horizon/dt))
        g=np.tile(driver,(steps,1))
        a=fb.evolve_modes(lam,q,g,dt,tau_years=tau)
        errors[str(dt)]=float(np.linalg.norm(a["final_modes"]-exact))
        require(a["max_balance_relative"]<1e-12 and
                a["max_backward_euler_energy_identity_relative"]<1e-11,
                "ROBUSTNESS_EXACT_ODE_BALANCE_FAILED")
    p1=math.log(errors["1.0"]/errors["0.5"],2)
    p2=math.log(errors["0.5"]/errors["0.25"],2)
    require(errors["0.25"]<errors["0.5"]<errors["1.0"] and
            .85<p1<1.15 and .85<p2<1.15,
            "ROBUSTNESS_SUBYEAR_FIRST_ORDER_NOT_OBSERVED")
    return {
        "independent_constant_drive_analytical_reference":True,
        "model":"TWO_MANUFACTURED_EIGENMODES_NOT_REGIONAL_SOURCE",
        "errors_m_by_dt_years":errors,
        "estimated_order_1_to_half":p1,
        "estimated_order_half_to_quarter":p2,
    }


def sparse_graph_operator(views, source_triangle_count):
    """Global plate-local graph ONLY, preserving splits at shared contacts."""
    from scipy import sparse
    ordered=sorted(views)
    offsets={}
    n=0
    triangle_total=0
    pairs=[]
    for plate in ordered:
        v=views[plate]
        coords=np.asarray(v["ids"],dtype=np.int64)
        tri=np.asarray(v["triangles"],dtype=np.int64)
        require(len(coords)>0 and tri.ndim==2 and tri.shape[1]==3
                and np.all((tri>=0)&(tri<len(coords))),
                "GLOBAL_SPARSE_INVALID_PLATE_LOCAL_TOPOLOGY")
        offsets[plate]=n
        triangle_total+=len(tri)
        for i,j in ((0,1),(1,2),(2,0)):
            pairs.append(tri[:,[i,j]]+n)
        n+=len(coords)
    require(triangle_total==source_triangle_count,
            "GLOBAL_SPARSE_TRIANGLE_COVERAGE_FAILED")
    edges=np.concatenate(pairs,axis=0)
    require(n>0 and len(edges)>0,"GLOBAL_SPARSE_EMPTY_GRAPH")
    a,b=edges.T
    degree=np.bincount(np.r_[a,b],minlength=n)
    rr=np.r_[a,b,np.arange(n)]
    cc=np.r_[b,a,np.arange(n)]
    vv=np.r_[-np.ones(2*len(edges)),degree.astype(float)]
    lap=sparse.coo_matrix((vv,(rr,cc)),shape=(n,n)).tocsr()
    lap.sum_duplicates()
    require(lap.shape==(n,n) and not np.any(~np.isfinite(lap.data)),
            "GLOBAL_SPARSE_GRAPH_INVALID")
    return lap,triangle_total


def global_sparse_probe(root):
    """One real-size sparse graph algebra probe, NOT full global G1<->G2."""
    from scipy import sparse
    from scipy.sparse.linalg import cg
    from experiments.global_t0_kinematic_baseline_v1.benchmark import (
        source_inputs,build_views, NODES, TRIANGLES, PLATES, usage)
    mesh, omegas, pins, horizon, pre=source_inputs(root)
    views=build_views(mesh)
    require(len(views)==len(PLATES)==12 and
            horizon>1000 and len(omegas)==12,
            "GLOBAL_SPARSE_G1_SOURCE_SCOPE_INVALID")
    graph, counted=sparse_graph_operator(views,TRIANGLES)
    n=graph.shape[0]
    require(n==66435 and counted==TRIANGLES and NODES==64442,
            "GLOBAL_SPARSE_SOURCE_VIEW_COUNTS_CHANGED")
    two_dof=2*n
    dense_bytes=two_dof*two_dof*8
    require(dense_bytes>100_000_000_000,
            "GLOBAL_SPARSE_DENSE_MEMORY_ESTIMATE_CHANGED")
    # Unit-free, artificial Laplacian and regularizing identity, NOT G2 physics.
    operator=sparse.eye(n,format="csr")+0.05*graph
    rhs=np.sin(np.arange(n,dtype=float)*0.031)+np.cos(np.arange(n)*.007)
    iterations=[0]
    def callback(_):
        iterations[0]+=1
    result,info=cg(operator,rhs,rtol=1e-9,atol=0.,maxiter=500,
                   callback=callback)
    residual=float(np.linalg.norm(operator@result-rhs)/
                   np.linalg.norm(rhs))
    require(info==0 and residual<1e-8 and
            np.all(np.isfinite(result)), "GLOBAL_SPARSE_CG_DID_NOT_CONVERGE")
    csr_bytes=operator.data.nbytes+operator.indices.nbytes+operator.indptr.nbytes
    # Memory estimate for two independent EN components; no 2N dense K.
    return {
        "status":"PASS_GLOBAL_SOURCE_TOPOLOGY_SPARSE_GRAPH_AND_ONE_CG_SOLVE",
        "parent_nodes":NODES,"source_triangles":TRIANGLES,
        "source_plates":len(PLATES),
        "source_plate_local_views":n,"EN_dofs":two_dof,
        "dense_EN_matrix_bytes_avoided":dense_bytes,
        "dense_EN_matrix_gib":dense_bytes/2**30,
        "one_component_CSR_bytes":int(csr_bytes),
        "two_uncoupled_components_CSR_estimated_bytes":int(2*csr_bytes),
        "graph_nnz":int(graph.nnz),
        "cg_iterations":iterations[0],
        "cg_relative_residual":residual,
        "rss_probe":usage(),
        "source_sha256":pins,
        "note":"GLOBAL GRAPH LAPLACIAN + IDENTITY IS NUMERICAL SCALING PROBE ONLY; NOT SPHERICAL FEM, G2 CONSTITUTIVE, ACTUAL GLOBAL FORCE OR 1000-YEAR GLOBAL COUPLING",
        "global_manufactured_feedback_1000y_executed":False,
        "physical_solver_runs":0,"physical_T1":None,
    }


def execute(multiscale,nodal,g1_audit,output,root):
    require(not output.exists(),"ROBUSTNESS_OUTPUT_EXISTS")
    require(multiscale.is_dir() and nodal.is_dir() and g1_audit.is_dir(),
            "ROBUSTNESS_SOURCE_EVIDENCE_DIR_MISSING")
    output.mkdir(parents=True,exist_ok=False)
    outcomes={}
    for name,overrides in SCENARIOS.items():
        params=scenario_parameters(overrides)
        with patch.multiple(fb,**params):
            result=fb.run(multiscale,nodal,g1_audit,output/name,root)
        require(result["status"]==fb.STATUS and
                result["physical_solver_runs"]==0 and
                result["physical_T1"] is None,
                "ROBUSTNESS_SYNTHETIC_RUN_UNEXPECTED")
        outcomes[name]=result
    comparisons=compare_regional(outcomes["baseline"],outcomes)
    exact=subyear_exact_check()
    global_probe=global_sparse_probe(root)
    report={
        "schema":SCHEMA,"status":STATUS,
        "source_authority":"ENGINEERING_ONLY_NO_GEOLOGICAL_CALIBRATION",
        "scenarios":{k:scenario_parameters(v) for k,v in SCENARIOS.items()},
        "regional_sensitivity":comparisons,
        "subyear_independent_exact_kernel":exact,
        "global_sparse_probe":global_probe,
        "global_full_G2_P1_FEM_time_evolution":None,
        "physical_material_rheology":None,"natural_G3_forces":None,
        "contact_opening_and_slip":None,
        "physical_solver_runs":0,"physical_T1":None,"D_024":"ACTIVE",
        "history_store_modified":False,
    }
    p=output/"ROBUSTNESS_GLOBAL_REPORT.json"
    p.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    manifest={
        "schema":"ARCANA_R6_G1_G2_ROBUSTNESS_GLOBAL_MANIFEST_V1",
        "status":STATUS,
        "files":{"ROBUSTNESS_GLOBAL_REPORT.json":sha(p)},
        "scenario_manifest_sha256":{name:sha(output/name/"MANIFEST.json")
                                    for name in SCENARIOS},
        "no_physical_solver_run":True,"no_T1":True,
        "no_canonical_promotion":True,
    }
    (output/"MANIFEST.json").write_text(json.dumps(manifest,indent=2)+"\n")
    return {
        "status":STATUS,
        "regional_scenarios":list(SCENARIOS),
        "uniform_viscosity_invariance_max_m":
            comparisons["uniform_scale_displacement_difference_m"],
        "exact_subyear_order":
            [exact["estimated_order_1_to_half"],
             exact["estimated_order_half_to_quarter"]],
        "global_sparse":{k:global_probe[k] for k in (
            "source_plate_local_views","EN_dofs","dense_EN_matrix_gib",
            "one_component_CSR_bytes","graph_nnz","cg_iterations",
            "cg_relative_residual")},
        "report":str(p),"physical_solver_runs":0,"physical_T1":None,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--multiscale",type=Path,required=True)
    p.add_argument("--nodal",type=Path,required=True)
    p.add_argument("--g1-audit",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    p.add_argument("--root",type=Path,
                   default=Path(__file__).resolve().parents[2])
    a=p.parse_args()
    print(json.dumps(execute(a.multiscale,a.nodal,a.g1_audit,
                             a.output,a.root),indent=2))


if __name__=="__main__":
    main()
