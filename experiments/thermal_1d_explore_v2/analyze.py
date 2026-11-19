"""Offline saved-data comparisons and independent short-time interface oracle."""
from pathlib import Path
import json,csv,hashlib,sys
import numpy as np
p=Path(sys.argv[1]);d=json.loads((p/'run02/RESULT.json').read_text());a=json.loads((p/'extra01/RESULT.json').read_text());r=json.loads((p/'SELECTED_INPUTS.json').read_text())['hot_C028'];out=[]
for k in (2.,3.):
 t=10*31557600.;rate=r['transient_rate_k_s'];q=r['moho_flux_w_m2'];ec=np.sqrt(k*2800*1000);em=np.sqrt(3.3*3300*1200);rc=(k/2.5*(2800*1000*rate-8e-7)+8e-7)/(2800*1000)
 expected=2*np.sqrt(t/np.pi)*(q-q*k/2.5)/(ec+em)+(ec*rc+em*rate)/(ec+em)*t-rate*t
 for x in a['Moho_k_sensitivity']:
  if x['k_C']==k:out.append(dict(k_C=k,dx=x['dx_Moho_m'],independent_two_halfspace_effect_K=float(expected),numerical_effect_K=x['effect_at_Moho_K'],error_K=float(abs(x['effect_at_Moho_K']-expected))))
(p/'MOHO_HALFSPACE_ORACLE.json').write_text(json.dumps(out,indent=2))
orders=[]
for label in ('distinct_continent','hot_C028'):
 z=[x for x in d['graded_references'] if x['column']==label]
 for i in (0,1):orders.append(dict(column=label,dx_from=z[i]['dx_m'],dx_to=z[i+1]['dx_m'],L2_order=float(np.log2(z[i]['global_error']['L2']/z[i+1]['global_error']['L2'])),Linf_order=float(np.log2(z[i]['global_error']['Linf']/z[i+1]['global_error']['Linf']))))
for k in (2.,3.):
 z=[x for x in out if x['k_C']==k]
 for i in (0,1):orders.append(dict(column='Moho_k'+str(k),dx_from=z[i]['dx'],dx_to=z[i+1]['dx'],Linf_order=float(np.log2(z[i]['error_K']/z[i+1]['error_K']))))
(p/'RESOLVED_SPATIAL_ORDERS.json').write_text(json.dumps(orders,indent=2))
with (p/'COMPARISON.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['column','nodes','steps','spatial_L2_K','spatial_Linf_K','temporal_L2_K','energy_residual_J_m2','CFL_ratio'])
 for x in d['rows']:w.writerow([x['column'],x['nodes'],x['steps'],x['spatial']['L2'],x['spatial']['Linf'],x['temporal']['L2'],x['ledger_residual_J_m2'],x['CFL_ratio']])
catalog=[];audit=[]
for f in sorted(p.rglob('*.npz')):
 with np.load(f,allow_pickle=False) as ar:
  for name in ar.files:
   x=ar[name];catalog.append(dict(file=str(f.relative_to(p)),field=name,shape=list(x.shape),dtype=str(x.dtype),raw_sha256=hashlib.sha256(x.tobytes()).hexdigest()))
  if 'history' in ar:
   assert np.isfinite(ar['history']).all() and np.min(ar['history'])>0
   assert np.array_equal(ar['history'][:,0],np.full(len(ar['history']),ar['T0'][0]))
   assert np.array_equal(ar['history'][:,-1],np.full(len(ar['history']),ar['T0'][-1]))
   assert np.array_equal(ar['history'][-1],ar['T']);assert np.all(abs(ar['ledger'][:,2])<=ar['ledger'][:,3])
   if 'reference_increment' in ar:ref=ar['reference_increment']
   else:ref=ar['semidiscrete_increment']
   audit.append(dict(file=str(f.relative_to(p)),trajectory='PASS',ledger='PASS',temporal_Linf_K=float(max(abs(ar['T'].astype(np.longdouble)-ar['T0'].astype(np.longdouble)-ref)))))
(p/'ARRAY_CATALOG.json').write_text(json.dumps(catalog,indent=2));(p/'SAVED_STATE_AUDIT.json').write_text(json.dumps(audit,indent=2))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
fig,axes=plt.subplots(1,2,figsize=(10,4))
for label in ('hot_C028','distinct_continent'):
 z=[x for x in d['graded_references'] if x['column']==label];axes[0].loglog([x['dx_m'] for x in z],[x['global_error']['Linf'] for x in z],'o-',label=label)
for k in (2.,3.):
 z=[x for x in out if x['k_C']==k];axes[1].loglog([x['dx'] for x in z],[x['error_K'] for x in z],'o-',label=f'k crust={k}')
for ax in axes:ax.set_xlabel('Local spacing (m)');ax.set_ylabel('Linf error (K)');ax.grid(True);ax.legend()
axes[0].set_title('Resolved Dirichlet layers, 10 model years');axes[1].set_title('Moho parameter step vs half-space oracle');fig.tight_layout();fig.savefig(p/'RESOLVED_ERRORS.png',dpi=160)
print(json.dumps(dict(orders=orders,array_fields=len(catalog),trajectories=len(audit))))
