from __future__ import annotations
import json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
import executable_historical_binding_v0_6D1 as b
checks={
 'canonical_D22_hash_pinned':len(b.EXPECTED_D22_SHA256)==64,
 'canonical_D22_size_pinned':b.EXPECTED_D22_BYTES==10142030,
 'canonical_survivors_31':len(b.EXPECTED_SURVIVORS)==31 and len(set(b.EXPECTED_SURVIVORS))==31,
 'raw_products_12':len(b.REQUIRED_RAW_BASENAMES)==12,
 'no_summary_reconstruction':b.GOVERNANCE['reconstruct_D2_from_summaries'] is False,
 'no_direct_survivor_selector':b.GOVERNANCE['direct_Deep_survivor_selector'] is False,
 'no_direct_speciation':b.GOVERNANCE['direct_Deep_speciation'] is False,
 'no_named_protection':b.GOVERNANCE['named_survivor_protection'] is False,
 'HSG025_proxy_forbidden_historical_HX':b.GOVERNANCE['HSG025_proxy_allowed_in_historical_HX'] is False,
 'full_HX_requires_preCHA1_runtime':b.GOVERNANCE['full_HX_allowed_without_preCHA1_executable_runtime'] is False,
}
res={'status':'PASS_V0_6D1_BINDER_GOVERNANCE_AUDIT' if all(checks.values()) else 'FAIL','passed':sum(checks.values()),'total':len(checks),'checks':checks}
(ROOT/'outputs/v0_6D1/FORMAL_AUDIT_v0_6D1.json').write_text(json.dumps(res,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(res,indent=2,sort_keys=True)); raise SystemExit(0 if all(checks.values()) else 1)
