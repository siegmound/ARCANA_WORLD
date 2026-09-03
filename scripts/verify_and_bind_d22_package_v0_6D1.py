from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
import executable_historical_binding_v0_6D1 as b

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--d22-zip',required=True); ap.add_argument('--workdir',default='local_runs/v0_6D1/d22_bound')
    a=ap.parse_args(); z=Path(a.d22_zip).resolve(); out=(ROOT/a.workdir).resolve() if not Path(a.workdir).is_absolute() else Path(a.workdir)
    report={'archive':b.verify_canonical_d22_archive(z)}
    ext=b.safe_extract_archive(z,out/'extracted'); raw=b.find_raw_dir(ext)
    report['raw_parity']=b.validate_d22_raw_reference(raw); report['runtime_discovery']=b.discover_runtime_surfaces(ext)
    report['extracted_root']=str(ext); report['raw_dir']=str(raw); report['status']='PASS_D22_EXECUTABLE_PARENT_BINDING_AND_DEEP_OFF_RAW_REFERENCE_PARITY'
    (out/'D22_BINDING_REPORT_v0_6D1.json').write_text(json.dumps(report,indent=2,sort_keys=True),encoding='utf-8')
    print(json.dumps(report,indent=2,sort_keys=True))
if __name__=='__main__': main()
