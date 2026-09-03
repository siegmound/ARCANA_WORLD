from __future__ import annotations
import numpy as np

import rebased_natural_control_runtime_v0_6D1_R3_5 as r35
import d3_additive_variance_v0_6_3D3_3A as av


def _meta():
    return {"S": {"thermal_niche_sigma_c": 2.0, "aridity_niche_sigma": 0.775}}


def test_q_matrix_uses_d3_trait_scales():
    va=np.array([[4*0.02, (0.775/1.55)**2*0.03, 0.35**2*0.04]])
    q=r35._q_matrix(va,np.array([0]),["S"],_meta(),0.35)
    assert np.allclose(q, [[0.02,0.03,0.04]])


def test_instrumentation_is_non_invasive_for_d3_3a_operators():
    cfg=r35.R35Config()
    avcfg=r35.r34._variance_cfg_d3_3a(cfg)
    z=np.array([[0.0,0.0,0.0],[0.2,0.1,0.0]])
    scales=av.trait_scales(_meta()["S"],cfg.body_mass_scale)
    v=np.stack([av.denormalize_variance(np.array([0.02,0.02,0.02]),scales),av.denormalize_variance(np.array([0.03,0.03,0.03]),scales)])
    n=np.array([10.0,8.0]); G=np.array([[0.0,0.1],[0.1,0.0]]); ri=np.zeros((2,2)); idx=np.array([0,0])
    exp_z,exp_v,_=av.gene_flow_moment_mix(z,v,n,G,ri,idx,avcfg)
    targets=np.zeros((2,3)); gen=np.array([5.0,5.0])
    exp_v2,_=av.advance_nonflow_variance(exp_v,z,targets,n,gen,idx,["S"],_meta(),cfg.body_mass_scale,125000,avcfg)
    with r35._instrument_additive_variance(cfg) as rec:
        got_z,got_v,_=av.gene_flow_moment_mix(z,v,n,G,ri,idx,avcfg)
        got_v2,_=av.advance_nonflow_variance(got_v,z,targets,n,gen,idx,["S"],_meta(),cfg.body_mass_scale,125000,avcfg)
    assert np.array_equal(got_z,exp_z)
    assert np.array_equal(got_v2,exp_v2)
    assert len(rec)==1
    assert rec[0]["homeostasis_clipping_count"]==0


def test_unclipped_probe_detects_true_safety_cap_contact_without_feedback():
    cfg=r35.R35Config(variance_ceiling_normalized=0.08)
    avcfg=r35.r34._variance_cfg_d3_3a(cfg)
    scales=av.trait_scales(_meta()["S"],cfg.body_mass_scale)
    # Start above the safety cap to force the exact parent Riccati operator to clip.
    v=np.stack([av.denormalize_variance(np.array([0.09,0.09,0.09]),scales)])
    z=np.zeros((1,3)); n=np.array([10.0]); G=np.zeros((1,1)); ri=np.zeros((1,1)); idx=np.array([0]); targets=np.zeros((1,3)); gen=np.array([5.0])
    with r35._instrument_additive_variance(cfg) as rec:
        _,v1,_=av.gene_flow_moment_mix(z,v,n,G,ri,idx,avcfg)
        actual,_=av.advance_nonflow_variance(v1,z,targets,n,gen,idx,["S"],_meta(),cfg.body_mass_scale,1.0,avcfg)
    qactual=r35._q_matrix(actual,idx,["S"],_meta(),cfg.body_mass_scale)
    assert float(np.max(qactual)) <= 0.08 + 1e-15
    assert rec[0]["homeostasis_clipping_count"]==3
    assert rec[0]["after_homeostasis_unclipped"]["max_q"] > 0.08


def test_event_context_attaches_by_internal_biology_step():
    cfg=r35.R35Config()
    rec=[{"step_index":0},{"step_index":1}]
    result={"events":[{"event":"deme_fission","elapsed_year":125000.0,"daughter_component_id":"D"},{"event":"speciation","elapsed_year":250000.0,"daughter_species_id":"S2"}]}
    r35._attach_time_and_events(rec,result,cfg)
    assert rec[0]["age_ma"]==209.875
    assert rec[0]["event_counts_same_step"]=={"deme_fission":1}
    assert rec[1]["event_counts_same_step"]=={"speciation":1}


def test_headroom_summary_counts_clipping_steps_and_peak_context():
    cfg=r35.R35Config()
    base={
      "after_homeostasis":{"max_q":0.04,"per_axis_max":[0.04,0.03,0.02],"max_root_species":"A"},
      "after_gene_flow":{"max_q":0.041},
      "after_homeostasis_unclipped":{"max_q":0.04},
      "homeostasis_clipping_count":0,
      "after_homeostasis_threshold":{"count_ge_threshold":0},
      "age_ma":200.0,"event_counts_same_step":{}
    }
    peak={
      "after_homeostasis":{"max_q":0.08,"per_axis_max":[0.08,0.05,0.03],"max_root_species":"B"},
      "after_gene_flow":{"max_q":0.081},
      "after_homeostasis_unclipped":{"max_q":0.083},
      "homeostasis_clipping_count":2,
      "after_homeostasis_threshold":{"count_ge_threshold":2},
      "age_ma":190.0,"event_counts_same_step":{"deme_fission":1}
    }
    s=r35.summarize_headroom_telemetry([base,peak],cfg)
    assert s["peak_after_homeostasis_q"]==0.08
    assert s["steps_with_homeostasis_clipping"]==1
    assert s["steps_with_ge_99pct_ceiling_after_homeostasis"]==1
    assert s["event_context_at_peak"]=={"deme_fission":1}


def test_r35_default_keeps_r34_scientific_parameters_except_instrumentation_fields():
    a=r35.R35Config(); b=r35.r34.R34Config()
    for k in r35.r34.R34Config.__dataclass_fields__:
        assert getattr(a,k)==getattr(b,k)
