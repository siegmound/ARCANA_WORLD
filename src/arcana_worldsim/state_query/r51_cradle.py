from __future__ import annotations
from collections import deque
from pathlib import Path
from typing import Any
import hashlib, json
import numpy as np

STAGE="v0.6D1-R5.1"
J14_REL=Path("outputs/v0_6D1_R4_30/authority/R4_30_J14_SPATIAL_AUTHORITY_REPLAY_CANDIDATE.npz")
J14_SEAL_REL=Path("outputs/v0_6D1_R4_31/authority/R4_31_J14_SPATIAL_AUTHORITY_VALIDATION_SEAL.json")
R327_REL=Path("outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz")
R327_CP_REL=Path("outputs/v0_6D1_R3_27/R3_27_HUMAN_200KA_CHECKPOINT.json")
R314_SEAL_REL=Path("outputs/v0_6D1_R3_14/FORMAL_AUDIT_SEALED_v0_6D1_R3_14.json")
R50_SEAL_REL=Path("outputs/v0_6D1_R5_0/R5_0_FINAL_SEAL.json")
CANDIDATES=("RPT_010_D02","RPT_009_D02")
EXPECTED_J14_SHA="eed2d1e350783f1d2dc31c5b7e697330ccbfcf63024062bc9f4ed2f8905f4756"
EXPECTED_J14_SEAL_SHA="f5ffc12524f0ebcd09540030b37b4264b19d538688d473068fb75a892ee95467"
EXPECTED_R327_SHA="fac973bd233c49facedb2d32e1c561800e65e27da1e940f967d680a36c1b47f3"
EXPECTED_R327_CP_SHA="9c86712ce6056515a6bfe5c25c7d382be0ccb707e92e8e0817bd6561bbbe35f9"
EXPECTED_R314_SEAL_SHA="4a97e2c5aa7e0d7583aff89b3507bbe9555abe151aec96ed1667045080a468f0"
EXPECTED_R50_SEAL_SHA="c37ac6684808fe6817ca07cb712e3ef814c0aeb08d1b83647cb6aae07ca801be"
THRESHOLD_QUANTILES=(0.90,0.95,0.975,0.99)

class R51Error(RuntimeError): pass

def sha256_file(p:Path)->str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for c in iter(lambda:f.read(1024*1024),b""): h.update(c)
    return h.hexdigest()

def load_json(p:Path)->Any: return json.loads(p.read_text(encoding="utf-8"))
def write_json(p:Path,o:Any)->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+"\n",encoding="utf-8")

def _components(mask:np.ndarray)->list[list[tuple[int,int]]]:
    nr,nc=mask.shape; seen=np.zeros_like(mask,bool); out=[]
    for r in range(nr):
        for c in range(nc):
            if not mask[r,c] or seen[r,c]: continue
            q=deque([(r,c)]); seen[r,c]=True; cells=[]
            while q:
                a,b=q.popleft(); cells.append((a,b))
                for aa,bb in ((a-1,b),(a+1,b),(a,(b-1)%nc),(a,(b+1)%nc)):
                    if 0<=aa<nr and mask[aa,bb] and not seen[aa,bb]:
                        seen[aa,bb]=True; q.append((aa,bb))
            out.append(cells)
    return out

def validate_authority(root:Path, allow_non_scientific_dev:bool=False)->dict[str,Any]:
    root=Path(root); checks={}
    paths={"r50":root/R50_SEAL_REL,"j14":root/J14_REL,"j14seal":root/J14_SEAL_REL,"r327":root/R327_REL,"r327cp":root/R327_CP_REL,"r314":root/R314_SEAL_REL}
    for k,p in paths.items(): checks[f"present::{k}"]=p.is_file()
    strict=not allow_non_scientific_dev
    if paths["r50"].is_file():
        d=load_json(paths["r50"])
        checks["r50_sealed_semantics"]=(d.get("sealed") is True and d.get("status")=="PASS_R50_SELECTIVE_HIGH_RESOLUTION_NESTED_REPLAY_AND_ARBITRARY_AGE_STATE_QUERY_SEALED" and (d.get("summary") or {}).get("canonical_state_changed") is False and (d.get("summary") or {}).get("derived_refinement_promoted_to_canon") is False)
        checks["r50_exact_hash"]=(sha256_file(paths["r50"])==EXPECTED_R50_SEAL_SHA) if strict else True
    else: checks["r50_sealed_semantics"]=checks["r50_exact_hash"]=False
    checks["j14_exact_hash"]=(paths["j14"].is_file() and sha256_file(paths["j14"])==EXPECTED_J14_SHA) if strict else paths["j14"].is_file()
    checks["j14_seal_exact_hash"]=(paths["j14seal"].is_file() and sha256_file(paths["j14seal"])==EXPECTED_J14_SEAL_SHA) if strict else paths["j14seal"].is_file()
    if paths["j14seal"].is_file():
        js=load_json(paths["j14seal"]); checks["j14_seal_semantics"]=(js.get("status")=="PASS_R431_J14_DERIVED_CANONICAL_SPATIAL_AUTHORITY_VALIDATION_SEALED" and js.get("verdict")=="SEALED" and js.get("observed_location_history_claim") is False and js.get("canonical_state_rewritten") is False and js.get("source_candidate_npz_sha256")==EXPECTED_J14_SHA)
    else: checks["j14_seal_semantics"]=False
    checks["r327_exact_hash"]=paths["r327"].is_file() and sha256_file(paths["r327"])==EXPECTED_R327_SHA
    checks["r327_checkpoint_exact_hash"]=paths["r327cp"].is_file() and sha256_file(paths["r327cp"])==EXPECTED_R327_CP_SHA
    checks["r314_seal_exact_hash"]=paths["r314"].is_file() and sha256_file(paths["r314"])==EXPECTED_R314_SEAL_SHA
    if paths["r327cp"].is_file():
        cp=load_json(paths["r327cp"]); cohort=tuple(cp.get("candidate_cohort") or [])
        checks["human_200ka_cohort_exact"]=(set(cohort)==set(CANDIDATES) and cp.get("unique_human_identity_materialized") is False)
    else: checks["human_200ka_cohort_exact"]=False
    if paths["r314"].is_file():
        a=load_json(paths["r314"])
        checks["r314_provider_sealed"]=(a.get("verdict")=="PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__30MA_H0_BIOLOGY_RESTART_BOUNDARY_SEALED" and a.get("failed")==[])
    else: checks["r314_provider_sealed"]=False
    # schema-level J14 validation
    try:
        with np.load(paths["j14"],allow_pickle=False) as z:
            age=np.asarray(z["age_ma"],float); ids=tuple(map(str,z["candidate_ids"].tolist())); names=tuple(map(str,z["state_variable_names"].tolist())); s=np.asarray(z["spatial_state"])
        checks["j14_schema_exact"]=(s.shape==(96,2,141,8,4) and ids==CANDIDATES and names==("population_proxy","grid_row","grid_col","active") and np.allclose(age,np.arange(3.0,.2-1e-12,-.02)) and np.isfinite(s).all())
    except Exception: checks["j14_schema_exact"]=False
    checks={k:bool(v) for k,v in checks.items()}
    failed=[k for k,v in checks.items() if not v]
    return {"stage":STAGE,"status":"PASS_R51_IMMUTABLE_PARENT_AUTHORITY" if not failed else "BLOCKED_R51_PARENT_AUTHORITY","scientific_parent_mode":strict,"checks_passed":sum(1 for v in checks.values() if v),"checks_total":len(checks),"failed":failed,"checks":checks}

def engine_utility_review()->dict[str,Any]:
    return {
      "stage":STAGE,"status":"R51_ENGINE_UTILITY_REVIEW_FROZEN","decision_rule":"RUN_EXTERNAL_ENGINE_ONLY_IF_IT_ADDS_DOMAIN_RELEVANT_EVIDENCE_NOT_ALREADY_AVAILABLE_FROM_SEALED_ARCANA_STATE_OR_R4_56_CORPUS",
      "engines":[
        {"engine":"RangeShifter","version":"3.0.1","utility":"HIGH","best_domains":["range_shift","connectivity","dispersal_corridors"],"r51_action":"DEFER_NEW_EXECUTION_TO_R5_2_EXPANSION_CORRIDORS","reason":"R5.1 locates cradle-opportunity regions first; RangeShifter becomes directly adjudicatively useful once origin regions and corridor hypotheses exist."},
        {"engine":"Geonomics","version":"1.4.9","utility":"HIGH_CONTEXT","best_domains":["spatial_population_structure","connectivity","landscape_genomics"],"r51_action":"REUSE_SEALED_J14_BINDING_AND_R4_50_EVIDENCE_NO_NEW_EXECUTION","reason":"R5.1 already has the SEALED J14 canonical spatial authority used for Geonomics binding; rerunning Geonomics cannot define ARCANA cradle truth."},
        {"engine":"Madingley","version":"1.0.6+C++2.02","utility":"MEDIUM_HIGH","best_domains":["biomass","trophic_opportunity","ecosystem_context"],"r51_action":"REUSE_R4_55_DESCRIPTIVE_EVIDENCE_DEFER_TARGETED_EXECUTION","reason":"Canonical C2 forage/environment is sufficient for first cradle-opportunity atlas; targeted trophic checks are useful only after regions emerge."},
        {"engine":"CDMetaPOP","version":"3.08@3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118","utility":"MEDIUM","best_domains":["population_viability","landscape_demogenetics","gene_flow"],"r51_action":"DEFER_TO_PERSISTENCE_BOTTLENECK_AND_CONTACT_ANALYSIS","reason":"Does not improve initial geographic cradle discovery enough to justify a new run before candidate regions exist."},
        {"engine":"NEMO","version":"2.4.2","utility":"MEDIUM","best_domains":["metapopulation_genetics","allele_frequency","quantitative_traits","gene_flow"],"r51_action":"DEFER_TO_GENETIC_PERSISTENCE_AND_GENE_FLOW_VALIDATION","reason":"Genetic dynamics validate later persistence/contact hypotheses; they do not supply missing canonical geography."},
        {"engine":"SLiM","version":"5.2","utility":"HIGH_LATER","best_domains":["ancestry","admixture","whole_genome_gene_flow"],"r51_action":"DEFER_TO_ANCESTRY_ADMIXTURE_STAGE","reason":"Powerful after demographic/spatial hypotheses are fixed; unnecessary for initial ecology-first cradle opportunity discovery."}
      ],
      "new_external_engine_execution_authorized_in_r51":False,
      "new_external_engine_execution_performed":False,
      "external_engine_defines_arcana_target":False,
      "majority_vote":False
    }

def _load_provider(root:Path):
    from arcana_worldsim.scientific_engines import r314_late_cenozoic_binding as r314
    a1=r314.load_a1(root); bind=root/"local_bindings/v0_6D1_R3_14"
    c2,_=r314.build_bound_provider_and_clock(a1,bind/"v0_6_1_SEALED_MINIMAL",bind/"v0_6_4B1/exact_120ka_A1_boundary_state.npz",bind/"v0_6_4B2/relative_eustatic_shoreline_anomaly_120ka_A1.npz")
    return a1,c2

def build_atlas(root:Path)->dict[str,Any]:
    root=Path(root)
    with np.load(root/J14_REL,allow_pickle=False) as z:
        ages=np.asarray(z["age_ma"],float); ids=tuple(map(str,z["candidate_ids"].tolist())); spatial=np.asarray(z["spatial_state"],float)
    with np.load(root/R327_REL,allow_pickle=False) as z:
        rages=np.asarray(z["age_ma"],float); rids=tuple(map(str,z["candidate_ids"].tolist())); varnames=tuple(map(str,z["variable_names"].tolist())); macro=np.asarray(z["state"],float); regimes=np.asarray(z["forcing_regime"]).astype(str); corridor=np.asarray(z["corridor_connectivity"],float)
    if not np.allclose(ages,rages): raise R51Error("J14/R3.27 age axes differ")
    ridx=[rids.index(x) for x in ids]
    a1,c2=_load_provider(root); lat=np.asarray(a1["lat"],float); lon=np.asarray(a1["lon"],float); nr,nc=len(lat),len(lon)
    ncan=len(ids); T=len(ages); E=spatial.shape[0]
    presence=np.zeros((ncan,T,nr,nc),np.uint16); popmass=np.zeros((ncan,T,nr,nc),np.float64)
    member_ever=np.zeros((ncan,E,nr,nc),bool)
    env_temp=np.empty((T,nr,nc),np.float32); env_arid=np.empty_like(env_temp); env_forage=np.empty_like(env_temp); env_wet=np.empty_like(env_temp); env_land=np.empty((T,nr,nc),bool)
    deme_env={sid:{"temperature_c":[],"aridity_index":[],"total_edible_forage":[],"wetland_forage":[]} for sid in ids}
    for t,age in enumerate(ages):
        st=c2.state_at(float(age)); land=np.asarray(st["land_support"],float)>1e-9
        env_land[t]=land; env_temp[t]=np.asarray(st["temperature_c"],np.float32); env_arid[t]=np.asarray(st["aridity_index"],np.float32); env_forage[t]=np.asarray(st["total_edible_forage"],np.float32); env_wet[t]=np.asarray(st["wetland_forage"],np.float32)
        for j,sid in enumerate(ids):
            for e in range(E):
                ds=spatial[e,j,t]
                active=ds[:,3]>0.5; total=float(np.sum(ds[active,0]))
                seen=set()
                for row in ds[active]:
                    r=int(np.clip(np.rint(row[1]),0,nr-1)); c=int(np.clip(np.rint(row[2]),0,nc-1)); p=max(0.0,float(row[0])); seen.add((r,c))
                    if total>0: popmass[j,t,r,c]+=p/total
                    for key,arr in (("temperature_c",env_temp),("aridity_index",env_arid),("total_edible_forage",env_forage),("wetland_forage",env_wet)):
                        deme_env[sid][key].append(float(arr[t,r,c]))
                for r,c in seen:
                    presence[j,t,r,c]+=1; member_ever[j,e,r,c]=True
    denom=float(E*T)
    population_mass_fraction=np.sum(popmass,axis=1)/denom
    ensemble_time_presence_fraction=np.sum(presence,axis=1)/denom
    age_presence_fraction=np.mean(presence>0,axis=1)
    member_coverage_fraction=np.mean(member_ever,axis=1)
    land_persistence=np.mean(env_land,axis=0)
    metrics={
      "land_persistence_fraction":land_persistence.astype(np.float32),
      "forage_q10":np.quantile(env_forage,.10,axis=0).astype(np.float32),
      "forage_median":np.median(env_forage,axis=0).astype(np.float32),
      "wetland_forage_median":np.median(env_wet,axis=0).astype(np.float32),
      "temperature_mean_c":np.mean(env_temp,axis=0).astype(np.float32),
      "temperature_std_c":np.std(env_temp,axis=0).astype(np.float32),
      "aridity_mean":np.mean(env_arid,axis=0).astype(np.float32),
      "aridity_std":np.std(env_arid,axis=0).astype(np.float32),
    }
    # Descriptive occupied-environment envelope; no back-projection of 0 ka traits.
    envelopes={}
    for sid in ids:
        envelopes[sid]={}
        for k,vals in deme_env[sid].items():
            a=np.asarray(vals,float); envelopes[sid][k]={"n":int(a.size),"q05":float(np.quantile(a,.05)),"q50":float(np.quantile(a,.50)),"q95":float(np.quantile(a,.95))}
    # Region registry across a fixed quantile sensitivity family; no result-selected threshold.
    regions=[]
    for j,sid in enumerate(ids):
        mass=population_mass_fraction[j]; positive=mass[mass>0]
        for q in THRESHOLD_QUANTILES:
            thr=float(np.quantile(positive,q)) if positive.size else float("inf")
            mask=(mass>=thr)&(mass>0)&(land_persistence>0)
            comps=_components(mask)
            for ci,cells in enumerate(comps):
                rr=np.array([x[0] for x in cells]); cc=np.array([x[1] for x in cells]); cm=mass[rr,cc]
                w=cm/max(float(cm.sum()),1e-30)
                regions.append({
                  "candidate_id":sid,"threshold_quantile":q,"component_index":ci,"cell_count":len(cells),"population_mass_fraction_sum":float(cm.sum()),
                  "age_presence_fraction_mean":float(np.mean(age_presence_fraction[j,rr,cc])),"member_coverage_fraction_mean":float(np.mean(member_coverage_fraction[j,rr,cc])),
                  "lat_centroid":float(np.sum(lat[rr]*w)),"lon_centroid_linear_diagnostic":float(np.sum(lon[cc]*w)),
                  "row_minmax":[int(rr.min()),int(rr.max())],"col_minmax":[int(cc.min()),int(cc.max())],
                  "land_persistence_mean":float(np.mean(land_persistence[rr,cc])),"forage_q10_mean":float(np.mean(metrics["forage_q10"][rr,cc])),"temperature_std_c_mean":float(np.mean(metrics["temperature_std_c"][rr,cc])),"aridity_std_mean":float(np.mean(metrics["aridity_std"][rr,cc]))
                })
    # Pareto fronts separately per candidate/threshold: maximize support/persistence/coverage/forage, minimize variability.
    def dominates(a,b):
        av=np.array([a["population_mass_fraction_sum"],a["age_presence_fraction_mean"],a["member_coverage_fraction_mean"],a["forage_q10_mean"],-a["temperature_std_c_mean"],-a["aridity_std_mean"]])
        bv=np.array([b["population_mass_fraction_sum"],b["age_presence_fraction_mean"],b["member_coverage_fraction_mean"],b["forage_q10_mean"],-b["temperature_std_c_mean"],-b["aridity_std_mean"]])
        return bool(np.all(av>=bv) and np.any(av>bv))
    for sid in ids:
        for q in THRESHOLD_QUANTILES:
            sub=[r for r in regions if r["candidate_id"]==sid and r["threshold_quantile"]==q]
            for r in sub: r["pareto_nondominated"]=not any(dominates(o,r) for o in sub if o is not r)
    vi={name:i for i,name in enumerate(varnames)}
    macro_summary={}
    for j,sid in enumerate(ids):
        x=macro[:,ridx[j]]
        macro_summary[sid]={
          "effective_population_median_by_age":np.median(x[:,:,vi["effective_population"]],axis=0).astype(np.float32),
          "deme_count_median_by_age":np.median(x[:,:,vi["deme_count"]],axis=0).astype(np.float32),
          "ecological_breadth_median_by_age":np.median(x[:,:,vi["ecological_breadth"]],axis=0).astype(np.float32),
          "dispersal_capacity_median_by_age":np.median(x[:,:,vi["dispersal_capacity"]],axis=0).astype(np.float32),
          "genetic_diversity_proxy_median_by_age":np.median(x[:,:,vi["genetic_diversity_proxy"]],axis=0).astype(np.float32),
          "adaptive_integration_median_by_age":np.median(x[:,:,vi["adaptive_integration"]],axis=0).astype(np.float32),
        }
    return {"age_ma":ages,"candidate_ids":ids,"lat":lat,"lon":lon,"presence":presence,"population_mass_fraction":population_mass_fraction.astype(np.float32),"ensemble_time_presence_fraction":ensemble_time_presence_fraction.astype(np.float32),"age_presence_fraction":age_presence_fraction.astype(np.float32),"member_coverage_fraction":member_coverage_fraction.astype(np.float32),"environment":metrics,"envelopes":envelopes,"regions":regions,"macro_summary":macro_summary,"forcing_regime":regimes,"corridor_connectivity_median_by_age":np.median(corridor,axis=0).astype(np.float32)}

def save_atlas(out:Path,a:dict[str,Any])->dict[str,Any]:
    out.mkdir(parents=True,exist_ok=True); npz=out/"R5_1_CRADLE_OPPORTUNITY_ATLAS.npz"
    kw={"age_ma":a["age_ma"],"candidate_ids":np.asarray(a["candidate_ids"]),"lat":a["lat"],"lon":a["lon"],"population_mass_fraction":a["population_mass_fraction"],"ensemble_time_presence_fraction":a["ensemble_time_presence_fraction"],"age_presence_fraction":a["age_presence_fraction"],"member_coverage_fraction":a["member_coverage_fraction"],"corridor_connectivity_median_by_age":a["corridor_connectivity_median_by_age"]}
    for k,v in a["environment"].items(): kw[k]=v
    for sid in a["candidate_ids"]:
        tag=sid.lower()
        for k,v in a["macro_summary"][sid].items(): kw[f"{tag}__{k}"]=v
    np.savez_compressed(npz,**kw)
    write_json(out/"R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json",{"stage":STAGE,"semantics":"DESCRIPTIVE_ENVELOPE_SAMPLED_AT_J14_MODEL_DERIVED_CANONICAL_DEMES_NOT_BACK_PROJECTED_0KA_TRAITS", "candidates":a["envelopes"]})
    write_json(out/"R5_1_CRADLE_CANDIDATE_REGISTRY.json",{"stage":STAGE,"status":"CRADLE_OPPORTUNITY_REGION_REGISTRY","threshold_quantiles":list(THRESHOLD_QUANTILES),"selection_semantics":"FIXED_QUANTILE_SENSITIVITY_FAMILY_PLUS_PARETO_NONDOMINANCE_NO_WEIGHTED_SCORE_NO_SINGLE_WINNER","regions":a["regions"]})
    return {"atlas_npz":npz.as_posix(),"atlas_sha256":sha256_file(npz),"region_count":len(a["regions"]),"pareto_region_count":sum(bool(r.get("pareto_nondominated")) for r in a["regions"])}
