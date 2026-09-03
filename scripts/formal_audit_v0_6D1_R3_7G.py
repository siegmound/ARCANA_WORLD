from __future__ import annotations
import hashlib, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from arcana_worldsim.scientific_engines.r37g_production_validation import R37GProductionValidationConfig

checks=[]
def check(name, cond, detail=None):
    checks.append({"name":name,"pass":bool(cond),"detail":detail})

cfg=R37GProductionValidationConfig()
check("stage_window_start", cfg.start_age_ma == 210.0)
check("stage_window_end", cfg.end_age_ma == 150.0)
check("biology_steps_480", round((cfg.start_age_ma-cfg.end_age_ma)*1e6/cfg.biology_cadence_years) == 480)
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

# Parent R3.7F package-manifest entries remain byte-identical.
parent=json.loads((ROOT/'PACKAGE_MANIFEST_v0_6D1_R3_7F.json').read_text(encoding='utf-8'))
parent_bad=[]
for rec in parent['files']:
    rel=rec['path']; expected=rec['sha256']; p=ROOT/rel
    actual=hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
    if actual != expected:
        parent_bad.append({"path":rel,"expected":expected,"actual":actual})
check("parent_r37f_file_count_3346", len(parent['files'])==3346, len(parent['files']))
check("parent_r37f_all_files_unchanged", not parent_bad, parent_bad[:10])

# Full R3.7F local evidence is embedded and reviewed.
evp=ROOT/'references/v0_6D1_R3_7F/v0_6D1_R3_7F_FULL_LOCAL_RESULTS.zip'
eva=ROOT/'outputs/v0_6D1_R3_7G/R3_7F_FULL_LOCAL_EVIDENCE_AUDIT.json'
check("r37f_full_result_zip_present", evp.exists())
check("r37f_full_evidence_audit_present", eva.exists())
if evp.exists() and eva.exists():
    evidence=json.loads(eva.read_text(encoding='utf-8'))
    actual=hashlib.sha256(evp.read_bytes()).hexdigest()
    check("r37f_result_zip_hash", actual==evidence['source_zip_sha256'], {"actual":actual,"expected":evidence['source_zip_sha256']})
    check("r37f_176_steps", evidence['biology_steps']==176)
    check("r37f_canonical_parity", evidence['canonical_parity'] is True)
    check("r37f_legacy_clipping_reproduced", evidence['legacy']['steps_with_clipping']>0)
    check("r37f_first_clip_191p25", abs(evidence['legacy']['first_clipping_age_ma']-191.25)<1e-12)
    check("r37f_zero_shadow_ceiling_contacts", all(v==0 for v in evidence['shadow']['ceiling_contacts'].values()))
    check("r37f_shadow_peak_below_ceiling", max(evidence['shadow']['peak_q'].values()) < 0.08)
    check("r37f_headroom_gain_positive", evidence['shadow']['headroom_gain_vs_legacy_peak_q']>0)
    check("r37f_governed_stress_pass", evidence['stress_gate']['governed_stress_pass'] is True)
    check("r37f_S_spread_real", evidence['k_sensitivity']['same_species_S_max']['final_relative_span_vs_abs_center']>0)
    check("r37f_h_spread_real", evidence['k_sensitivity']['adaptive_coordinate_abs_max']['final_relative_span_vs_abs_center']>0)
    check("r37f_scalar_K_still_denied", evidence['production_binding_readiness']['scalar_K_eff_authorized'] is False)

# Diagnostic R3.7G smoke proves wrapper execution/parity but cannot satisfy the full historical gate.
smoke=ROOT/'outputs/v0_6D1_R3_7G/smoke/210_to_209p0Ma_R3_7G_summary.json'
check("r37g_smoke_present", smoke.exists())
if smoke.exists():
    sm=json.loads(smoke.read_text(encoding='utf-8'))
    check("r37g_smoke_8_steps", sm['production_validation_gate']['expected_biology_steps']==8)
    check("r37g_smoke_canonical_parity", sm['canonical_parity']['all_core_parity'] is True)
    check("r37g_smoke_zero_shadow_contacts", all(v==0 for v in sm['shadow']['ceiling_contacts_by_variant'].values()))
    check("r37g_smoke_positive_center_headroom", sm['center_headroom_to_existing_ceiling']>0)
    check("r37g_smoke_full_gate_correctly_false", sm['production_validation_gate']['governed_validation_pass'] is False)

for doc in [
    'src/arcana_worldsim/scientific_engines/r37g_production_validation.py',
    'scripts/run_v0_6D1_R3_7G_production_validation.py',
    'scripts/formal_audit_v0_6D1_R3_7G.py',
    'tests/test_r37g_production_validation.py',
    'configs/world1_production_binding_validation_v0_6D1_R3_7G.json',
    'PRODUCTION_BINDING_READINESS_CONTRACT_v0_6D1_R3_7G.md',
    'R3_7F_FULL_LOCAL_EVIDENCE_AUDIT.md',
    'R3_7G_DIAGNOSTIC_SMOKE_AUDIT.md',
    'README_R3_7G.md',
    'V0_6D1_R3_7G_STATUS.md',
    'NEXT_STAGE_HANDOFF_v0_6D1_R3_7G.md',
    'run_v0_6D1_R3_7G_production_validation.ps1',
    'run_v0_6D1_R3_7G_smoke.ps1',
    'run_v0_6D1_R3_7G_checks.ps1',
]:
    check('exists_'+doc, (ROOT/doc).exists())

src=(ROOT/'src/arcana_worldsim/scientific_engines/r37g_production_validation.py').read_text(encoding='utf-8')
contract=(ROOT/'PRODUCTION_BINDING_READINESS_CONTRACT_v0_6D1_R3_7G.md').read_text(encoding='utf-8')
check("source_requires_canonical_parity", 'canonical_parity' in src)
check("source_requires_legacy_clipping", 'legacy_clipping_reproduced' in src)
check("source_requires_all_shadow_clear", 'shadow_all_variants_clear_of_ceiling' in src)
check("source_requires_positive_center_headroom", 'center_positive_headroom_to_existing_ceiling' in src)
check("source_keeps_K_center_nominal_only", 'NOMINAL_VALIDATION_BRANCH_NOT_CANONICAL_CONSTANT' in src)
check("source_production_runtime_denied", '"production_runtime_replacement_authorized": False' in src)
check("source_scalar_K_denied", '"scalar_K_eff_production_authorized": False' in src)
check("source_mu_b_ceiling_change_denied", '"mu_b_or_ceiling_change_authorized": False' in src)
check("contract_no_new_S_threshold", 'No new fitted tolerance is imposed on S' in contract)
check("contract_pass_not_auto_promotion", 'not automatic replacement' in contract)

ok=all(c['pass'] for c in checks)
out={"stage":"v0.6D1-R3.7G","status":"PASS" if ok else "FAIL","check_count":len(checks),"checks":checks}
od=ROOT/'outputs/v0_6D1_R3_7G'; od.mkdir(parents=True,exist_ok=True)
(od/'FORMAL_AUDIT_v0_6D1_R3_7G.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({"status":out['status'],"checks_passed":sum(c['pass'] for c in checks),"check_count":len(checks)},indent=2))
raise SystemExit(0 if ok else 2)
