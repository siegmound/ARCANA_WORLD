from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.late_cenozoic import sealed_120ka_boundary as b1
from arcana_worldsim.late_cenozoic.cha2_nested_50y import CHA2Nested50YRecentProvider, _canonical_freshwater_pulse
from arcana_worldsim.late_cenozoic import cha2_hydrological_hazard as r320

EXPECTED_C1_SHA = "d0b121f0b0fe7214d6c6f4736176d1c64f419c77dd991659291fe12b633ada0f"
EXPECTED_R319_JSON = "658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71"
EXPECTED_R319_NPZ = "f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406"
EXPECTED_R319_VERDICT = "PASS_R319_CANONICAL_125KA_TO_0_H0_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY__0KA_NATURAL_CONTROL_BIOLOGY_BOUNDARY_SEALED"

checks = []
failed = []
def ck(name, cond, detail=None):
    ok = bool(cond)
    checks.append({"name": name, "pass": ok, "detail": detail})
    if not ok: failed.append(name)
    return ok

def hfile(p):
    h=sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
    return h.hexdigest()

# Source/config governance.
mod = ROOT/'src/arcana_worldsim/late_cenozoic/cha2_hydrological_hazard.py'
c1p = ROOT/'src/arcana_worldsim/late_cenozoic/cha2_nested_50y.py'
cfgp = ROOT/'configs/world1_r320_cha2_yd_hydrological_hazard_v0_6D1_R3_20.json'
ck('r320_source_exists', mod.is_file())
ck('c1_authority_exists', c1p.is_file())
ck('c1_authority_hash_frozen', hfile(c1p)==EXPECTED_C1_SHA, hfile(c1p))
conf=json.loads(cfgp.read_text())
ck('stage_exact', conf['stage']=='v0.6D1-R3.20')
ck('audit_revision_r1_exact', conf.get('audit_revision')=='R1_METRIC_AND_PARENT_SCHEMA_REPAIR', conf.get('audit_revision'))
ck('50y_cadence_exact', conf['hazard_step_years']==50)
ck('global_low_order_scalar_not_hard_magnitude_gate', conf.get('yd_class_hard_gate_global_low_order_scalar_magnitude') is False)
ck('event_exit_timing_not_hard_gate', conf.get('yd_class_event_exit_timing_is_hard_gate') is False)
for k in ('impact_origin_required','human_population_used','settlement_target_used','flood_myth_target_used','religion_target_used','biology_modified','cha2_c1_modified'):
    ck('config_'+k+'_false', conf[k] is False)
src=mod.read_text(encoding='utf-8')
ck('no_random_source', 'np.random' not in src and 'random.' not in src)
ck('no_biology_advance', 'advance_state(' not in src)
ck('no_population_argument', 'population' not in src.lower() or 'human_population_used' in src)
ck('hazard_is_derived', 'DERIVED_DIAGNOSTIC_LAYER_OVER_SEALED_CHA2_C1' in src)
ck('r1_global_scalar_semantics_present', 'global_temperature_scalar_magnitude_is_hard_gate' in src)
ck('r1_full_recovery_diagnostic_semantics_present', 'full_90pct_overturning_recovery_is_hard_gate' in src)
ck('no_legacy_global_magnitude_threshold', 'min_global_cooling_c' not in src and 'max_global_cooling_c' not in src)

# Canonical forcing itself must already sit in the expected YD forcing class.
t=np.arange(-15000,-10999,1,dtype=float); f=_canonical_freshwater_pulse(t); i=int(np.argmax(f))
ck('canonical_freshwater_peak_timing', -13000 <= t[i] <= -12800, float(t[i]))
ck('canonical_freshwater_peak_magnitude', 0.18 <= f[i] <= 0.21, float(f[i]))

# Parent R3.19 sealed authority.
sealp=ROOT/'R3_19_SEAL_SUMMARY.json'
jp=ROOT/'local_runs/v0_6D1_R3_19/WORLD1_H0_0KA_PHASE_AWARE_TRANSPORT_FIXED_BIOLOGY_CHECKPOINT_v0_6D1_R3_19.json'
npzp=jp.with_suffix('.npz')
ck('r319_seal_materialized', sealp.is_file())
ck('r319_checkpoint_json_materialized', jp.is_file())
ck('r319_checkpoint_npz_materialized', npzp.is_file())
if sealp.is_file():
    s=json.loads(sealp.read_text())
    ck('r319_seal_verdict', s.get('verdict')==EXPECTED_R319_VERDICT, s.get('verdict'))
    seal_checks = s.get('formal_audit_checks', s.get('checks'))
    ck('r319_seal_checks_73_73', str(seal_checks)=='73/73', seal_checks)
if jp.is_file(): ck('r319_json_hash', hfile(jp)==EXPECTED_R319_JSON, hfile(jp))
if npzp.is_file(): ck('r319_npz_hash', hfile(npzp)==EXPECTED_R319_NPZ, hfile(npzp))

# Exact v0.6.1 binding and live physical magnitude audit.
sealed_root=ROOT/'local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL'
a1p=ROOT/'references/v0_6D1_R3/FULL_A1_REFERENCE_210_0Ma.npz'
ck('a1_materialized', a1p.is_file())
ck('v061_binding_materialized', sealed_root.is_dir())
mag=None
if a1p.is_file() and sealed_root.is_dir():
    try:
        hashes=b1.verify_v061_sealed_root(sealed_root)
        for key,want in b1.EXPECTED.items(): ck('v061_'+key+'_hash', hashes.get(key)==want, hashes.get(key))
        z=np.load(a1p,allow_pickle=False); a1={k:z[k] for k in z.files}
        provider=CHA2Nested50YRecentProvider(a1,sealed_root)
        mag=r320.audit_younger_dryas_class_magnitude(provider,a1)
        for name,ok in mag['checks'].items(): ck('live_magnitude_'+name, ok, mag['metrics'])
        snap=r320.hydrological_hazard_snapshot(provider,a1,-12900)
        for k in ('pluvial_flood_potential_index','coastal_inundation_potential_index','compound_flood_hazard_index','hydrological_disruption_index'):
            a=np.asarray(snap[k],float)
            ck('live_hazard_'+k+'_finite', np.all(np.isfinite(a)))
            ck('live_hazard_'+k+'_bounded', np.min(a)>=0 and np.max(a)<=1, [float(np.min(a)),float(np.max(a))])
        ck('live_hazard_population_free', snap['human_population_used'] is False)
        ck('live_hazard_myth_free', snap['flood_myth_target_used'] is False)
    except Exception as exc:
        ck('live_provider_and_magnitude_audit', False, repr(exc))

verdict = ('PASS_R320_CANDIDATE_FORMAL_AUDIT__CHA2_YD_CLASS_MAGNITUDE_CONFIRMED_HYDROLOGICAL_HAZARD_RUN_READY'
           if not failed else 'FAIL_R320_CANDIDATE_FORMAL_AUDIT')
out={
    'schema':'ARCANA_R320_FORMAL_CANDIDATE_AUDIT_V1','stage':'v0.6D1-R3.20','verdict':verdict,
    'checks':f"{len(checks)-len(failed)}/{len(checks)}",'failed':failed,'check_records':checks,
    'live_magnitude_audit':mag,
    'decision':'PRESERVE_SEALED_CHA2_C1_AND_ADD_DERIVED_50Y_HYDROLOGICAL_HAZARD_ONLY',
    'scientific_parameter_changes':False,'biology_changes':False,'r319_state_changes':False,
    'human_or_cultural_calibration_targets':False,
}
outp=ROOT/'outputs/v0_6D1_R3_20/FORMAL_AUDIT_CANDIDATE_v0_6D1_R3_20.json'; outp.parent.mkdir(parents=True,exist_ok=True); outp.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'verdict':verdict,'checks':out['checks'],'failed':failed,'magnitude':None if mag is None else mag['metrics'],'out':str(outp)},indent=2))
raise SystemExit(0 if not failed else 1)
