from __future__ import annotations
from pathlib import Path
import json
import hashlib
import numpy as np

from arcana_worldsim.state_query import r52_corridors as r


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _write_json(p: Path, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, sort_keys=True) + "\n", encoding="utf-8")


def test_frozen_sensitivity_family_is_exact_and_not_result_selected():
    assert r.HABITAT_PROFILES == (
        "LAND_SUPPORT_UPPER_BOUND",
        "OCCUPIED_ENVELOPE_CORE_DIAGNOSTIC",
    )
    assert r.MOVEMENT_PROFILES == {
        "D1_STANDARDIZED_1_CELL_CHARACTERISTIC": 100.0,
        "D2_STANDARDIZED_2_CELL_CHARACTERISTIC": 200.0,
    }
    assert r.SEEDS == (520201, 520202)
    assert r.EXPECTED_ROBUST_FAMILY_COUNT * len(r.HABITAT_PROFILES) * len(r.MOVEMENT_PROFILES) * len(r.SEEDS) == 96


def test_components_wrap_longitude_seam():
    mask=np.zeros((3,5),bool); mask[1,0]=True; mask[1,4]=True
    comps=r._components(mask)
    assert len(comps)==1
    assert set(comps[0])=={(1,0),(1,4)}


def test_habitat_profiles_are_fixed_bounds_not_weighted_score():
    env={
        "land":np.array([[[True,True,False]]]),
        "temperature_c":np.array([[[10.,30.,10.]]]),
        "aridity_index":np.array([[[.5,.5,.5]]]),
        "total_edible_forage":np.array([[[2.,2.,2.]]]),
        "wetland_forage":np.array([[[1.,1.,1.]]]),
    }
    e={
        "temperature_c":{"q05":5,"q95":20},
        "aridity_index":{"q05":.2,"q95":.8},
        "total_edible_forage":{"q05":1,"q95":3},
        "wetland_forage":{"q05":0,"q95":2},
    }
    assert r._habitat_mask("LAND_SUPPORT_UPPER_BOUND",env,e).tolist()==[[[True,True,False]]]
    assert r._habitat_mask("OCCUPIED_ENVELOPE_CORE_DIAGNOSTIC",env,e).tolist()==[[[True,False,False]]]


def test_ascii_grid_vertical_flip_makes_arcana_row_zero_engine_bottom(tmp_path):
    a=np.array([[1,2],[3,4]],dtype=np.uint8)
    p=tmp_path/'x.asc'; r._write_ascii_grid(p,a,cellsize=100)
    lines=p.read_text().splitlines()
    assert lines[:6]==['ncols 2','nrows 2','xllcorner 0','yllcorner 0','cellsize 100','NODATA_value -9999']
    assert lines[6:] == ['3 4','1 2']



def test_group_source_reader_uses_exact_profile_filtered_source_input(tmp_path):
    nr,nc=3,5
    # This is the rolled/profile-filtered engine source, deliberately smaller than a hypothetical family core.
    rolled=np.zeros((nr,nc),dtype=np.uint8); rolled[0,1]=1; rolled[2,4]=1
    inp=tmp_path/'Inputs'; inp.mkdir()
    r._write_ascii_grid(inp/'source.asc',rolled,cellsize=100)
    group={
        'group_id':'G','input_dir':'Inputs','roll_columns':2,
        'source_semantic_sha256':r.semantic_sha256(rolled),
    }
    unrolled,ok=r._read_group_source_unrolled(tmp_path,group,nr,nc)
    assert ok is True
    assert np.array_equal(unrolled,np.roll(rolled.astype(bool),-2,axis=1))


def test_semantic_hash_is_shape_and_dtype_sensitive():
    a=np.array([[1,2]],dtype=np.uint8)
    assert r.semantic_sha256(a)==r.semantic_sha256(a.copy())
    assert r.semantic_sha256(a)!=r.semantic_sha256(a.astype(np.int16))
    assert r.semantic_sha256(a)!=r.semantic_sha256(a.reshape(2,1))


def test_circular_source_col_handles_dateline_cluster():
    # cells at columns 179 and 0 should center at seam, not around col 90.
    nc=180
    cells={0*nc+179,0*nc+0}
    c=r._circular_source_col(cells,nc)
    assert c in (0,179)



def test_engine_xy_decoder_requires_unique_exact_year0_source_recovery():
    nr,nc=3,4; roll=0
    expected={0, 1*nc+2}
    # Engine coordinates at 100-unit cell centres; rows are already ARCANA-oriented here.
    raw=[(0,50.0,50.0,5.0),(0,250.0,150.0,5.0)]
    d=r._decode_engine_xy_exact_source(raw,expected,nr,nc,roll)
    assert d['exact'] is True
    assert d['coordinate_mode']=='RESOLUTION_FLOOR'
    assert d['y_reflected'] is False


def test_parent_authority_semantics_can_be_dev_validated(tmp_path):
    # Dev fixture deliberately uses non-authoritative bytes; allow_non_scientific_dev
    # relaxes exact parent hashes but not sealed semantics and manifest integrity.
    out=tmp_path/r.R51_OUT_REL; out.mkdir(parents=True)
    _write_json(out/'R5_1_FINAL_SEAL.json',{
        'sealed':True,'scientific_seal':True,
        'status':'PASS_R51_EMERGENT_HOMINID_CRADLE_AND_ECOLOGICAL_NICHE_DISCOVERY_SEALED',
        'summary':{
            'all_threshold_family_count':12,
            'closure_readiness':'READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED',
            'RangeShifter_action':'DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION',
            'canonical_state_changed':False,'derived_refinement_promoted_to_canon':False,'deep_biological_coupling':False,
        }
    })
    (out/'R5_1_CRADLE_OPPORTUNITY_ATLAS.npz').write_bytes(b'dev-atlas')
    _write_json(out/'R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json',{'candidates':{}})
    _write_json(out/'R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json',{
        'status':'PASS_R51_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION','all_threshold_family_count':12,
        'closure_readiness':'READY_FOR_R51_SEAL_NO_NEW_EXTERNAL_ENGINE_REQUIRED',
        'engine_adjudication':{'RangeShifter':{'action':'DEFER_NEW_EXECUTION_TO_R5_2_TARGETED_CORRIDOR_VALIDATION'},'external_engine_defines_arcana_target':False,'majority_vote':False}
    })
    fams=[]
    for i in range(12):
        fams.append({'family_id':f'F{i}','candidate_id':r.CANDIDATES[i%2],'survives_all_thresholds':True})
    _write_json(out/'R5_1_ROBUST_REGION_FAMILIES.json',{'families':fams})
    # Candidate manifest over atlas+envelope.
    cand_files={}
    for name in ['R5_1_CRADLE_OPPORTUNITY_ATLAS.npz','R5_1_OCCUPIED_ENVIRONMENT_ENVELOPES.json']:
        p=out/name; cand_files[name]={'bytes':p.stat().st_size,'sha256':_sha(p)}
    _write_json(out/'R5_1_OUTPUT_MANIFEST.json',{'files':cand_files})
    # Structure manifest over structure+families.
    struct_files={}
    for name in ['R5_1_CRADLE_STRUCTURE_AND_ENGINE_ADJUDICATION.json','R5_1_ROBUST_REGION_FAMILIES.json']:
        p=out/name; struct_files[name]={'bytes':p.stat().st_size,'sha256':_sha(p)}
    _write_json(out/'R5_1_STRUCTURE_ADJUDICATION_MANIFEST.json',{'files':struct_files})
    j14=tmp_path/r.J14_REL; j14.parent.mkdir(parents=True); j14.write_bytes(b'dev-j14')
    _write_json(tmp_path/r.R314_SEAL_REL,{'verdict':'PASS_R314_LATE_CENOZOIC_PROVIDER_C2_AND_ADAPTIVE_CLOCK_BOUND__30MA_H0_BIOLOGY_RESTART_BOUNDARY_SEALED','failed':[]})
    wrap=tmp_path/r.R41_R_WRAPPER_REL; wrap.parent.mkdir(parents=True); wrap.write_text('#!/bin/sh\n',encoding='utf-8')
    result=r.validate_parent_authority(tmp_path,allow_non_scientific_dev=True)
    assert result['failed']==[]


def test_adapter_and_runner_freeze_single_replicate_governed_path():
    root=Path(__file__).resolve().parents[1]
    adapter=(root/'benchmarks/r52/rangeshiftr_r52_group.R').read_text(encoding='utf-8')
    runner=(root/'run_v0_6D1_R5_2.ps1').read_text(encoding='utf-8')
    assert 'packageVersion("RangeShiftR")' in adapter
    assert 'Replicates=1' in adapter
    assert 'Rmax=1.5' in adapter
    assert 'EmigProb=0.1' in adapter
    assert 'Distances=movement_dist[mi]' in adapter
    assert 'Initialise(InitType=1, SpType=0, InitDens=1)' in adapter
    assert 'Initialise(InitType=0, FreeType=1, InitDens=1)' not in adapter
    assert 'SPDIST_INITTYPE1_SPTYPE0' in adapter
    assert 'PowerShell' not in adapter
    assert 'wsl_executable' in runner and 'conda_binding' in runner
    assert 'PASS_R52_INTEGRATED_TARGETED_RANGESHIFTER_CORRIDOR_EVIDENCE_CANDIDATE_RUN' in runner
    assert 'source-binding preflight' in runner
    assert 'probe_rangeshiftr_r52_source_binding.R' in runner
    assert '[switch]$ProbeOnly' in runner and 'PASS_R52_R1_SOURCE_BINDING_PREFLIGHT_ONLY' in runner




def test_runner_resume_refuses_pre_r1_free_initialisation_evidence():
    root=Path(__file__).resolve().parents[1]
    runner=(root/'run_v0_6D1_R5_2.ps1').read_text(encoding='utf-8')
    assert 'initialization_mode' in runner
    assert 'SPDIST_INITTYPE1_SPTYPE0' in runner
    assert 'v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_' in runner


def test_config_matches_code_frozen_sensitivity():
    root=Path(__file__).resolve().parents[1]
    cfg=json.loads((root/'configs/world1_r52_targeted_expansion_corridors_v0_6D1_R5_2.json').read_text(encoding='utf-8'))
    assert tuple(cfg['habitat_profiles']) == r.HABITAT_PROFILES
    assert cfg['movement_profiles'] == r.MOVEMENT_PROFILES
    assert tuple(cfg['seeds']) == r.SEEDS
    assert cfg['r41_parameter_reuse'] == {'Rmax':r.RMAX,'EmigProb':r.EMIGRATION_PROBABILITY,'K':r.HABITAT_CARRYING_CAPACITY}
    assert cfg['time_mapping']['engine_step_to_arcana_kyr'] == r.ENGINE_STEP_KYR
    assert cfg['time_mapping']['literal_biological_year_claim'] is False
    assert cfg['source_initialization_contract'] == {
        'mode': r.RANGESHIFTER_INITIALIZATION_MODE,
        'InitType': r.RANGESHIFTER_INIT_TYPE,
        'SpType': r.RANGESHIFTER_SP_TYPE,
        'InitDens': r.RANGESHIFTER_INIT_DENS,
        'source': 'GROUP_INPUT_SOURCE_ASC_SPDISTFILE',
        'repair_semantics': 'R52_R1_REPAIR_FREE_INITIALISATION_DEFECT_NO_ORIGIN_HABITAT_MOVEMENT_SEED_OR_TARGET_CHANGED',
    }

def test_contract_forbids_engine_truth_and_literal_time_space_claims():
    root=Path(__file__).resolve().parents[1]
    text=(root/'R5_2_TARGETED_EXPANSION_CORRIDOR_VALIDATION_CONTRACT.md').read_text(encoding='utf-8')
    assert 'does not select origins, targets, corridors, canonical states, or winners' in text
    assert '20,000 biological years' in text and 'not** a claim' in text
    assert 'not geodesic distance' in text
    assert 'do not automatically cause scientific PASS/FAIL' in text
