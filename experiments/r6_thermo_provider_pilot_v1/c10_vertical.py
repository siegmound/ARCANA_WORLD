"""Independent numerical readback of the native thin-shell reference stress."""
import math

import numpy as np

from experiments.r6_thermo_provider_pilot_v1 import c08_constitutive as summary
from experiments.r6_thermo_provider_pilot_v1 import c09_column_scenarios as c09
from experiments.r6_thermo_provider_pilot_v1.run_c08_regional_closure import need

G = 9.82
KM = 1000.


def samples(pre, depth):
    """Owner-specific T, rho0, alpha at common below-surface sample depths."""
    z=np.asarray(depth,dtype=float)
    moho,lab=pre["layer1_z1_m"],pre["layer2_z1_m"]
    result=[]
    for layer,k in ((1,"crust"),(2,"mantle")):
        x=z-pre[f"layer{layer}_z0_m"]
        t=np.polynomial.polynomial.polyval(x,[pre[f"layer{layer}_{field}"]
                                             for field in ("c0_k","c1_k_m","c2_k_m2","c3_k_m3")])
        if layer==2:
            bottom_t=np.polynomial.polynomial.polyval(lab-pre["layer2_z0_m"],
                [pre["layer2_"+key] for key in ("c0_k","c1_k_m","c2_k_m2","c3_k_m3")])
            t=np.where(z<=lab,t,bottom_t*np.exp(pre["mantle_expansivity_k_1"]*G*(z-lab)/pre["mantle_cp_j_kg_k"]))
        rho=np.full_like(z,pre[k+"_density_kg_m3"])
        if layer==2:
            rho=np.where(z<=lab,rho,pre["rho_asthenosphere_kg_m3"])
        result.append((t,rho,np.full_like(z,pre[k+"_expansivity_k_1"])))
    return np.where(z<moho,np.asarray(result[0]),np.asarray(result[1]))


def reference_stress(profiles, weights, elevation, stop):
    """Reconstruct actual Squeez datum and grids; use cumulative reductions."""
    weights=np.asarray(weights)
    water=weights @ [r["rho_water_kg_m3"] for r in profiles]
    asth=weights @ [r["rho_asthenosphere_kg_m3"] for r in profiles]
    z_top=min(0.,-elevation)
    z_base=stop-elevation
    length=z_base-z_top
    sea_depth=z_top+KM*np.arange(int(length/KM)+1,dtype=float)
    sea_depth=np.r_[sea_depth,z_base]
    z=sea_depth+elevation
    t,rho,alpha=np.einsum("i,ijk->jk",weights,
                          [samples(row,np.maximum(z,0.)) for row in profiles])
    effective=rho*(1-alpha*t)
    rhotop=effective[0]
    effective=np.where(z>0.,effective,water)
    if elevation>0.:
        effective[0]=rhotop
    densities=np.array([water,water,.7*water+.3*rhotop,*([rhotop]*4),
                        .7*rhotop+.3*asth,*([asth]*292)])
    ref_pa=np.interp(sea_depth,KM*np.arange(301),np.r_[0.,np.cumsum(densities*G*KM)])
    overburden=np.r_[0.,np.cumsum(G*np.diff(sea_depth)*(effective[:-1]+effective[1:])*.5)]
    residual=ref_pa-overburden
    return {"reference_pressure_at_base_Pa":float(ref_pa[-1]),
            "native_1km_column_pressure_Pa":float(overburden[-1]),
            "sigZZB_Pa":float(residual[-1]),
            "tauZZ_N_m":float(np.trapezoid(residual,sea_depth)),
            "rho_water_kg_m3":float(water)}


def offline_column_pressure(pre, depth):
    """Extend the C09 column pressure comparator only with its PRE adiabat."""
    lab=pre["layer2_z1_m"]
    prefix={"crust":pre["crust_expansivity_k_1"],"mantle":pre["mantle_expansivity_k_1"]}
    p=float(c09.pressure(pre,min(depth,lab),G,prefix))
    if depth<=lab:
        return p
    excess=depth-lab
    alpha=pre["mantle_expansivity_k_1"]
    rate=alpha*G/pre["mantle_cp_j_kg_k"]
    temp=samples(pre,[lab])[0,0]
    t_integral=temp*math.expm1(rate*excess)/rate
    return p+G*pre["rho_asthenosphere_kg_m3"]*(excess-alpha*t_integral)


def diagnostics(case, profiles, ip_geometry, data):
    """Require native fixture parity, preserve the original nonzero residuals."""
    hyd=data["hydrostatic"]
    dry=data["dry"]
    deeper=data["depth_2km"]
    linear=data["linear_arc"]
    need(all(linear[k]==hyd[k] for k in ("SIZE","CONTROL","NODE","IP")),
         "C10_TRACE_CHANGED_FIXED_STATE")
    nrow=hyd["SIZE"][0]
    need(nrow[:4]==[81,128,32,162] and nrow[4]==nrow[5],
         "C10_NATIVE_SIZE_SCOPE")
    expected_controls=[(1.,1000.),(0.,1000.),(1.,2000.)]
    for native,expected in zip((hyd,dry,deeper),expected_controls,strict=True):
        a=native["CONTROL"][0]
        need(tuple(a[:2])==expected and a[2]==0. and a[3]>0. and a[-2:]==[0.,1.],
             "C10_NATIVE_CONTROL_BINDING")
    need(hyd["NODE"]==dry["NODE"]==deeper["NODE"] and hyd["BC"]==dry["BC"]==deeper["BC"],
         "C10_INACTIVE_LIMIT_CHANGED_FIXED_STATE")
    need(hyd["IP"]==dry["IP"] and
         all(a[:6]+a[7:]==b[:6]+b[7:] for a,b in zip(hyd["IP"],deeper["IP"],strict=True)),
         "C10_INACTIVE_LIMIT_CHANGED_IP_STATE")
    need(all(row[-3:]==[0.,0.,0.] for v in data.values() for row in v["IP"]),
         "C10_BASAL_FORCE_NONZERO")
    bc_errors = {}
    for name, native, rows in (("smooth_distributed", hyd, case["selected_trace_rows"]),
                               ("linear_arc", linear, case["linear_trace_rows"])):
        max_bc = 0.
        for (order,i,code,s,e),row in zip(native["BC"],rows,strict=True):
            need((order,i,code)==(row["BC_order"],row["runtime_node_id"],2),
                 "C10_NATIVE_BC_BINDING")
            max_bc=max(max_bc,math.dist((s,e),row["prescribed_south_east_m_s"]))
        need(max_bc<2e-22,"C10_NATIVE_BC_ROUNDTRIP")
        bc_errors[name] = max_bc

    nodes=[]
    points=[]
    max_sigma,max_tau=0.,0.
    for actual,mapped,source in zip(hyd["NODE"],case["reporting_plate_binding"],
                                    case["feg_columns"],strict=True):
        idx,slot,height,moho,mantle,sig,tau,fs,fe=actual
        need(idx==mapped["local_id"] and slot==mapped["native_slot"],"C10_NATIVE_NODE_BINDING")
        need([idx,height,moho,mantle]==source,"C10_FEG_COLUMN_BINDING")
        data_row=reference_stress([profiles[str(mapped["parent_id"])]],[1.],height,moho+mantle)
        nodes.append({"local_id":int(idx),"parent_id":mapped["parent_id"],"elevation_m":height,
                      "native_sigZZB_Pa":sig,"native_tauZZ_N_m":tau,"native_fixed_S_E_N":[fs,fe],**data_row})
    geom=ip_geometry["triangles"]
    weights=ip_geometry["native_points"]
    element_map={m["local_id"]:m for m in case["G4_mapping"]["elements"]}
    by_parent={row["parent_id"]:row for row in nodes}
    for i,actual in enumerate(hyd["IP"]):
        local,point,moho,mantle,sig,tau,glue,water,p_c,p_total,*_=actual
        need(local==i//7+1 and point==i%7+1,"C10_NATIVE_IP_BINDING")
        parent=element_map[local]["parent_id"]
        geo=geom[str(parent)]
        w=np.asarray(weights[int(point)-1])
        elevation=float(w @ [by_parent[n]["elevation_m"] for n in geo["parents"]])
        rows=[profiles[str(key)] for key in geo["parents"]]
        diag=reference_stress(rows,w,elevation,moho+mantle)
        need(abs(diag["rho_water_kg_m3"]-water)<1e-10 and elevation>0.,"C10_PORE_SOURCE")
        depths=[moho,moho+mantle]
        surrogate=[float(w @ [offline_column_pressure(row,d) for row in rows]) for d in depths]
        pore=[water*G*d for d in depths]
        # The C09 proxy used the same local surface zero, nominal water 1000.
        pore_diff=[d*G*(water-1000.) for d in depths]
        points.append({"element_local":int(local),"element_parent":parent,"ip":int(point),
                       "parents":geo["parents"],"elev_m":elevation,"depth_m":depths,
                       "native_sigZZB_Pa":sig,"native_tauZZ_N_m":tau,"OneBar_glue":glue,
                       "native_solid_pressure_Pa":[p_c,p_total],"native_pore_pressure_Pa":pore,
                       "native_hydrostatic_effective_pressure_Pa":[p_c-pore[0],p_total-pore[1]],
                       "native_dry_effective_pressure_Pa":[p_c,p_total],
                       "native_minus_C09_pore_pressure_Pa":pore_diff,
                       "native_minus_parent_projected_C09_overburden_Pa":
                           [p_c-surrogate[0],p_total-surrogate[1]],**diag})
    # 1 km paired reference/column replay. Use pressure/length magnitudes,
    # not the possibly cancelled residual, for the rounding-scale check.
    for row in (*nodes,*points):
        dp=abs(row["native_sigZZB_Pa"]-row["sigZZB_Pa"])
        dt=abs(row["native_tauZZ_N_m"]-row["tauZZ_N_m"])
        scale=max(row["reference_pressure_at_base_Pa"],row["native_1km_column_pressure_Pa"])
        slack=(4096*np.finfo(float).eps)*scale
        need(dp<=slack and dt<=slack*300000.,"C10_VERTICAL_ORACLE_MISMATCH")
        max_sigma,max_tau=max(max_sigma,dp),max(max_tau,dt)
    return {
        "native_nodes":nodes,"native_IP":points,"matrix_size":{
            "nRank":int(nrow[3]),"kl":int(nrow[4]),"ku":int(nrow[5]),"nKRows":int(nrow[6]),
            "binary64_band_payload_bytes":int(nrow[3]*nrow[6]*8),
            "operator_assembled":False,"rank_of_operator":None},
        "native_visMax_Pa_s":hyd["CONTROL"][0][3],
        "native_bc_max_abs_norm_error_m_s":bc_errors,
        "sigZZB_ranges_Pa":{k:summary.summary([r["native_sigZZB_Pa"] for r in v])
                            for k,v in (("nodes",nodes),("integration_points",points))},
        "tauZZ_ranges_N_m":{k:summary.summary([r["native_tauZZ_N_m"] for r in v])
                            for k,v in (("nodes",nodes),("integration_points",points))},
        "oracle_max_abs_error":{"sigZZB_Pa":max_sigma,"tauZZ_N_m":max_tau},
        "max_native_minus_C09_pore_Pa":max(abs(x) for r in points for x in r["native_minus_C09_pore_pressure_Pa"]),
        "max_native_minus_parent_projected_C09_overburden_Pa":max(abs(x) for r in points for x in r["native_minus_parent_projected_C09_overburden_Pa"]),
        "hydrostatic_ip_range_Pa":summary.summary([x for r in points for x in r["native_hydrostatic_effective_pressure_Pa"]]),
        "glue_range_by_compatibility_depth":{k:summary.summary([r[6] for r in v["IP"]]) for k,v in data.items()},
        "zero_sigHB_eta_vM_oVB_pulled_measured":True,
        "hydrostatic_and_dry_fixed_GPE_identical":True,
    }
