"""Experimental compensated 1D thermal state; no production providers imported."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
YEAR=31557600.
def encoded(x):return json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(x):return hashlib.sha256(encoded(x)).hexdigest()
def source_identity():return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob('*.py'))}
def runtime():return dict(python=sys.version,numpy=np.__version__,longdouble_mantissa=int(np.finfo(np.longdouble).nmant),byteorder=sys.byteorder)
def properties(z,H,m):
 z=np.asarray(z,float);m=np.asarray(m,float)
 if z.ndim!=1 or len(z)<3 or not np.isfinite(z).all() or z[0]!=0 or np.any(np.diff(z)<=0) or H not in z or not 0<H<z[-1]:raise ValueError('GEOMETRY')
 if m.shape!=(2,4) or not np.isfinite(m).all() or np.any(m[:,:3]<=0) or np.any(m[:,3]<0):raise ValueError('MATERIALS')
 edges=np.r_[0.,(z[:-1]+z[1:])/2,z[-1]];dc=np.clip(H-edges[:-1],0,np.diff(edges));dm=np.diff(edges)-dc
 C=dc*m[0,1]*m[0,2]+dm*m[1,1]*m[1,2];S=dc*m[0,3]+dm*m[1,3]
 lc=np.clip(H-z[:-1],0,np.diff(z));g=1/(lc/m[0,0]+(np.diff(z)-lc)/m[1,0])
 return dict(z_m=z.tolist(),dual_edges_m=edges.tolist(),dual_volume_per_unit_area_m=np.diff(edges).tolist(),capacity_J_m2_K=C.tolist(),source_W_m2=S.tolist(),conductance_W_m2_K=g.tolist(),materials_k_rho_Cp_A=m.tolist(),Moho_m=float(H))
def current_flux(s):
 hi=np.array(s['T_hi_K'],np.longdouble);co=np.array(s['T_correction_K'],np.longdouble)
 return np.asarray(np.asarray(s['geometry']['conductance_W_m2_K'])* (np.diff(hi)-np.diff(co)),dtype=float)
def initial(geometry,T0,context):
 dt=context['duration_s']/context['steps'];C=np.array(geometry['capacity_J_m2_K']);g=np.array(geometry['conductance_W_m2_K']);limit=float(min(C[1:-1]/(g[:-1]+g[1:])))
 if dt>.8*limit or context['duration_s']>10*YEAR:raise ValueError('PLAN_CFL_OR_DURATION')
 s=dict(schema='THERMAL_HISTORY_STATE_V1',parent_snapshot_sha256=None,context=context,geometry=geometry,initial_T_K=list(map(float,T0)),T_hi_K=list(map(float,T0)),T_correction_K=[0.]*len(T0),time_s=0.,step=0,dt_s=dt,CFL_s=limit,ledger=[],last_step_flux_W_m2=None,current_flux_W_m2=[])
 s['current_flux_W_m2']=current_flux(s).tolist();validate(s,context);return s

def validate(s,expected):
 if s['schema']!='THERMAL_HISTORY_STATE_V1' or s['context']!=expected:raise ValueError('CONTEXT_IDENTITY')
 if expected['sources']!=source_identity() or expected['runtime']!=runtime():raise ValueError('SOURCE_OR_RUNTIME_IDENTITY')
 parent=s['parent_snapshot_sha256']
 if parent is not None and (not isinstance(parent,str) or len(parent)!=64 or any(c not in '0123456789abcdef' for c in parent)):raise ValueError('PARENT_IDENTITY')
 geometry=s['geometry'];derived=properties(geometry['z_m'],geometry['Moho_m'],geometry['materials_k_rho_Cp_A'])
 if geometry!=derived or digest(geometry)!=expected['geometry_sha256']:raise ValueError('GEOMETRY_IDENTITY')
 if digest(s['initial_T_K'])!=expected['initial_T_sha256']:raise ValueError('INITIAL_IDENTITY')
 hi=np.array(s['T_hi_K']);co=np.array(s['T_correction_K']);n=len(geometry['z_m'])
 if hi.shape!=(n,) or co.shape!=(n,) or not np.isfinite(hi).all() or not np.isfinite(co).all() or min(hi.astype(np.longdouble)-co)<=0:raise ValueError('TEMPERATURE')
 if [float(hi[0]),float(hi[-1])]!=expected['Dirichlet_K'] or co[0]!=0 or co[-1]!=0:raise ValueError('BOUNDARY_IDENTITY')
 if type(s['step']) is not int or not 0<=s['step']<=expected['steps'] or len(s['ledger'])!=s['step'] or s['dt_s']!=expected['duration_s']/expected['steps'] or s['time_s']!=s['step']*s['dt_s']:raise ValueError('CLOCK')
 C=np.array(geometry['capacity_J_m2_K']);g=np.array(geometry['conductance_W_m2_K']);limit=float(min(C[1:-1]/(g[:-1]+g[1:])))
 if s['CFL_s']!=limit or s['dt_s']>.8*limit:raise ValueError('CFL')
 if s['current_flux_W_m2']!=current_flux(s).tolist():raise ValueError('FLUX_IDENTITY')
 for i,row in enumerate(s['ledger']):
  if row['step']!=i+1 or row['time_s']!=(i+1)*s['dt_s'] or not all(np.isfinite(v) for v in row.values()) or abs(row['residual_J_m2'])>row['roundoff_bound_J_m2']:raise ValueError('LEDGER')
 if s['step']==0 and s['last_step_flux_W_m2'] is not None:raise ValueError('LAST_FLUX')
 if s['step']>0 and (len(s['last_step_flux_W_m2'])!=n-1 or not np.isfinite(s['last_step_flux_W_m2']).all()):raise ValueError('LAST_FLUX')

def step(s):
 # Accepted-step state only: no partly updated array is persisted.
 if s['step']>=s['context']['steps']:raise ValueError('PLAN_EXHAUSTED')
 C=np.array(s['geometry']['capacity_J_m2_K']);S=np.array(s['geometry']['source_W_m2']);dt=s['dt_s'];hi=np.array(s['T_hi_K']);co=np.array(s['T_correction_K']);Q=current_flux(s)
 increment=dt*(np.diff(Q)+S[1:-1])/C[1:-1]
 y=increment-co[1:-1];new=hi.copy();new[1:-1]=hi[1:-1]+y;corr=co.copy();corr[1:-1]=(new[1:-1]-hi[1:-1])-y
 delta=(new[1:-1].astype(np.longdouble)-hi[1:-1])-(corr[1:-1].astype(np.longdouble)-co[1:-1])
 change=np.sum(C[1:-1].astype(np.longdouble)*delta);rad=np.longdouble(dt)*np.sum(S[1:-1].astype(np.longdouble));top=-np.longdouble(dt)*Q[0];base=np.longdouble(dt)*Q[-1];supply=rad+top+base;residual=change-supply
 bound=8*np.finfo(float).eps*(abs(change)+abs(rad)+abs(top)+abs(base))+np.finfo(np.longdouble).eps*np.sum(abs(C[1:-1].astype(np.longdouble)*delta))*8
 if abs(residual)>bound or not np.isfinite(new).all() or min(new.astype(np.longdouble)-corr)<=0:raise ValueError('ENERGY_OR_TEMPERATURE')
 s['T_hi_K']=new.tolist();s['T_correction_K']=corr.tolist();s['step']+=1;s['time_s']=s['step']*dt;s['last_step_flux_W_m2']=Q.tolist();s['current_flux_W_m2']=current_flux(s).tolist()
 s['ledger'].append(dict(step=s['step'],time_s=s['time_s'],internal_deltaE_J_m2=float(change),radiogenic_internal_J_m2=float(rad),Dirichlet_top_exchange_J_m2=float(top),Dirichlet_base_exchange_J_m2=float(base),residual_J_m2=float(residual),roundoff_bound_J_m2=float(bound)))
 return s
