"""Source-linked *normalized* rate-and-state laboratory fault stability.

Analyzes ONE/TWO state published fitted parameters in a massless, quasi-static
spring-slider with Dieterich aging law, steady reference speed v0, and fixed
normal stress. No sigma_eff, elastic stiffness, fault length, physical Earth
rupture probability, or ARCANA T0 fault/material parameter is inferred.

The normalized quantity kappa = K/sigma_n_eff [1/m] is meaningful without
knowing sigma_n_eff; K (Pa/m) is NOT known without an independent source.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np

from experiments.plate58_deforming_explore_v1.g2_g3_rsf_pangaea import (
    AUTHORITY, DOI, SCHEMA as RSF_SCHEMA, ingest_pangaea_table2,
)

SCHEMA = "ARCANA_R6_G2_G3_PANGAEA921284_NORMALIZED_RSF_STABILITY_V1"
SOURCE_SHA256 = "b033466b212db38eff8f12e3119ff4b36188cdd80a5894e2c70dbc0e57463c7d"
DECISION = "EARTH_LAB_NORMALIZED_QUASISTATIC_STABILITY__NO_ARCANA_FAULT_BINDING"

class StabilityInputError(ValueError):
    pass


def need(condition, message):
    if not condition:
        raise StabilityInputError(message)


def real(value, label, *, positive=False):
    try:
        x=float(value)
    except (TypeError, ValueError) as exc:
        raise StabilityInputError("RSF_STABILITY_INVALID_"+label) from exc
    need(math.isfinite(x) and (not positive or x>0),
         "RSF_STABILITY_INVALID_"+label)
    return x


def critical_normalized_stiffness(row):
    """Compute k_crit/sigma_eff [1/m] when fitted law meets scope.

    For one aging state, critical normalized stiffness is max(b-a,0)/Dc.
    For two aging states, the exact massless slider linearized characteristic
    cubic is analyzed by Routh-Hurwitz, *not* an invented effective Dc.
    Parameters with a<=0, b_i<0, or published rounded (a-b)==0 are
    deliberately unqualified for a unique empirical threshold.
    """
    need(isinstance(row,dict) and isinstance(row.get("states"),list) and
         len(row["states"]) in (1,2),"RSF_STABILITY_ONE_OR_TWO_STATES_REQUIRED")
    a=real(row.get("a"),"A")
    states=row["states"]
    b=[real(s.get("b"),"B") for s in states]
    dc=[real(s.get("Dc_m"),"DC",positive=True) for s in states]
    v0=real(row.get("v0_m_s"),"V0",positive=True)
    published=real(row.get("published_a_minus_b"),"SOURCE_A_MINUS_B")
    effective=a-sum(b)
    baseline={"source_line":row.get("source_line"),
       "source_event":row.get("event"),"source_sample":row.get("sample_label"),
       "source_experiment":row.get("experiment"),
       "state_count":len(states),"a_minus_sum_b_computed":effective,
       "a_minus_b_published":published,
       "dc_m":dc,"v0_m_s":v0,
       "critical_K_over_sigma_effective_m_inv":None,
       "critical_K_Pa_per_m":None,
       "physical_fault_stiffness":None,"physical_normal_stress_pa":None,
       "arcana_fault_site_id":None,"physical_instability_predicted":False,
       "model":"MASSLESS_QUASISTATIC_AGING_SPRING_SLIDER_ONLY",
       "source_is_model_extracted_fit_not_raw_instrument":True}
    if a<=0 or any(x<0 for x in b):
        return {**baseline,"qualification":"EXCLUDED_NONPOSITIVE_DIRECT_EFFECT_OR_NEGATIVE_STATE_WEIGHT"}
    if published==0.:
        return {**baseline,"qualification":"EXCLUDED_SOURCE_ROUNDED_ZERO_A_MINUS_B"}
    if published*effective<0:
        return {**baseline,"qualification":"EXCLUDED_PUBLISHED_AND_DERIVED_SIGN_CONFLICT"}
    if effective>=0:
        # For a>0 and b_i>=0, the aging slider is asymptotically stable
        # at every strictly positive normalized elastic stiffness.
        return {**baseline,"qualification":"STABLE_FOR_ANY_POSITIVE_NORMALIZED_STIFFNESS_IN_SURROGATE",
                "critical_K_over_sigma_effective_m_inv":0.}
    if len(states)==1:
        return {**baseline,"qualification":"CRITICAL_STIFFNESS_ONE_STATE_EXACT",
                "critical_K_over_sigma_effective_m_inv":(-effective)/dc[0]}
    # Non-dimensional characteristic in x=lambda*Dc_ref/v0,
    # q=K*Dc_ref/sigma_eff, d_i=Dc_i/Dc_ref:
    # (q+a*x)*(1+d1*x)*(1+d2*x)
    #   - b1*x*(1+d2*x) - b2*x*(1+d1*x) = 0.
    dref=min(dc)
    d1,d2=[d/dref for d in dc]
    b1,b2=b
    c2_const=a*(d1+d2)-b1*d2-b2*d1
    c1_const=effective
    c2_slope=d1*d2
    c1_slope=d1+d2
    c3=a*d1*d2
    # Stability boundary: c2*c1 = c3*q, with c2,c1>0.
    f2=c2_slope*c1_slope
    f1=c2_slope*c1_const+c2_const*c1_slope-c3
    f0=c2_const*c1_const
    roots=np.roots([f2,f1,f0])
    floor=max(0.,-c1_const/c1_slope,-c2_const/c2_slope)
    eligible=[float(z.real) for z in roots
              if abs(float(z.imag))<=1e-8*max(1.,abs(float(z.real)))
              and float(z.real)>floor*(1+1e-9)+1e-14]
    if len(eligible)!=1:
        return {**baseline,"qualification":"EXCLUDED_TWO_STATE_RH_THRESHOLD_NOT_IDENTIFIABLE"}
    q=eligible[0]
    need((c2_slope*q+c2_const)>0 and (c1_slope*q+c1_const)>0,
         "RSF_STABILITY_TWO_STATE_MARGINAL_WRONG_BRANCH")
    return {**baseline,"qualification":"CRITICAL_STIFFNESS_TWO_STATE_ROUTH_HURWITZ",
            "critical_K_over_sigma_effective_m_inv":q/dref,
            "dimensionless_critical_K_Dcref_over_sigma":q}


def roots_at_normalized_stiffness(row, stiffness_over_sigma_m_inv):
    """Only a hypothetical stiffness ratio: not an ARCANA/Earth prediction."""
    qphys=real(stiffness_over_sigma_m_inv,"NORMALIZED_STIFFNESS",positive=True)
    critical=critical_normalized_stiffness(row)
    need(critical["critical_K_over_sigma_effective_m_inv"] is not None,
         "RSF_STABILITY_FIT_NOT_QUALIFIED_FOR_SPECTRUM")
    dc=critical["dc_m"]
    dref=min(dc)
    a=real(row["a"],"A",positive=True)
    weights=[real(s["b"],"B") for s in row["states"]]
    q=qphys*dref
    if len(dc)==1:
        coefficients=[a,a-weights[0]+q,q]
    else:
        d1,d2=[d/dref for d in dc]
        b1,b2=weights
        coefficients=[a*d1*d2,
              q*d1*d2+a*(d1+d2)-b1*d2-b2*d1,
              q*(d1+d2)+a-b1-b2,q]
    modes=np.roots(coefficients)
    real_max=max(float(z.real) for z in modes)
    # The source roundoff and floating-point critical boundary can give
    # near-zero eigenvalues; explicit marginal band instead of false PASS.
    tol=1e-9*max(1.,max(abs(complex(z)) for z in modes))
    classification=("STABLE_FOR_THIS_HYPOTHETICAL_KAPPA" if real_max < -tol
      else "UNSTABLE_FOR_THIS_HYPOTHETICAL_KAPPA" if real_max>tol
      else "MARGINAL_OR_NUMERICALLY_UNRESOLVED")
    return {"classification":classification,"normalized_kappa_m_inv":qphys,
       "dimensionless_q":q,"dimensionless_eigenvalues":
       [[float(z.real),float(z.imag)] for z in modes],
       "maximum_real_part_per_s":real_max*real(row["v0_m_s"],"V0",positive=True)/dref,
       "K_Pa_per_m":None,"sigma_effective_pa":None,
       "actual_earth_or_arcana_fault_stability_assessed":False}


def analyze_model_fit_records(rows):
    need(isinstance(rows,list) and len(rows)>0,
         "RSF_STABILITY_MISSING_SOURCE_ROWS")
    result=[]
    seen=set()
    for row in rows:
        n=row.get("source_line")
        need(isinstance(n,int) and n not in seen,
             "RSF_STABILITY_DUPLICATED_SOURCE_LINE")
        seen.add(n)
        result.append(critical_normalized_stiffness(row))
    summary=Counter(r["qualification"] for r in result)
    vals=[r["critical_K_over_sigma_effective_m_inv"] for r in result
          if r["critical_K_over_sigma_effective_m_inv"] is not None
          and r["critical_K_over_sigma_effective_m_inv"]>0]
    return {"rows":result,
            "inventory":{"fitted_model_rows":len(result),
              "source_row_qualification_counts":dict(sorted(summary.items())),
              "positive_critical_ratio_rows":len(vals),
              "min_positive_critical_K_over_sigma_m_inv":min(vals) if vals else None,
              "max_positive_critical_K_over_sigma_m_inv":max(vals) if vals else None,
              "pressure_values_assigned":0,
              "arcana_faults_assigned":0,
              "independent_experimental_trials_inferred":None}}


def _sha(data):return hashlib.sha256(data).hexdigest()


def build_source_bound_evidence(raw_path:Path, ingest_directory:Path,
                                output:Path):
    """Recompute real input parsing and compare to SHA-certified ingestion.

    Requires prior FAIR INGEST_NEW_02 report and its immutable manifest;
    original raw file is not modified. Output directory MUST NOT exist.
    """
    need(not output.exists(),"RSF_STABILITY_OUTPUT_ALREADY_EXISTS")
    raw=raw_path.read_bytes()
    need(_sha(raw)==SOURCE_SHA256,"RSF_STABILITY_SOURCE_SHA_MISMATCH")
    reread=ingest_pangaea_table2(raw)
    report_path=ingest_directory/"REPORT.json"
    manifest_path=ingest_directory/"MANIFEST.json"
    manifest=json.loads(manifest_path.read_text())
    earlier=json.loads(report_path.read_text())
    need(manifest.get("schema")=="ARCANA_R6_G2_G3_LAB_RSF_EVIDENCE_MANIFEST_V1"
         and manifest.get("no_physical_solve") is True
         and manifest.get("no_T1") is True
         and manifest.get("no_canonical_promotion") is True
         and manifest.get("files",{}).get("REPORT.json")==_sha(report_path.read_bytes())
         and manifest.get("source_sha256")==SOURCE_SHA256,
         "RSF_STABILITY_REPORT_MANIFEST_NOT_SOURCE_BOUND")
    need(earlier.get("schema")==RSF_SCHEMA and earlier.get("authority")==AUTHORITY
         and earlier.get("doi")==DOI and earlier.get("source_sha256")==SOURCE_SHA256
         and earlier.get("fitted_model_rows")==reread["fitted_model_rows"]
         and earlier.get("per_experiment_effective_normal_stress_qualified") is False
         and earlier.get("lab_effective_normal_stress_pa") is None
         and len(earlier["fitted_model_rows"])==66,
         "RSF_STABILITY_REPLAY_SOURCE_ROW_OR_AUTHORITY_DRIFT")
    old_predictions=earlier.get("conditional_lab_velocity_step_predictions")
    need(isinstance(old_predictions,list) and len(old_predictions)==66 and all(
         p.get("immediate_delta_tau_pa") is None and
         p.get("steady_delta_tau_pa") is None and
         p.get("per_experiment_effective_normal_stress_pa") is None
         for p in old_predictions),
         "RSF_STABILITY_OLD_REPORT_UNQUALIFIED_PRESSURE_FORCES")
    check=analyze_model_fit_records(earlier["fitted_model_rows"])
    report={"schema":SCHEMA,"decision":DECISION,
        "source_doi":DOI,"source_sha256":SOURCE_SHA256,
        "ingest_report_sha256":_sha(report_path.read_bytes()),
        "ingest_manifest_sha256":_sha(manifest_path.read_bytes()),
        "stability_surrogate":"MASSLESS_LINEAR_QUASISTATIC_SLIDER_AGING_LAW",
        "stiffness_is_normalized_by_unknown_effective_stress":True,
        "original_source_model_extracted_not_direct_observations":True,
        "lab_pressure_by_experiment":None,
        "elastic_stiffness_of_arcana_fault":None,
        "reference_friction":None,
        "physical_fault_sidedness":None,
        "physical_fault_rupture_or_seismicity_predicted":False,
        **check,
        "mechanical_solve_authorized":False,"physical_T1":None,
        "D_024":"ACTIVE"}
    output.mkdir(parents=True,exist_ok=False)
    out=output/"REPORT.json"
    out.write_text(json.dumps(report,indent=2,allow_nan=False)+"\n")
    (output/"MANIFEST.json").write_text(json.dumps({
       "schema":"ARCANA_R6_G2_G3_NORMALIZED_RSF_STABILITY_MANIFEST_V1",
       "source_sha256":SOURCE_SHA256,
       "ingest_report_sha256":report["ingest_report_sha256"],
       "files":{"REPORT.json":_sha(out.read_bytes())},
       "no_solver_run":True,"no_T1":True,
       "no_canonical_promotion":True
    },indent=2)+"\n")
    return {"decision":DECISION,"summary":check["inventory"],
            "physical_T1":None,"mechanical_solve_authorized":False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--raw",type=Path,required=True)
    p.add_argument("--ingest-dir",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    print(json.dumps(build_source_bound_evidence(a.raw,a.ingest_dir,a.output),indent=2))

if __name__=="__main__":main()
