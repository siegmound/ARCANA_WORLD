from __future__ import annotations
import argparse, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/'src'))
import executable_historical_binding_v0_6D1 as b

def main():
    ap=argparse.ArgumentParser(description='v0.6D1 historical HX pilot gate. Does not reconstruct missing D1/D2 state.')
    for x in ('d22_zip','d1_zip','d2_precha1_zip','d1_population_state','d1_variance_state'):
        ap.add_argument('--'+x.replace('_','-'),required=True)
    ap.add_argument('--adapter-command',nargs='+',help='Explicit verified historical adapter command supplied after source inspection.')
    ap.add_argument('--cwd',default='.')
    a=ap.parse_args()
    b.require_historical_hx_inputs(d22_archive=Path(a.d22_zip),d1_archive=Path(a.d1_zip),d2_precha1_archive=Path(a.d2_precha1_zip),d1_population_state=Path(a.d1_population_state),d1_variance_state=Path(a.d1_variance_state))
    d22=b.verify_canonical_d22_archive(Path(a.d22_zip))
    if not a.adapter_command:
        raise b.BindingError('historical inputs exist but no inspected executable adapter command was supplied: FAIL_CLOSED')
    result=b.run_external_command(a.adapter_command,Path(a.cwd).resolve())
    print(json.dumps({'status':'HX_PILOT_EXTERNAL_ADAPTER_COMPLETED_REQUIRES_OUTPUT_PARITY_AUDIT','d22':d22,'run':result},indent=2))
if __name__=='__main__': main()
