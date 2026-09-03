from __future__ import annotations
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DATA=Path('/mnt/data')
expected='ARCANA_WorldSim_v0_6_3D2_2_CHA1_High_Resolution_Replay.zip'
candidates=[str(p) for p in DATA.rglob('*.zip') if 'D2_2' in p.name or 'D2.2' in p.name or p.name==expected]
report={
 'status':'BLOCKED_CANONICAL_D22_ARCHIVE_BYTES_NOT_MOUNTED' if not any(Path(x).name==expected for x in candidates) else 'D22_CANDIDATE_FOUND_REQUIRES_HASH_VERIFICATION',
 'expected_filename':expected,
 'expected_sha256':'42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8',
 'expected_bytes':10142030,
 'matching_or_related_zip_paths':candidates,
 'raw_first_action':'DO_NOT_RECONSTRUCT_D2_D22_FROM_SUMMARIES',
 'historical_HX_executed':False,
}
out=ROOT/'outputs/v0_6D1/CURRENT_SESSION_PREFLIGHT_v0_6D1.json'; out.write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
print(json.dumps(report,indent=2,sort_keys=True))
