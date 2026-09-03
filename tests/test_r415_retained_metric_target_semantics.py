from pathlib import Path
import tempfile
import json
from arcana_worldsim.scientific_engines.r415_retained_metric_target_semantics import (
    _nemo_qfreq,_cdm_summary,_authorized_recovery_engine,_recover_p0,REPAIR_REVISION
)

def test_nemo_qfreq_parses():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'r43_nemo_1.qfreq'; p.write_text('h\n1 0 1 0 0.2\n2 0 1 0 0.8\n1 0 2 0 0.3\n2 0 2 0 0.7\n')
        x=_nemo_qfreq(p); assert x['status']=='PASS'; assert x['locus_count']==2; assert x['mean_between_population_frequency_gap']>0

def test_cdmeta_summary_parses_total_and_growth():
    with tempfile.TemporaryDirectory() as td:
        p=Path(td)/'summary_popAllTime.csv'; p.write_text('Year,N_Initial,GrowthRate\n0,100|50|50,1.1|x\n1,110|55|55,0.9|x\n')
        x=_cdm_summary(p); assert x['status']=='PASS'; assert x['initial_population']==100; assert abs(x['final_population']-99)<1e-9

def test_authorized_recovery_engine_is_frozen_r414_closure_action():
    assert _authorized_recovery_engine({'closure_action':'RETAINED_NEMO_RUNTIME_METRIC_RECOVERY_CANDIDATE'})=='NEMO'
    assert _authorized_recovery_engine({'closure_action':'RETAINED_SLIM_RUNTIME_METRIC_RECOVERY_CANDIDATE'})=='SLiM'
    assert _authorized_recovery_engine({'closure_action':'RETAINED_CDMETAPOP_RUNTIME_METRIC_RECOVERY_CANDIDATE'})=='CDMetaPOP'
    assert _authorized_recovery_engine({'closure_action':'SOMETHING_ELSE'}) is None

def test_r415_r1_does_not_require_unselected_primary_engine_to_recover():
    # R4.14 selects NEMO as the P0 retained-recovery candidate. A second PRIMARY
    # engine can be present in the authority cell without becoming a required
    # retained extractor for this frozen P0 action.
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        jid_n='J_NEMO'; jid_s='J_SLIM'
        rw=root/'outputs/v0_6D1_R4_3/jobs'/jid_n/'runtime_work'; rw.mkdir(parents=True)
        (rw/'r43_nemo_1.qfreq').write_text('h\n1 0 1 0 0.2\n2 0 1 0 0.8\n')
        gap={
            'window_id':'W','domain':'gene_flow',
            'closure_action':'RETAINED_NEMO_RUNTIME_METRIC_RECOVERY_CANDIDATE',
            'primary_engines':['NEMO','SLiM'],
            'primary_rows':[{'engine':'NEMO','job_id':jid_n},{'engine':'SLiM','job_id':jid_s}],
            'retained_runtime_hits':{'NEMO':[str(rw/'r43_nemo_1.qfreq')],'SLiM':[]},
        }
        x=_recover_p0(root,gap)
        assert x['recovery_pass'] is True
        assert x['resolved'] is True
        assert x['authorized_recovery_engine']=='NEMO'
        assert x['resolution_status']=='P0_RETAINED_RUNTIME_METRIC_RECOVERED'
        slim=[r for r in x['engine_records'] if r['engine']=='SLiM'][0]
        assert slim['pass'] is False
        assert slim['required_for_r414_p0_candidate_realization'] is False

def test_unrecoverable_predeclared_candidate_is_explicitly_reclassified_not_faked():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); jid='J_CDM'
        rw=root/'outputs/v0_6D1_R4_3/jobs'/jid/'runtime_work'; rw.mkdir(parents=True)
        # This broad artifact could have caused the R4.14 candidate hit, but it
        # is not the clean summary file required by the frozen CDMetaPOP extractor.
        bad=rw/'some_ind_output.csv'; bad.write_text('x\n')
        gap={
            'window_id':'W','domain':'gene_flow',
            'closure_action':'RETAINED_CDMETAPOP_RUNTIME_METRIC_RECOVERY_CANDIDATE',
            'primary_engines':['CDMetaPOP'],
            'primary_rows':[{'engine':'CDMetaPOP','job_id':jid}],
            'retained_runtime_hits':{'CDMetaPOP':[str(bad)]},
        }
        x=_recover_p0(root,gap)
        assert x['recovery_pass'] is False
        assert x['resolved'] is True
        assert x['resolution_status']=='P0_CANDIDATE_EXHAUSTED_RECLASSIFIED_TO_P2'
        assert x['next_priority']=='P2_EXISTING_FROZEN_JOB_ADAPTER_ENHANCEMENT_AND_SYMMETRIC_REEXECUTION'
        assert x['adjudicative_promotion_authorized'] is False

def test_candidate_without_predeclared_r414_hit_fails_closed():
    with tempfile.TemporaryDirectory() as td:
        root=Path(td); jid='J_NEMO'
        gap={
            'window_id':'W','domain':'gene_flow',
            'closure_action':'RETAINED_NEMO_RUNTIME_METRIC_RECOVERY_CANDIDATE',
            'primary_engines':['NEMO'],
            'primary_rows':[{'engine':'NEMO','job_id':jid}],
            'retained_runtime_hits':{'NEMO':[]},
        }
        x=_recover_p0(root,gap)
        assert x['resolved'] is False
        assert x['resolution_status'].startswith('UNRESOLVED_')

def test_no_engine_execution_is_design_invariant():
    p=Path('configs/world1_r415_retained_metric_target_semantics_v0_6D1_R4_15.json')
    d=json.loads(p.read_text()); assert d['engine_execution_performed'] is False; assert d['rules']['no_engine_rerun'] is True

def test_r415_r1_repair_is_fail_closed_and_no_auto_promotion():
    d=json.loads(Path('configs/world1_r415_retained_metric_target_semantics_v0_6D1_R4_15.json').read_text())
    assert d['r415_r1_repair']['revision']==REPAIR_REVISION
    assert d['r415_r1_repair']['authorized_recovery_engine_is_defined_by_r414_closure_action'] is True
    assert d['r415_r1_repair']['unrecoverable_predeclared_p0_candidate_reclassifies_to_p2_without_rerun'] is True
    assert d['rules']['no_target_leakage'] is True
    assert d['rules']['recovered_metric_not_adjudicative_until_domain_transform_is_explicit'] is True
    assert d['rules']['arcana_target_candidate_not_adjudicative_until_provenance_and_transform_are_explicit'] is True
