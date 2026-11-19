"""Small exclusive snapshot archive. No CAS, crash recovery or interpolation."""
from pathlib import Path
import json,hashlib,os,time
import numpy as np
from thermal import encoded,digest,validate

def hashfile(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load_snapshot(path,expected_sha,context):
 raw=Path(path).read_bytes()
 if hashlib.sha256(raw).hexdigest()!=expected_sha:raise ValueError('CHECKPOINT_SHA')
 s=json.loads(raw);validate(s,context);return s

def read_index(root,context):
 root=Path(root);entries=[];parent=None;last=-1
 for line in (root/'index.jsonl').read_text().splitlines():
  e=json.loads(line)
  if e['parent_sha256']!=parent or e['step']<=last or e['column']!=context['column'] or Path(e['file']).name!=e['file']:raise ValueError('CHAIN')
  s=load_snapshot(root/e['file'],e['sha256'],context)
  if e['step']!=s['step'] or e['time_s']!=s['time_s'] or s['parent_snapshot_sha256']!=e['parent_sha256']:raise ValueError('INDEX_STATE')
  entries.append(e);parent=e['sha256'];last=e['step']
 listed={e['file'] for e in entries}
 if {p.name for p in root.glob('snapshot_*.json')}!=listed:raise ValueError('UNCONFIRMED_TAIL')
 return entries

def create(root):
 p=Path(root);p.mkdir();(p/'index.jsonl').open('x').close()

def publish(root,s,context):
 root=Path(root);entries=read_index(root,context);s['parent_snapshot_sha256']=entries[-1]['sha256'] if entries else None;validate(s,context);step=s['step']
 if entries and step<=entries[-1]['step']:raise ValueError('NONADVANCING_SNAPSHOT')
 if not entries and step!=0:raise ValueError('MISSING_T0')
 raw=encoded(s);file=f'snapshot_{step:06d}.json';start=time.perf_counter()
 with (root/file).open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
 e=dict(column=context['column'],step=step,time_s=s['time_s'],time_years=s['time_s']/31557600.,file=file,sha256=hashlib.sha256(raw).hexdigest(),parent_sha256=entries[-1]['sha256'] if entries else None)
 with (root/'index.jsonl').open('ab') as f:f.write(encoded(e)+b'\n');f.flush();os.fsync(f.fileno())
 return dict(bytes=len(raw),write_fsync_s=time.perf_counter()-start,step=step)

def query(root,context,column,time_years,depth_min,depth_max):
 start=time.perf_counter()
 if not np.isfinite([time_years,depth_min,depth_max]).all() or depth_min>depth_max:raise ValueError('QUERY')
 entries=read_index(root,context)
 if column!=context['column']:return dict(status='COLUMN_NOT_ARCHIVED',column=column)
 hits=[e for e in entries if e['time_years']==time_years]
 if not hits:return dict(status='TIME_NOT_ARCHIVED',available_years=[e['time_years'] for e in entries],interpolation_performed=False)
 e=hits[0];s=load_snapshot(Path(root)/e['file'],e['sha256'],context);z=np.array(s['geometry']['z_m']);ids=np.flatnonzero((z>=depth_min)&(z<=depth_max));hi=np.array(s['T_hi_K']);co=np.array(s['T_correction_K'])
 return dict(status='STORED_NODES' if len(ids) else 'NO_STORED_NODES_IN_INTERVAL',column=column,time_years=e['time_years'],time_s=e['time_s'],snapshot_sha256=e['sha256'],parent_sha256=e['parent_sha256'],depth_interval_requested_m=[depth_min,depth_max],interpolation_performed=False,nodes=[dict(index=int(i),depth_m=float(z[i]),T_hi_K=float(hi[i]),T_correction_K=float(co[i]),temperature_K_display=float(np.longdouble(hi[i])-np.longdouble(co[i]))) for i in ids],read_s=time.perf_counter()-start,temperature_representation='physical temperature = hi - correction; display rounded to binary64',boundary_K=context['Dirichlet_K'])
