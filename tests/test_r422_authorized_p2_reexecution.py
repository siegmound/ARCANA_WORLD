from pathlib import Path
import numpy as np
from arcana_worldsim.scientific_engines.r422_authorized_p2_reexecution import _job_semantics_ok, deferred_geonomics_completion_audit

def test_nemo_semantic_guards_accept_only_raw_metrics():
    raw={'replicates':[{'metrics':{'loci':8,'metric_semantics':{'mean_expected_heterozygosity':'RAW_EXPECTED_HETEROZYGOSITY_NOT_ADDITIVE_GENETIC_VARIANCE','mean_population_frequency_range':'RAW_ALLELE_FREQUENCY_DIFFERENTIATION_NOT_GENE_FLOW_RATE'}}}]}
    ok,err=_job_semantics_ok('NEMO',raw); assert ok and not err

def test_nemo_semantic_guard_rejects_false_variance_identity():
    raw={'replicates':[{'metrics':{'loci':8,'metric_semantics':{'mean_expected_heterozygosity':'ADDITIVE_VARIANCE','mean_population_frequency_range':'RAW_ALLELE_FREQUENCY_DIFFERENTIATION_NOT_GENE_FLOW_RATE'}}}]}
    ok,err=_job_semantics_ok('NEMO',raw); assert not ok and 'heterozygosity_semantic_guard_missing' in err

def test_slim_semantic_guards_accept_only_nonidentity_metrics():
    raw={'replicates':[{'metrics':{'current_sample_nodes':20,'metric_semantics':{'global_diversity_per_site':'DIVERSITY_NOT_ANCESTRY_CONTRIBUTION','fst_between_current_population_samples':'DIFFERENTIATION_NOT_MIGRATION_RATE'}}}]}
    ok,err=_job_semantics_ok('SLiM',raw); assert ok and not err

def test_cdmetapop_requires_matched_control_and_proxy_absolute_response():
    raw={'absolute_population_response_comparability':'PROXY_ONLY','replicates':[{'matched_control_population_effect_ratio':0.93,'dynamic':{'population_response_ratio':1.1},'neutral':{'population_response_ratio':1.18}}]}
    ok,err=_job_semantics_ok('CDMetaPOP',raw); assert ok and not err

def test_geonomics_deferred_audit_never_authorizes_scalar_synthesis(tmp_path:Path):
    def save(rel, **kw):
        p=tmp_path/rel; p.parent.mkdir(parents=True,exist_ok=True); np.savez(p,**kw)
    save('outputs/v0_6D1_R3_27/R3_27_MACRO_REPLAY_TRAJECTORIES.npz',age_ma=np.array([3.,.2]),state=np.zeros((1,1,2,1)),candidate_ids=np.array(['x']))
    save('outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz',snapshot_deme_state=np.zeros((1,1,1,1,4)),snapshot_active=np.ones((1,1,1,1)),snapshot_age_ka=np.array([200.]),state_variable_names=np.array(['population_proxy','grid_row','grid_col','local_suitability']))
    save('outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz',anchor_age_ka=np.array([20.,0.]),environment_fields=np.zeros((2,2,2,1)),environment_variable_names=np.array(['land_fraction']))
    save('outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz',anchor_age_ka=np.array([20.,0.]),producer_landscape=np.zeros((1,2,2,2,1)),landscape_variable_names=np.array(['suitability']))
    out=deferred_geonomics_completion_audit(tmp_path)
    assert out['record_count']==3
    assert out['geonomics_execution_authorized_in_r422'] is False
    assert out['geonomics_family_ready_for_execution'] is False
    assert all(r['scalar_descriptor_synthesis_forbidden'] for r in out['records'])


def test_r422_r1_nemo_bridge_uses_governed_base_python_without_adapter_mutation():
    src = Path("capture_v0_6D1_R4_22_authorized_jobs.ps1").read_text(encoding="utf-8")
    assert "$CondaBasePython = $CondaPath -replace '/bin/conda$','/bin/python'" in src
    marker = "    'NEMO' {$script=@\""
    nemo = src.split(marker, 1)[1].split("\"@}", 1)[0]
    assert "$CondaBasePythonQ" in nemo
    assert "run -n '$NemoEnv' python " not in nemo
    assert "benchmarks/r421/nemo_r421.py" in nemo
