from __future__ import annotations

from pathlib import Path
from typing import Any
import io
import json
import zipfile

import numpy as np

from .nemo242_r37a import canonical_r37a_b2_phases, b2_nemo_transition
from .segregation_aware_admixture import qtl_segregation_potential
from .neutral_reduced_lifecycle import advance_neutral_generations


def _read_tsv_matrix(zf: zipfile.ZipFile, name: str) -> np.ndarray:
    return np.loadtxt(io.StringIO(zf.read(name).decode("utf-8")), delimiter="\t")


def _read_effects(zf: zipfile.ZipFile, name: str, axis: int) -> np.ndarray:
    lines = zf.read(name).decode("utf-8").splitlines()
    out=[]
    for line in lines[1:]:
        if not line.strip():
            continue
        tok=line.split("\t")
        if int(tok[1]) == int(axis):
            out.append((int(tok[2]), float(tok[3])))
    out.sort()
    return np.asarray([v for _,v in out], dtype=float)


def _read_qfreq_final(zf: zipfile.ZipFile, name: str, effects: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray]:
    lines=[x.strip() for x in zf.read(name).decode("utf-8").splitlines() if x.strip()]
    if not lines or lines[0].split()[:4] != ["pop","trait","locus","allele"]:
        raise ValueError("unexpected qfreq format")
    pops=sorted({int(x.split()[0]) for x in lines[1:]})
    pidx={p:i for i,p in enumerate(pops)}
    freq=np.full((len(pops), len(effects)), np.nan, dtype=float)
    for line in lines[1:]:
        tok=line.split(); pop=int(tok[0]); locus=int(tok[2])-1
        freq[pidx[pop],locus]=float(tok[-1])
    if np.any(~np.isfinite(freq)):
        raise ValueError("incomplete qfreq")
    mean=np.sum(effects[None,:]*(2.0*freq-1.0), axis=1)
    va=2.0*np.sum((effects[None,:]**2)*freq*(1.0-freq), axis=1)
    return freq,mean,va


def analyze_r37a_b2_neutral_closure(raw_results_zip: str|Path) -> dict[str,Any]:
    """Compare the parameter-free reduced neutral recursion with real NEMO B2.

    Each NEMO phase is conditioned on its *actual* saved initial qfreq state.
    The reduced model therefore predicts only migration+drift over that phase,
    avoiding contamination by stochastic error accumulated in earlier phases.
    """
    raw=Path(raw_results_zip)
    phase_by_name={p.name:p for p in canonical_r37a_b2_phases()}
    rows=[]
    with zipfile.ZipFile(raw) as zf:
        suite=json.loads(zf.read("R3_7A_NEMO_B2_SUITE_SUMMARY.json"))
        if suite.get("status") != "NEMO_B2_EVIDENCE_COMPLETE_REVIEW_REQUIRED":
            raise ValueError("B2 suite is incomplete")
        for rec in suite["records"]:
            if rec.get("status") != "ENGINE_COMPLETED_B2_CHAIN":
                raise ValueError("B2 chain incomplete")
            N=int(rec["population_size"]); rep=int(rec["replicate"]); axis=int(rec["axis"])
            base=f"N_{N}/rep_{rep:03d}/axis_{axis}/"
            effects=_read_effects(zf, base+"qtl/qtl_effects.tsv", axis)
            for pi, phase_rec in enumerate(rec["phases"]):
                pname=phase_rec["phase"]; phase=phase_by_name[pname]
                pbase=base+f"phase_{pi:02d}_{pname}/"
                f0=_read_tsv_matrix(zf,pbase+"initial_allele_frequencies.tsv")
                if f0.ndim == 1: f0=f0[None,:]
                va0=2.0*np.sum((effects[None,:]**2)*f0*(1.0-f0), axis=1)[:,None]
                s0=qtl_segregation_potential(effects[None,:],f0[:,None,:])
                pred=advance_neutral_generations(
                    va0,s0,b2_nemo_transition(phase.exchange_matrix),float(N),int(phase.transitions)
                )
                qname=pbase+phase_rec["qfreq_file"]
                ff,_,vao=_read_qfreq_final(zf,qname,effects)
                so=qtl_segregation_potential(effects[None,:],ff[:,None,:])
                tri=np.triu_indices(so.shape[0],1)
                pmeanS=float(np.mean(pred.segregation_potential[:,:,0][tri]))
                omeanS=float(np.mean(so[:,:,0][tri]))
                pmeanVA=float(np.mean(pred.va_within[:,0])); omeanVA=float(np.mean(vao))
                rows.append({
                    "population_size":N,"replicate":rep,"axis":axis,"phase":pname,
                    "transitions":int(phase.transitions),
                    "predicted_mean_pair_S":pmeanS,"observed_mean_pair_S":omeanS,
                    "observed_over_predicted_S":omeanS/max(pmeanS,1e-300),
                    "predicted_mean_VA":pmeanVA,"observed_mean_VA":omeanVA,
                    "VA_fractional_error":(omeanVA-pmeanVA)/max(pmeanVA,1e-300),
                    "predicted_max_S":float(np.max(pred.segregation_potential)),
                    "observed_max_S":float(np.max(so)),
                })
    ratios=np.asarray([r["observed_over_predicted_S"] for r in rows],float)
    vaerr=np.asarray([r["VA_fractional_error"] for r in rows],float)
    phase_summary={}
    for pname in phase_by_name:
        rr=np.asarray([r["observed_over_predicted_S"] for r in rows if r["phase"]==pname],float)
        ee=np.asarray([abs(r["VA_fractional_error"]) for r in rows if r["phase"]==pname],float)
        phase_summary[pname]={
            "n":int(rr.size),"median_S_ratio":float(np.median(rr)),"mean_S_ratio":float(np.mean(rr)),
            "median_abs_VA_fractional_error":float(np.median(ee)),
        }
    n_summary={}
    for N in sorted({r["population_size"] for r in rows}):
        rr=np.asarray([r["observed_over_predicted_S"] for r in rows if r["population_size"]==N],float)
        ee=np.asarray([abs(r["VA_fractional_error"]) for r in rows if r["population_size"]==N],float)
        n_summary[str(N)]={
            "n":int(rr.size),"median_S_ratio":float(np.median(rr)),"mean_S_ratio":float(np.mean(rr)),
            "median_abs_VA_fractional_error":float(np.median(ee)),
        }
    # These are evidence-review tolerances, not World-1 physical constants.
    supports=(
        0.80 <= float(np.median(ratios)) <= 1.20
        and float(np.min(ratios)) >= 0.50 and float(np.max(ratios)) <= 1.50
        and float(np.median(np.abs(vaerr))) <= 0.05
        and float(np.max(np.abs(vaerr))) <= 0.10
    )
    return {
        "schema":"ARCANA_R37B_NEMO_B2_NEUTRAL_CLOSURE_V1","stage":"v0.6D1-R3.7B",
        "verdict":"PASS_NEUTRAL_S_LIFECYCLE_SUPPORTED_BY_NEMO_B2" if supports else "REVIEW_NEUTRAL_S_LIFECYCLE_MISMATCH",
        "raw_evidence_status":"NEMO_B2_EVIDENCE_COMPLETE_REVIEW_REQUIRED",
        "phase_observation_count":len(rows),
        "S_observed_over_predicted":{
            "minimum":float(np.min(ratios)),"median":float(np.median(ratios)),"mean":float(np.mean(ratios)),"maximum":float(np.max(ratios)),
        },
        "VA_fractional_error":{
            "median_abs":float(np.median(np.abs(vaerr))),"mean_abs":float(np.mean(np.abs(vaerr))),"maximum_abs":float(np.max(np.abs(vaerr))),
        },
        "by_phase":phase_summary,"by_population_size":n_summary,"rows":rows,
        "free_calibration_parameter_fitted":False,
        "selection_enabled_in_b2":False,
        "selection_participation_K_eff_authorized":False,
        "interpretation":"B2 independently supports the neutral migration+drift closure of (VA_within,S). It cannot authorize directional-selection K_eff because NEMO selection was disabled.",
        "canonical_write_allowed":False,"production_runtime_binding_authorized":False,
    }
