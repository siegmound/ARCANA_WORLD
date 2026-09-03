from __future__ import annotations
import json,sys,traceback
from pathlib import Path
out=Path(sys.argv[1]); trees=Path(sys.argv[2]); stdout_file=Path(sys.argv[3])
try:
 import tskit
 ts=tskit.load(str(trees))
 metrics={
   'tree_nodes':int(ts.num_nodes),
   'tree_edges':int(ts.num_edges),
   'tree_individuals':int(ts.num_individuals),
   'tree_mutations':int(ts.num_mutations),
   'sequence_length':float(ts.sequence_length),
   'generations':50,
 }
 result={'status':'PASS' if metrics['tree_nodes']>0 and metrics['tree_edges']>0 and metrics['tree_individuals']>0 else 'FAIL','returncode':0,'metrics':metrics,'slim_stdout_tail':stdout_file.read_text(encoding='utf-8',errors='replace')[-4000:] if stdout_file.exists() else ''}
except Exception as exc:
 result={'status':'FAIL','returncode':1,'metrics':{},'error':repr(exc),'traceback':traceback.format_exc()[-8000:]}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if result['status']!='PASS': raise SystemExit(1)
