from __future__ import annotations

from pathlib import Path
from typing import Any
import io
import json
import zipfile

import numpy as np

from .segregation_aware_admixture import qtl_segregation_potential


def _read_effects(zf: zipfile.ZipFile, name: str, axis: int) -> np.ndarray:
    lines = zf.read(name).decode("utf-8").splitlines()
    vals=[]
    for line in lines[1:]:
        if not line.strip():
            continue
        tok=line.split("\t")
        if int(tok[1]) == int(axis):
            vals.append((int(tok[2]), float(tok[3])))
    vals.sort()
    return np.asarray([v for _,v in vals], float)


def _qfreq_final(zf: zipfile.ZipFile, name: str, effects: np.ndarray) -> tuple[np.ndarray,np.ndarray,np.ndarray,np.ndarray]:
    lines=[x.strip() for x in zf.read(name).decode("utf-8").splitlines() if x.strip()]
    if not lines or lines[0].split()[:4] != ["pop","trait","locus","allele"]:
        raise ValueError("unexpected qfreq format")
    pops=sorted({int(x.split()[0]) for x in lines[1:]})
    pidx={p:i for i,p in enumerate(pops)}
    freq=np.full((len(pops),len(effects)),np.nan,float)
    for line in lines[1:]:
        tok=line.split(); pop=int(tok[0]); locus=int(tok[2])-1
        freq[pidx[pop],locus]=float(tok[-1])
    if np.any(~np.isfinite(freq)):
        raise ValueError("incomplete qfreq")
    mean=np.sum(effects[None,:]*(2*freq-1),axis=1)
    va=2*np.sum((effects[None,:]**2)*freq*(1-freq),axis=1)
    s=qtl_segregation_potential(effects[None,:],freq[:,None,:])[:,:,0]
    return freq,mean,va,s


def _cross_group_mean(s: np.ndarray) -> float:
    return float(np.mean([s[i,j] for i in (0,1) for j in (2,3)]))


def _signed_group_divergence(z: np.ndarray) -> float:
    return float(np.mean(z[[2,3]]) - np.mean(z[[0,1]]))


def analyze_r37c_selection_evidence(raw_results_zip: str|Path) -> dict[str,Any]:
    raw=Path(raw_results_zip)
    rows=[]
    reconnect_rows=[]
    with zipfile.ZipFile(raw) as zf:
        suite=json.loads(zf.read("R3_7C_NEMO_SELECTION_SUITE_SUMMARY.json"))
        if suite.get("status") != "NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED":
            raise ValueError("R3.7C selection suite incomplete")
        for rec in suite["records"]:
            if rec.get("status") != "ENGINE_COMPLETED_SELECTION_CHAIN":
                raise ValueError("R3.7C chain incomplete")
            N=int(rec["population_size"]); rep=int(rec["replicate"]); axis=int(rec["axis"])
            sv=float(rec["selection_variance"])
            base=f"selection_variance_{sv:g}/N_{N}/rep_{rep:03d}/axis_{axis}/"
            effects=_read_effects(zf,base+"qtl/qtl_effects.tsv",axis)
            sel=rec["selected_branch"]
            ctl=rec["neutral_branch"]
            _,zs,vas,ss=_qfreq_final(zf,base+sel["fragmented"]["qfreq_relpath"],effects)
            _,zn,van,sn=_qfreq_final(zf,base+ctl["fragmented"]["qfreq_relpath"],effects)
            dz_sel=_signed_group_divergence(zs); dz_ctl=_signed_group_divergence(zn)
            adaptive_dz=dz_sel-dz_ctl
            cross_sel=_cross_group_mean(ss); cross_ctl=_cross_group_mean(sn)
            adaptive_dS=cross_sel-cross_ctl
            keff=(adaptive_dz*adaptive_dz/(2*adaptive_dS)) if adaptive_dS>1e-14 else float("nan")
            direction_ok=adaptive_dz>0
            rows.append({
                "population_size":N,"replicate":rep,"axis":axis,"selection_variance":sv,
                "selected_group_trait_divergence":dz_sel,"neutral_group_trait_divergence":dz_ctl,
                "adaptive_trait_divergence":adaptive_dz,
                "selected_cross_group_S":cross_sel,"neutral_cross_group_S":cross_ctl,
                "adaptive_cross_group_S":adaptive_dS,"K_eff":keff,
                "direction_aligned_with_optima":bool(direction_ok),
                "selected_mean_VA":float(np.mean(vas)),"neutral_mean_VA":float(np.mean(van)),
            })
            _,zsr,_,ssr=_qfreq_final(zf,base+sel["reconnected"]["qfreq_relpath"],effects)
            _,znr,_,snr=_qfreq_final(zf,base+ctl["reconnected"]["qfreq_relpath"],effects)
            excess_before=adaptive_dS
            excess_after=_cross_group_mean(ssr)-_cross_group_mean(snr)
            reconnect_rows.append({
                "population_size":N,"replicate":rep,"axis":axis,"selection_variance":sv,
                "adaptive_cross_group_S_before_reconnection":excess_before,
                "adaptive_cross_group_S_after_reconnection":excess_after,
                "adaptive_S_retention_after_reconnection":excess_after/excess_before if excess_before>1e-14 else float("nan"),
                "selected_group_trait_divergence_after_reconnection":_signed_group_divergence(zsr),
                "neutral_group_trait_divergence_after_reconnection":_signed_group_divergence(znr),
            })
    kvals=np.asarray([r["K_eff"] for r in rows if np.isfinite(r["K_eff"]) and r["K_eff"]>0],float)
    aligned=sum(r["direction_aligned_with_optima"] for r in rows)
    positive=sum(r["adaptive_cross_group_S"]>0 for r in rows)
    if len(kvals) != len(rows) or aligned != len(rows) or positive != len(rows):
        verdict="REVIEW_SELECTION_ORACLE_RESPONSE_INVALID"
    else:
        verdict="PASS_SELECTION_ORACLE_EVIDENCE_COMPLETE__K_EFF_RULE_REVIEW_REQUIRED"
    by_strength={}
    for sv in sorted({r["selection_variance"] for r in rows}):
        a=np.asarray([r["K_eff"] for r in rows if r["selection_variance"]==sv and np.isfinite(r["K_eff"])],float)
        by_strength[str(sv)]={"n":int(a.size),"median":float(np.median(a)),"mean":float(np.mean(a)),"min":float(np.min(a)),"max":float(np.max(a)),"cv":float(np.std(a)/np.mean(a)) if np.mean(a)!=0 else float("nan")}
    by_N={}
    for N in sorted({r["population_size"] for r in rows}):
        a=np.asarray([r["K_eff"] for r in rows if r["population_size"]==N and np.isfinite(r["K_eff"])],float)
        by_N[str(N)]={"n":int(a.size),"median":float(np.median(a)),"mean":float(np.mean(a)),"min":float(np.min(a)),"max":float(np.max(a)),"cv":float(np.std(a)/np.mean(a)) if np.mean(a)!=0 else float("nan")}
    ret=np.asarray([r["adaptive_S_retention_after_reconnection"] for r in reconnect_rows if np.isfinite(r["adaptive_S_retention_after_reconnection"])],float)
    return {
        "schema":"ARCANA_R37C_SELECTION_PARTICIPATION_EVIDENCE_V1","stage":"v0.6D1-R3.7C",
        "verdict":verdict,"observation_count":len(rows),"direction_aligned_count":aligned,"positive_adaptive_S_count":positive,
        "K_eff":{"n":int(kvals.size),"minimum":float(np.min(kvals)) if kvals.size else None,"median":float(np.median(kvals)) if kvals.size else None,"mean":float(np.mean(kvals)) if kvals.size else None,"maximum":float(np.max(kvals)) if kvals.size else None,"cv":float(np.std(kvals)/np.mean(kvals)) if kvals.size and np.mean(kvals)!=0 else None},
        "by_selection_variance":by_strength,"by_population_size":by_N,
        "reconnection_adaptive_S_retention":{"n":int(ret.size),"minimum":float(np.min(ret)) if ret.size else None,"median":float(np.median(ret)) if ret.size else None,"maximum":float(np.max(ret)) if ret.size else None},
        "rows":rows,"reconnection_rows":reconnect_rows,
        "matched_neutral_subtraction_used":True,"free_calibration_parameter_fitted":False,
        "scalar_K_eff_authorized":False,"production_runtime_binding_authorized":False,"canonical_write_allowed":False,
        "interpretation":"R3.7C measures dynamic selection participation. Evidence completion alone does not authorize a scalar K_eff; stability/state-dependence must be reviewed after the real NEMO run.",
    }
