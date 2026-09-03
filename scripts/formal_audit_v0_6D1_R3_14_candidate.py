from __future__ import annotations
from pathlib import Path
import hashlib, json, sys

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/'src'
if str(SRC) not in sys.path: sys.path.insert(0,str(SRC))
from arcana_worldsim.scientific_engines import r314_late_cenozoic_binding as r314
from arcana_worldsim.late_cenozoic import environment, paleogeography, integrated_provider, adaptive_clock, adaptive_clock_c1, adaptive_clock_c2, late_pleistocene_boundary, production_interface, sealed_120ka_boundary

checks=[]
def ck(name,cond,actual=None,expected=None): checks.append({'name':name,'pass':bool(cond),'actual':actual,'expected':expected})
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
 return h.hexdigest()

cfg=r314.R314Config()
ck('stage',r314.STAGE=='v0.6D1-R3.14',r314.STAGE,'v0.6D1-R3.14')
ck('parent_stage',r314.PARENT_STAGE=='v0.6D1-R3.13_SEALED')
ck('boundary_30Ma',cfg.boundary_age_ma==30.0,cfg.boundary_age_ma,30.0)
ck('biology_not_advanced',cfg.biology_advanced_in_stage is False)
ck('preview_forbidden',cfg.preview_boundary_authorized is False)
parent=r314.validate_parent_r313_authority(ROOT)
ck('parent_age',parent['age_ma']==30.0,parent['age_ma'],30.0)
ck('parent_species',parent['species']==111,parent['species'],111)
ck('parent_components',parent['components']==219,parent['components'],219)
ck('parent_population',abs(parent['population']-1304.4717354192449)<1e-9,parent['population'],1304.4717354192449)

a1=r314.load_a1(ROOT)
ages=[float(x) for x in a1['age_ma']]
ck('a1_30_endpoint',30.0 in ages)
ck('a1_book_endpoint',0.0 in ages)
ck('a1_grid_shape',a1['land_mask'].shape[1:]==(90,180),a1['land_mask'].shape[1:],(90,180))
handoff=r314.r313.validate_30ma_environment_handoff(a1)
ck('r313_handoff_exact',handoff['environmental_endpoint_identity_exact'] is True)
for k,v in handoff['fields'].items():
 ck('handoff_'+k+'_exact',v['exact'] is True)
 ck('handoff_'+k+'_error_zero',v['max_abs_error']==0.0,v['max_abs_error'],0.0)

expected={
 'authorial_seal':'d097f83ce53fb298689c63458dfa1012d26b3983254ccf25085b91f882e55a2a',
 'model_py':'de2399e2b92157ee98d10458db5dcd849b557c076beeed3a648154a6c62e016f',
 'recent_history':'be385c4e41345c9964ac49c695084cf2b37366058b1bc3d9fa22ff39195bb3c1',
 'spatial_snapshots':'a0ecdf8ee18ecb40883973e69b417bea3de7faead2a123a3bb09bd6c740176fd',
 'shoreline':'f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85'}
for k,v in expected.items(): ck('sealed_hash_'+k,r314.EXPECTED_V061_SHA256[k]==v,r314.EXPECTED_V061_SHA256[k],v)
ck('hash_authority_shared',r314.EXPECTED_V061_SHA256==sealed_120ka_boundary.EXPECTED)

for name,status,prefix in [
 ('environment',environment.STATUS,'PASS_LATE_CENOZOIC'),('paleogeography',paleogeography.STATUS,'PASS_LATE_CENOZOIC'),
 ('integrated_provider',integrated_provider.STATUS,'PASS_INTEGRATED_LATE_CENOZOIC'),('adaptive_clock',adaptive_clock.STATUS,'PASS_ADAPTIVE_CLOCK_STRUCTURE'),
 ('adaptive_clock_c1',adaptive_clock_c1.STATUS,'PASS_ADAPTIVE_CLOCK_WITH_AUTHORIZED_CHA2'),('adaptive_clock_c2',adaptive_clock_c2.STATUS,'PASS_ADAPTIVE_CLOCK_WITH_200_120KA'),
 ('late_pleistocene',late_pleistocene_boundary.STATUS,'PASS_200_120KA'),('production_interface',production_interface.STATUS,'PASS_v0_6_4D'),
 ('sealed_120ka',sealed_120ka_boundary.STATUS,'PASS_EXACT_SEALED_120KA')]:
 ck('module_status_'+name,str(status).startswith(prefix),status,prefix)

src=(ROOT/'src/arcana_worldsim/scientific_engines/r314_late_cenozoic_binding.py').read_text()
ck('no_preview_call_in_binding','preview_boundary_from_book_reference' not in src)
ck('exact_discovery_used','discover_exact_v061' in src)
ck('B1_rematerialized','reconstruct_v061_spatial_at_year' in src and 'remap_exact_120ka_to_a1' in src)
ck('C1_constructed','IntegratedLateCenozoicProviderC1' in src)
ck('C2_constructed','IntegratedLateCenozoicProviderC2' in src)
ck('C2_clock_constructed','build_adaptive_late_cenozoic_clock_c2' in src)
ck('production_ready_required','production_replay_ready' in src)
ck('biology_runtime_not_imported','advance_state(' not in src and 'run_rebased_natural_control' not in src)
ck('deep_runtime_not_imported','import deep_' not in src.lower() and 'from deep_' not in src.lower())

# Fail-closed smoke using a deliberately empty search root.
import tempfile
with tempfile.TemporaryDirectory() as td:
 proof=r314.discover_exact_v061([Path(td)],Path(td)/'bound')
 ck('empty_search_fails_closed',proof is None)
 ck('empty_search_no_proxy_created',not (Path(td)/'bound').exists())

files=[
 'src/arcana_worldsim/scientific_engines/r314_late_cenozoic_binding.py',
 'scripts/run_v0_6D1_R3_14_late_cenozoic_binding.py','tests/test_r314_late_cenozoic_binding.py',
 'configs/world1_r314_late_cenozoic_binding_v0_6D1_R3_14.json','run_v0_6D1_R3_14_late_cenozoic_binding.ps1','run_v0_6D1_R3_14_checks.ps1']
for f in files: ck('file_exists::'+f,(ROOT/f).is_file())

passed=sum(x['pass'] for x in checks); total=len(checks)
res={'schema':'ARCANA_R314_CANDIDATE_FORMAL_AUDIT_V1','stage':r314.STAGE,'verdict':'PASS_R314_CANDIDATE_PROVIDER_BINDING_GATE__LOCAL_EXACT_V061_REHYDRATION_REQUIRED' if passed==total else 'FAIL_R314_CANDIDATE_AUDIT','checks_passed':passed,'checks_total':total,'all_pass':passed==total,'parent_r313':parent,'source_hashes':{f:sha(ROOT/f) for f in files},'checks':checks}
out=ROOT/'outputs/v0_6D1_R3_14/FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_14.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(res,indent=2))
print(json.dumps({'verdict':res['verdict'],'checks':f'{passed}/{total}','out':str(out)},indent=2))
raise SystemExit(0 if passed==total else 1)
