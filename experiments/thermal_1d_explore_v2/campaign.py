from pathlib import Path
import sys,json,time,hashlib,resource
import numpy as np
from scipy.sparse import diags,bmat,csr_matrix
from scipy.sparse.linalg import expm_multiply
from scipy.linalg import expm
from scipy.special import erfc
from model import properties,advance

OUT=Path(sys.argv[1]); OUT.mkdir();BASE=Path(__file__).resolve().parents[3];REPO=BASE/'ARCANA_WORLD_R6_GEOMETRY_R1_WORK';start=time.perf_counter();YEAR=31557600.;DURATION=10*YEAR
write=lambda p,o:p.write_text(json.dumps(o,indent=2,allow_nan=False))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before=json.loads((OUT.parent/'BEFORE.json').read_text())
for p,h in {**before['pins'],**before['sources'],**before['thermal_v1']}.items():assert sha(REPO/p)==h,p
for p,x in before['inputs'].items():assert sha(Path(p))==x['sha256'],p
records=json.loads((OUT.parent/'SELECTED_INPUTS.json').read_text())
config=json.loads((REPO/'R6_PRE_ORBDATA_MATERIAL_REFERENCE_COLUMN_V1.json').read_text())

def material(rec):return [[rec[p+'_conductivity_w_m_k'],rec[p+'_density_kg_m3'],rec[p+'_cp_j_kg_k'],rec[p+'_heat_production_w_m3']] for p in ('crust','mantle')]
def grid(rec,factor):
    H,L=rec['crust_thickness_m'],rec['lab_depth_m']
    return np.r_[np.linspace(0,H,24*factor+1),np.linspace(H,L,48*factor+1)[1:]]
def initial(rec,z):
    a=[]
    for x in z:
        p='layer1' if x<=rec['crust_thickness_m'] else 'layer2';t=x-rec[p+'_z0_m']
        a.append(((rec[p+'_c3_k_m3']*t+rec[p+'_c2_k_m2'])*t+rec[p+'_c1_k_m'])*t+rec[p+'_c0_k'])
    return np.array(a)

def reference(z,H,m,T):
    # Independent assembly: scalar overlap intersections, independent of properties().
    C=[];S=[];g=[]
    for i,x in enumerate(z):
        left=z[0] if i==0 else (z[i-1]+x)/2;right=z[-1] if i==len(z)-1 else (z[i+1]+x)/2
        c=s=0.
        for (lo,hi),v in zip(((0,H),(H,z[-1])),m):
            length=max(0,min(right,hi)-max(left,lo));c+=length*v[1]*v[2];s+=length*v[3]
        C.append(c);S.append(s)
    for l,r in zip(z[:-1],z[1:]):
        resistance=sum(max(0,min(r,hi)-max(l,lo))/v[0] for (lo,hi),v in zip(((0,H),(H,z[-1])),m));g.append(1/resistance)
    C,S,g=map(np.array,(C,S,g)); n=len(z)-2
    L=diags([g[1:-1]/C[2:-1],-(g[:-1]+g[1:])/C[1:-1],g[1:-1]/C[1:-2]],[-1,0,1],shape=(n,n),format='csr')
    rhs=(np.diff(g*np.diff(T))+S[1:-1])/C[1:-1]
    B=bmat([[L,csr_matrix(rhs[:,None])],[None,csr_matrix((1,1))]],format='csr')*DURATION
    seed=np.r_[np.zeros(n),1.];inc=expm_multiply(B,seed,traceA=float(B.diagonal().sum()))[:-1]
    cross=None
    if len(z)<=289:cross=float(max(abs(inc-(expm(B.toarray())@seed)[:-1])))
    return np.r_[0.,inc,0.],cross

def norm(err,z):
    w=np.diff(np.r_[z[0],(z[:-1]+z[1:])/2,z[-1]])
    return dict(L1=float(np.sum(w*abs(err))/sum(w)),L2=float(np.sqrt(np.sum(w*err**2)/sum(w))),Linf=float(max(abs(err))))

def continuum(rec,z,m):
    # Short-time half-space boundary response for constant initial tendency r.
    # T0+r*t-r*I(z,kappa_C,t)-r*I(L-z,kappa_M,t),
    # I=int_0^t erfc(d/(2sqrt(kappa*s))) ds. Remote-interface effects exponentially tiny.
    rate=rec['transient_rate_k_s'];L=rec['lab_depth_m']
    def I(d,kappa):
        eta=d/(2*np.sqrt(kappa*DURATION));return (DURATION+d*d/(2*kappa))*erfc(eta)-d*np.sqrt(DURATION/(np.pi*kappa))*np.exp(-eta**2)
    return rate*(DURATION-I(z,m[0][0]/(m[0][1]*m[0][2]))-I(L-z,m[1][0]/(m[1][1]*m[1][2])))

# Simple independent constant-temperature/source-free and unsafe-dt controls.
tz=np.array([0.,1.,2.,3.]);tm=[[2.,3.,4.,0.],[4.,5.,6.,0.]]
a=advance(tz,1.,tm,np.full(4,280.),.01,2);assert np.array_equal(a['T'],np.full(4,280.))
try:advance(tz,1.,tm,np.full(4,280.),1e9,1)
except ValueError:pass
else:raise AssertionError('unsafe dt accepted')
rows=[];sensitivity=[];graded=[]
for label,rec in records.items():
    H=rec['crust_thickness_m'];m=material(rec);print(label,flush=True)
    for factor in (1,2,4):
        z=grid(rec,factor);T=initial(rec,z);C,S,g,e=properties(z,H,m);inc,cross=reference(z,H,m,T);analytic=continuum(rec,z,m)
        # Verify initial polynomial consistency at every internal node incl Moho.
        tendency=(np.diff(g*np.diff(T))+S[1:-1])/C[1:-1];rate=rec['transient_rate_k_s']
        assert max(abs(tendency-rate))<1e-22
        for steps in (16,32,64):
            runstart=time.perf_counter();a=advance(z,H,m,T,DURATION,steps);errT=a['T'].astype(np.longdouble)-T.astype(np.longdouble)-inc.astype(np.longdouble)
            result=dict(column=label,nodes=len(z),steps=steps,temporal=norm(errT,z),spatial=norm(inc-analytic,z),delta_T_linf_K=float(max(abs(a['T']-T))),CFL_s=a['CFL_s'],CFL_ratio=a['dt_s']/a['CFL_s'],ledger_residual_J_m2=float(sum(a['ledger'][:,2])),ledger_abs_sum_J_m2=float(sum(abs(a['ledger'][:,2]))),ledger_input_J_m2=float(sum(a['ledger'][:,1])),max_step_ledger_J_m2=float(max(abs(a['ledger'][:,2]))),production_interior_W_m2=float(sum(S[1:-1])),production_reservoir_W_m2=float(S[0]+S[-1]),production_full_W_m2=float(sum(S)),initial_rate_error_K_s=float(max(abs(tendency-rate))),expm_crosscheck_K=cross,wall_s=time.perf_counter()-runstart)
            # Initial Moho exact one-sided derivatives vs original stored flux.
            j=24*factor;fits=[np.polyfit(z[j-2:j+1]-H,T[j-2:j+1],2),np.polyfit(z[j:j+3]-H,T[j:j+3],2)]
            result['initial_reconstructed_Moho_flux_W_m2']=[float(m[i][0]*fits[i][1]) for i in (0,1)]
            ffinal=g*np.diff(a['T']);result['final_Moho_adjacent_flux_W_m2']=[float(ffinal[j-1]),float(ffinal[j])]
            np.savez(OUT/f'{label}_{len(z)}_{steps}.npz',z=z,T0=T,semidiscrete_increment=inc,continuum_increment=analytic,**{k:v for k,v in a.items() if isinstance(v,np.ndarray)})
            rows.append(result)
    # Boundary resolving reference only: same PRE initial profile; no new physical fields.
    for dx in (4.,2.,1.):
        z0=grid(rec,4);d=np.arange(dx,256.+dx/2,dx);z=np.unique(np.r_[z0,d,z0[-1]-d]);T=initial(rec,z);inc,cross=reference(z,H,m,T);analytic=continuum(rec,z,m)
        edge_mask=(z<=256)|(z>=z[-1]-256)
        gd=dict(column=label,dx_m=dx,nodes=len(z),global_error=norm(inc-analytic,z),boundary_Linf_K=float(max(abs((inc-analytic)[edge_mask]))),reference_only=True)
        np.savez(OUT/f'{label}_boundary_dx{dx:g}.npz',z=z,T0=T,semidiscrete_increment=inc,continuum_increment=analytic);graded.append(gd)
    # Only the hot original column: one-at-a-time parameter sensitivity, fixed T0 and Dirichlet.
    if label=='hot_C028':
        controls=[('crust_k',0,0,config['thermal_properties']['continental_crust']['k']['sensitivity_range']),('crust_Cp',0,2,config['thermal_properties']['continental_crust']['Cp']['sensitivity_range']),('crust_A',0,3,config['radiogenic_heat']['continental_crust']['sensitivity_range']),('mantle_A',1,3,config['radiogenic_heat']['mantle_lithosphere']['sensitivity_range'])]
        for name,layer,idx,values in controls:
            for val in values:
                for factor in (1,4):
                    mm=[v.copy() for v in m];mm[layer][idx]=val;z=grid(rec,factor);T=initial(rec,z);inc,cross=reference(z,H,mm,T);a=advance(z,H,mm,T,DURATION,64);nom,_=reference(z,H,m,T)
                    st=dict(parameter=name,value=val,nodes=len(z),nominal_value=m[layer][idx],max_change_from_nominal_K=float(max(abs(inc-nom))),final_change_linf_K=float(max(abs(a['T']-T))),temporal_error=norm(a['T'].astype(np.longdouble)-T.astype(np.longdouble)-inc,z),energy_residual_J_m2=float(sum(a['ledger'][:,2])),CFL_ratio=a['dt_s']/a['CFL_s'],initial_profile_rebuilt=False)
                    sensitivity.append(st);np.savez(OUT/f'sensitivity_{name}_{val:g}_{len(z)}.npz',z=z,T0=T,semidiscrete_increment=inc,nominal_increment=nom,materials=mm,**{k:v for k,v in a.items() if isinstance(v,np.ndarray)})
write(OUT/'RESULT.json',dict(rows=rows,graded_references=graded,sensitivities=sensitivity,wall_s=time.perf_counter()-start,cpu_user_s=resource.getrusage(resource.RUSAGE_SELF).ru_utime,cpu_system_s=resource.getrusage(resource.RUSAGE_SELF).ru_stime,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,controls='PASS',source={p.name:sha(p) for p in Path(__file__).parent.glob('*.py')}))
print('completed',time.perf_counter()-start,flush=True)
