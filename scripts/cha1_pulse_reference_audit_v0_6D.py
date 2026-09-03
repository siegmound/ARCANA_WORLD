from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from historical_deep_bridge_v0_6D import validate_cha1_reference_against_v05, cha1_surface_pulse_energy_by_mode
stats=json.loads((ROOT/'references'/'CHA1_HIGH_RES_EXPOSURE_STATS_v0_5.json').read_text())
modes=['E','th','p','I','N']
y=np.asarray([float(r['years_after_CHA1']) for r in stats],float)
ref=np.asarray([[float(r['energy_ledger']['mode_cha1_surface_remaining_j'][m]) for m in modes] for r in stats],float)
d=validate_cha1_reference_against_v05(y,ref)
# exact event-relative pulse is preferred; record the age-coordinate materialization delta, don't hide it.
report={'status':'PASS_CHA1_EXACT_EVENT_TIME_PULSE_REFERENCE_AUDIT','mode_order':modes,**d,
        'exact_event_time_preferred':True,
        'v05_materialization_note':'v0.5 reporting reconstructs event time through age_Ma; sub-1e-9 relative differences are floating-coordinate roundoff, not changed physics',
        'pulse_before_impact_j':cha1_surface_pulse_energy_by_mode(-1.0).tolist(),
        'pulse_at_impact_total_j':float(cha1_surface_pulse_energy_by_mode(0.0).sum()),
        'checkpoint_years':y.tolist()}
(ROOT/'outputs'/'CHA1_PULSE_REFERENCE_AUDIT_v0_6D.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
