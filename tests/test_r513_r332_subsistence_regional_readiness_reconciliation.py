from pathlib import Path
import json, shutil
import numpy as np
import pytest

from arcana_worldsim.state_query import r513_r332_subsistence_regional_readiness_reconciliation as r513

PROJECT_ROOT=Path(__file__).resolve().parents[1]

REQUIRED=[
 r513.R512_MANIFEST,r513.R512_AUDIT,r513.R512_HANDOFF,r513.R512_BINDING,
 r513.R512_SOURCE_MANIFEST,r513.R512_SOURCE_MODULE,r513.R512_CONFIG,r513.R512_CONTRACT,
 r513.R330_GROUP,r513.R331_REPLAY,r513.R331_GROUP,
 r513.R332_REPLAY,r513.R332_REGIONAL,r513.R332_AUTHORITY,r513.R332_CHECKPOINT,r513.R332_OUTCOMES,r513.R332_SENSITIVITY,
 r513.R332_AUDIT,r513.R332_OUTPUT_MANIFEST,r513.R332_SEAL_AUDIT,r513.R332_SEAL_MANIFEST,
 r513.R332_SOURCE_MANIFEST,r513.R332_SOURCE_MODULE,r513.R332_CONFIG,r513.R332_CONTRACT,r513.R333_CONTRACT,
 r513.R513_CONFIG,
]

def _copy_tree(tmp:Path)->Path:
 root=tmp/'repo'
 for rel in REQUIRED:
  src=PROJECT_ROOT/rel
  assert src.is_file(), f'missing test source {src}'
  dst=root/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst)
 for drel in (r513.R512_OUT,r513.R332_OUT):
  shutil.copytree(PROJECT_ROOT/drel,root/drel,dirs_exist_ok=True)
 return root

def _rewrite_manifest_entry(root:Path,manifest_rel:Path,file_rel:Path):
 m=json.loads((root/manifest_rel).read_text(encoding='utf-8'))
 p=root/file_rel
 key=file_rel.name
 m['files'][key]={'bytes':p.stat().st_size,'sha256':r513.sha256_file(p)}
 (root/manifest_rel).write_text(json.dumps(m,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')

def test_r513_passes_and_emits_readiness_handoff(tmp_path):
 root=_copy_tree(tmp_path);a=r513.reconcile(root)
 assert a['scientific_candidate_eligible'] and a['checks_passed']==a['checks_total']
 h=json.loads((root/r513.OUT_REL/'R5_13_0KA_SUBSISTENCE_REGIONAL_READINESS_RECONCILED_HANDOFF.json').read_text())
 assert h['candidate_cohort']==list(r513.TARGET_COHORT)
 assert h['managed_resource_transition_pockets_available'] is True
 assert h['transition_pockets_realized_food_production'] is False
 assert h['agriculture_materialized'] is False
 assert h['downstream_r333_auto_authorized'] is False

def test_r332_stock_drift_fails_deterministic_revalidation(tmp_path,monkeypatch):
 root=_copy_tree(tmp_path)
 with np.load(root/r513.R332_REPLAY,allow_pickle=False) as z:d={k:z[k] for k in z.files}
 d['subsistence_domain_stock']=d['subsistence_domain_stock'].copy();d['subsistence_domain_stock'][0,0,0,0]+=0.01
 np.savez_compressed(root/r513.R332_REPLAY,**d)
 _rewrite_manifest_entry(root,r513.R332_OUTPUT_MANIFEST,r513.R332_REPLAY)
 monkeypatch.setattr(r513,'EXPECTED_R332_REPLAY_SHA256',r513.sha256_file(root/r513.R332_REPLAY))
 monkeypatch.setattr(r513,'EXPECTED_R332_OUTPUT_MANIFEST_SHA256',r513.sha256_file(root/r513.R332_OUTPUT_MANIFEST))
 a=r513.reconcile(root)
 assert not a['scientific_candidate_eligible']
 assert 'r332_deterministic_stock_replay_exact' in a['failed']

def test_agriculture_semantic_promotion_fails_closed(tmp_path,monkeypatch):
 root=_copy_tree(tmp_path)
 p=root/r513.R332_AUTHORITY;o=json.loads(p.read_text());o['agriculture_materialized']=True;p.write_text(json.dumps(o,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
 _rewrite_manifest_entry(root,r513.R332_OUTPUT_MANIFEST,r513.R332_AUTHORITY)
 monkeypatch.setattr(r513,'EXPECTED_R332_AUTHORITY_SHA256',r513.sha256_file(root/r513.R332_AUTHORITY))
 monkeypatch.setattr(r513,'EXPECTED_R332_OUTPUT_MANIFEST_SHA256',r513.sha256_file(root/r513.R332_OUTPUT_MANIFEST))
 a=r513.reconcile(root)
 assert not a['scientific_candidate_eligible']
 assert 'r332_no_agriculture_or_domesticated_species' in a['failed']

def test_r512_unique_identity_drift_blocks_parent(tmp_path):
 root=_copy_tree(tmp_path)
 p=root/r513.R512_HANDOFF;h=json.loads(p.read_text());h['unique_human_identity_materialized']=True;p.write_text(json.dumps(h,indent=2,sort_keys=True,ensure_ascii=False)+'\n',encoding='utf-8')
 _rewrite_manifest_entry(root,r513.R512_MANIFEST,r513.R512_HANDOFF)
 a=r513.reconcile(root)
 assert not a['scientific_candidate_eligible']
 assert 'parent_authority_pass' in a['failed']
