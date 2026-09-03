from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r37f_stress_window_shadow_replay import R37FStressWindowConfig

checks=[]
def check(name, cond, detail=None):
    checks.append({"name":name,"pass":bool(cond),"detail":detail})

cfg=R37FStressWindowConfig()
check("stage_window_start", cfg.start_age_ma == 210.0)
check("stage_window_end", cfg.end_age_ma == 188.0)
check("biology_steps_176", round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years) == 176)
check("crosses_legacy_clip_onset", cfg.end_age_ma < 191.25 < cfg.start_age_ma)
check("K_low", abs(cfg.adaptive_k_low-37.614)<1e-12)
check("K_center", abs(cfg.adaptive_k_center-38.470)<1e-12)
check("K_high", abs(cfg.adaptive_k_high-41.002)<1e-12)
check("K_order", cfg.adaptive_k_low < cfg.adaptive_k_center < cfg.adaptive_k_high)
check("ceiling_unchanged", abs(cfg.variance_ceiling_normalized-0.08)<1e-15)
check("biology_cadence_unchanged", abs(cfg.biology_cadence_years-125000.0)<1e-12)
check("transport_cadence_unchanged", abs(cfg.transport_cadence_years-62500.0)<1e-12)
check("mu_unchanged", abs(cfg.mutation_variance_supply_normalized_per_myr-0.002)<1e-15)
check("b_unchanged", abs(cfg.nonlinear_stabilizing_variance_depletion_per_myr_per_q-0.9876543209876544)<1e-15)
check("recombination_reference_half", abs(cfg.shadow_recombination_fraction_per_generation-0.5)<1e-15)

# Parent R3.7E package-manifest entries must remain byte-identical.
parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7E.json').read_text(encoding='utf-8'))
parent_bad=[]
for rec in parent['files']:
    rel=rec['path']; expected=rec['sha256']
    p=ROOT/rel
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if actual != expected:
        parent_bad.append({"path":rel,"expected":expected,"actual":actual})
check("parent_r37e_file_count_3283", len(parent['files'])==3283, len(parent['files']))
check("parent_r37e_all_files_unchanged", not parent_bad, parent_bad[:10])

# Full R3.7E local evidence is embedded and independently summarized.
evp=ROOT/'references/v0_6D1_R3_7E/v0_6D1_R3_7E_FULL_LOCAL_RESULTS.zip'
eva=ROOT/'outputs/v0_6D1_R3_7F/R3_7E_FULL_LOCAL_EVIDENCE_AUDIT.json'
check("r37e_full_result_zip_present", evp.exists())
check("r37e_full_evidence_audit_present", eva.exists())
if evp.exists() and eva.exists():
    evidence=json.loads(eva.read_text(encoding='utf-8'))
    actual=hashlib.sha256(evp.read_bytes()).hexdigest()
    check("r37e_result_zip_hash", actual==evidence['source_zip_sha256'], {"actual":actual,"expected":evidence['source_zip_sha256']})
    check("r37e_40_steps", evidence['biology_steps']==40)
    check("r37e_canonical_parity", evidence['canonical_parity'] is True)
    check("r37e_zero_ceiling_contacts", all(v==0 for v in evidence['ceiling_contacts'].values()))
    check("r37e_q_spread_zero", evidence['max_K_envelope_q_spread']==0.0)
    check("r37e_S_spread_nonzero", evidence['k_sensitivity']['same_species_S_median']['maximum_absolute_K_spread']>0)
    check("r37e_h_spread_nonzero", evidence['k_sensitivity']['adaptive_coordinate_abs_max']['maximum_absolute_K_spread']>0)

for doc in [
    'src/arcana_worldsim/scientific_engines/r37f_stress_window_shadow_replay.py',
    'scripts/run_v0_6D1_R3_7F_stress_shadow.py',
    'tests/test_r37f_stress_window_shadow.py',
    'configs/world1_stress_window_adaptive_genetic_shadow_replay_v0_6D1_R3_7F.json',
    'SHORT_WORLD1_STRESS_WINDOW_SHADOW_REPLAY_CONTRACT_v0_6D1_R3_7F.md',
    'R3_7E_FULL_LOCAL_EVIDENCE_AUDIT.md',
    'README_R3_7F.md',
    'V0_6D1_R3_7F_STATUS.md',
    'NEXT_STAGE_HANDOFF_v0_6D1_R3_7F.md',
    'run_v0_6D1_R3_7F_stress_shadow.ps1',
    'run_v0_6D1_R3_7F_smoke.ps1',
]:
    check('exists_'+doc, (ROOT/doc).exists())

# Fail-closed governance must be explicitly present in source and contract.
src=(ROOT/'src/arcana_worldsim/scientific_engines/r37f_stress_window_shadow_replay.py').read_text(encoding='utf-8')
contract=(ROOT/'SHORT_WORLD1_STRESS_WINDOW_SHADOW_REPLAY_CONTRACT_v0_6D1_R3_7F.md').read_text(encoding='utf-8')
check("source_requires_legacy_clipping_reproduction", 'legacy_clipping_reproduced' in src)
check("source_requires_shadow_clear", 'shadow_all_variants_clear_of_ceiling' in src)
check("source_production_runtime_denied", '"production_runtime_replacement_authorized": False' in src)
check("source_scalar_K_denied", '"scalar_K_eff_production_authorized": False' in src)
check("source_mu_b_ceiling_change_denied", '"mu_b_or_ceiling_change_authorized": False' in src)
check("contract_no_arbitrary_S_threshold", 'No arbitrary tolerance is imposed on S' in contract)

ok=all(c['pass'] for c in checks)
out={"stage":"v0.6D1-R3.7F","status":"PASS" if ok else "FAIL","check_count":len(checks),"checks":checks}
od=ROOT/'outputs/v0_6D1_R3_7F'; od.mkdir(parents=True,exist_ok=True)
(od/'FORMAL_AUDIT_v0_6D1_R3_7F.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({"status":out['status'],"checks_passed":sum(c['pass'] for c in checks),"check_count":len(checks)},indent=2))
raise SystemExit(0 if ok else 2)
