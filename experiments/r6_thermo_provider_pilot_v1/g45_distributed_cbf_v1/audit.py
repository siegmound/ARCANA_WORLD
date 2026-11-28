"""Independent sparse reconstruction from per-rank G45 exports, no ASPECT writes."""
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy import sparse
from scipy.sparse.linalg import spsolve,eigsh

CONTRACT=json.loads(Path(__file__).with_name('contract.json').read_text())
T=CONTRACT['tolerances']
class Rejected(RuntimeError):pass

def require(condition,label):
    if not condition:raise Rejected(label)
def norm(x):return float(np.linalg.norm(x))
def relative(x,y):return norm(np.asarray(x)-np.asarray(y))/max(norm(y),1e-300)
def numeric(p,columns):
    if p.stat().st_size==0:return np.empty((0,columns))
    a=np.loadtxt(p,ndmin=2);require(a.shape[1]==columns and np.isfinite(a).all(),'NUMERIC_SCHEMA:'+p.name);return a

def keyed(p,columns):
    keys=[];values=[]
    for line in p.read_text().splitlines():
        fields=line.split();keys.append(fields[0]);values.append([float(x) for x in fields[1:]])
    a=np.array(values,dtype=float).reshape(-1,columns);require(np.isfinite(a).all(),'NONFINITE:'+p.name);return keys,a

def trace_operator(H,mass,residual):
    """Full sparse H has zero slave columns; preserve the exact Gram operator."""
    M=(H.T@sparse.diags(mass)@H).tocsr();diagonal=M.diagonal();active=np.flatnonzero(diagonal>1e-20)
    require(len(active)>0,'EMPTY_TRACE');A=M[active,:][:,active].tocsr();rhs=np.asarray(H.T@residual).ravel()[active]
    require(sparse.linalg.norm(A-A.T)/max(sparse.linalg.norm(A),1e-300)<T['trace_symmetry_relative'],'TRACE_ASYMMETRY')
    return active,A,rhs

def load(case,step=0):
    case=Path(case);spec=json.loads((case/'CASE_SPEC.json').read_text());n=spec['ranks'];dofs=[];faces=[];facekeys=[];cells=[];cellkeys=[];basis=[];basiskeys=[];h=[];ghosts=[];summaries=[]
    for rank in range(n):
        pre=case/'output'/f'G45_s{step}_r{rank}'
        summaries.append(numeric(Path(str(pre)+'_SUMMARY.dat'),14)[0]);dofs.append(numeric(Path(str(pre)+'_DOFS.dat'),17));h.append(numeric(Path(str(pre)+'_H.dat'),3));ghosts.append(numeric(Path(str(pre)+'_GHOSTS.dat'),4))
        for suffix,cols,ks,arrays in (('_FACES.dat',37,facekeys,faces),('_CELLS.dat',38,cellkeys,cells),('_BASIS.dat',6,basiskeys,basis)):
            k,a=keyed(Path(str(pre)+suffix),cols);ks.extend(k);arrays.append(a)
    return {'spec':spec,'dofs':np.vstack(dofs),'faces':np.vstack(faces),'facekeys':facekeys,'cells':np.vstack(cells),'cellkeys':cellkeys,'basis':np.vstack(basis),'basiskeys':basiskeys,
        'H_entries':np.vstack(h),'ghosts':np.vstack(ghosts),'summary':np.array(summaries)}

def evaluate(case,step=0):
    data=load(case,step);spec=data['spec'];n=spec['ranks'];d=data['dofs'];f=data['faces'];cells=data['cells'];summary=data['summary'];basis=data['basis'];ids=d[:,0].astype(np.int64);N=len(ids)
    require(len(set(ids))==N and np.array_equal(summary[:,0],np.arange(n)),'DOF_OR_RANK_OWNERSHIP')
    require(summary[:,1].sum()==len(cells) and len(set(data['cellkeys']))==len(cells),'CELL_COVERAGE')
    require(summary[:,3].sum()==N and np.all(summary[:,12]==0) and np.all(summary[:,13]==step),'OWNED_DOF_OR_TIME')
    require(np.all(cells[:,26]>0) and np.all(f[:,3]>0) and np.all(d[:,9]>=0),'POSITIVE_JACOBIAN_OR_MASS')
    require(set(f[:,2])=={0.,1.} and np.all(cells[:,1]<=1),'BOUNDARY_SCOPE')
    fk=[(k,int(row[0]),int(row[1])) for k,row in zip(data['facekeys'],f)]
    require(len(set(fk))==len(fk) and len(f)==9*summary[:,2].sum(),'FACE_COVERAGE')
    counts={}
    for cell,face,q in fk:counts.setdefault((cell,face),set()).add(q)
    require(all(v==set(range(9)) for v in counts.values()),'FACE_QUADRATURE_COVERAGE')
    facecounts={}
    for cell,face in counts:facecounts[cell]=facecounts.get(cell,0)+1
    require(all(facecounts.get(k,0)==int(row[1]) for k,row in zip(data['cellkeys'],cells)),'CELL_FACE_COVERAGE')
    x=f[:,4:7];normal=f[:,7:10];w=f[:,3];u=f[:,10:13];native=f[:,13:16];replica=f[:,16:19];raw=f[:,19:22];cons=f[:,22:25];hydro=f[:,25:28];stress=f[:,28:31]
    radial=x/np.linalg.norm(x,axis=1)[:,None]
    require(np.max(abs(np.linalg.norm(normal,axis=1)-1))<1e-12 and np.min(np.sum(normal*radial,axis=1)*np.where(f[:,2]==1,1,-1))>.99,'FACE_ORIENTATION')
    require(np.max(abs(np.linalg.norm(x,axis=1)-np.where(f[:,2]==1,1,.5)))<.002,'FACE_RADIUS')
    position={int(i):j for j,i in enumerate(ids)}
    try:
        node=np.array([[position[int(i)] for i in row] for row in f[:,34:37]])
        bi=np.array([position[int(i)] for i in basis[:,1]])
    except KeyError as e:raise Rejected('MISSING_OWNED_DOF') from e
    require(np.array_equal(d[bi,1],basis[:,2]) and np.max(abs(d[bi,2:5]-basis[:,3:6]))<1e-12,'SUPPORT_IDENTITY')
    require(all(np.array_equal(d[node[:,k],1],np.full(len(f),k)) for k in range(3)),'FACE_COMPONENTS')
    for value,column in ((u,5),(native,6),(cons,13),(hydro,15)):
        require(relative(value,d[node,column])<1e-12,'FACE_DOF_GHOST_INTERPOLATION')
    boundary=d[:,9]>1e-15
    require(boundary.any() and (~boundary).any(),'TRACE_COVERAGE')
    require(relative(raw,d[node,7]/d[node,9])<1e-12,'RAW_FACE_RECONSTRUCTION')
    native_dof=relative(d[boundary,8],d[boundary,9]*d[boundary,6]);native_face=relative(replica,native)
    require(native_dof<T['native_dof_relative'] and native_face<T['native_face_relative'],'NATIVE_IMPLEMENTATION_PARITY')
    rows=[];cols=[];vals=[];slaves={};expected=set(ids[d[:,16]==1].tolist())
    for slave,master,weight in data['H_entries']:
        a,b=int(slave),int(master);require(a in position and b in position and a!=b,'CONSTRAINT_SUPPORT')
        slaves.setdefault(a,[]).append((b,weight));rows.append(position[a]);cols.append(position[b]);vals.append(weight)
    require(set(slaves)==expected and len(slaves)==summary[:,4].sum(),'CONSTRAINT_COVERAGE')
    require(all(b not in slaves for entries in slaves.values() for b,_ in entries),'CONSTRAINT_NOT_CLOSED')
    for a in ids:
        if int(a) not in slaves:rows.append(position[int(a)]);cols.append(position[int(a)]);vals.append(1.)
    H=sparse.coo_matrix((vals,(rows,cols)),shape=(N,N)).tocsr();H.sum_duplicates()
    require(np.max(abs(np.asarray(H@np.ones(N))-1))<T['rigid_translation_reproduction_relative'],'TRANSLATION_REPRODUCTION')
    constraint_u=norm(d[:,5]-H@d[:,5])/max(norm(d[:,5]),1.)
    require(constraint_u<T['topological_constraint_relative'],'SOLUTION_HANGING_CONSTRAINT')
    active,A,rhs=trace_operator(H,d[:,9],d[:,7]);off=A-sparse.diags(A.diagonal());off.eliminate_zeros()
    if off.nnz:
        inv=1/np.sqrt(A.diagonal());scaled=sparse.diags(inv)@A@sparse.diags(inv)
        eigmin=float(eigsh(scaled,k=1,which='SA',return_eigenvectors=False,tol=1e-10)[0])
    else:eigmin=1.
    require(eigmin>1e-12,'TRACE_NOT_SPD');require(relative(A.diagonal(),d[active,11])<1e-12,'TRACE_DIAGONAL_ASSEMBLY')
    require(relative(rhs,d[active,10])<1e-12,'TRANSPOSE_RESIDUAL_ASSEMBLY')
    independent=np.asarray(spsolve(A,rhs));trace_delta=relative(d[active,12],independent)
    require(trace_delta<T['trace_independent_solve_relative'],'INDEPENDENT_TRACE_SOLVE')
    require(relative(H@d[:,12],d[:,13])<1e-12,'TRACTION_HANGING_CONSTRAINT')
    cg_res=norm(A@d[active,12]-rhs)/max(norm(rhs),1e-300)
    require(cg_res<T['trace_CG_relative_residual'] and np.max(summary[:,9])<T['trace_CG_relative_residual'],'TRACE_CG_RESIDUAL')
    hload=np.asarray(H.T@d[:,14])[active];hsol=spsolve(A,hload)
    require(relative(d[:,15],H[:,active]@hsol)<T['trace_independent_solve_relative'],'HYDRO_TRACE_SPLIT')
    if spec['adaptive_cycles']:
        require(summary[:,5].sum()>0 and len(set(cells[:,0]))>1,'NO_BOUNDARY_HANGING_NODES')
    else:require(summary[:,4].sum()==0,'UNEXPECTED_UNIFORM_CONSTRAINT')
    ghost_delta=0.
    for row in data['ghosts']:
        require(int(row[0]) in position,'GHOST_MISSING_OWNER');j=position[int(row[0])]
        target=np.array([d[j,5],d[j,13],d[j,7]/d[j,9] if d[j,9]>1e-15 else 0.])
        ghost_delta=max(ghost_delta,norm(row[1:]-target)/max(norm(target),1.))
    require(ghost_delta<T['ghost_relative'],'STALE_GHOST')
    D=float(cells[:,27].sum());B=float(cells[:,28].sum());P=float(cells[:,29].sum());body=cells[:,30:33].sum(axis=0);bodytorque=cells[:,33:36].sum(axis=0);bodyabs=float(cells[:,36].sum());loadscale=max(bodyabs+float(w@np.linalg.norm(cons,axis=1)),1.)
    totalwork=float(d[:,7]@d[:,5]);weak=D-B-P
    forced=spec['family'] in ('forced','datum')
    work_replay=abs(totalwork-weak)/max(D,1e-300) if forced else abs(totalwork-weak)/loadscale
    require(work_replay<T['work_replay_relative_D'],'VOLUME_WORK_REPLAY')
    facework=float(w@np.sum(cons*u,axis=1));nodalwork=float(rhs@d[active,5]);adjoint=abs(facework-nodalwork)/max(D,1e-300) if forced else abs(facework-nodalwork)/loadscale
    require(adjoint<T['adjoint_solution_relative_D'],'ADJOINT_SOLUTION_WORK')
    if forced:require(abs(weak)/max(D,1e-300)<T['forced_weak_balance_relative_D'],'FORCED_WEAK_BALANCE')
    stable={}
    for key,row in zip(data['basiskeys'],basis):
        j=position[int(row[1])];v=f'{key}/{int(row[0])}';stable[j]=min(stable.get(j,v),v)
    require(len(stable)==N,'STABLE_DOF_COVERAGE')
    virtual_max=0.
    for seed in range(5):
        v=np.array([(int(hashlib.sha256(f'{seed}/{stable[j]}'.encode()).hexdigest()[:12],16)/16**12)*2-1 for j in active]);fullv=H[:,active]@v;vf=fullv[node]
        a=float(w@np.sum(vf*cons,axis=1));bwork=float(d[:,7]@fullv)
        virtual_max=max(virtual_max,abs(a-bwork)/max(loadscale*max(float(np.max(abs(fullv))),1.),1.))
    require(virtual_max<T['adjoint_virtual_relative_absolute_power'],'ADJOINT_RANDOM_VIRTUAL_WORK')
    rotations=[]
    for axis in np.eye(3):
        rv=np.cross(np.broadcast_to(axis,(N,3)),d[:,2:5])[np.arange(N),d[:,1].astype(int)]
        projected=H@rv;rotations.append(norm(projected-rv)/max(norm(rv),1e-300))
    require(max(rotations)<T['rigid_rotation_reproduction_relative'],'ROTATION_REPRODUCTION')
    reactions={}
    for name,tr in (('native',native),('raw_all_cells',raw),('constrained',cons),('hydro_reference',hydro),('dynamic',cons-hydro),('raw_pointwise_stress',stress)):
        force=w@tr;torque=w@np.cross(x,tr);s=max(bodyabs+float(w@np.linalg.norm(tr,axis=1)),1.)
        reactions[name]={'force':force.tolist(),'moment':torque.tolist(),'force_balance_relative':norm(force+body)/s,'moment_balance_relative':norm(torque+bodytorque)/s,
            'boundary_work':float(w@np.sum(tr*u,axis=1)),'sides':{}}
        for side,label,area in ((0,'inner',np.pi),(1,'outer',4*np.pi)):
            m=f[:,2]==side;area_value=float(w[m].sum());require(abs(area_value/area-1)<T['area_relative'],'SURFACE_AREA')
            tang=tr[m]-np.sum(tr[m]*normal[m],axis=1)[:,None]*normal[m]
            reactions[name]['sides'][label]={'area':area_value,'force':(w[m]@tr[m]).tolist(),'moment':(w[m]@np.cross(x[m],tr[m])).tolist(),'work':float(w[m]@np.sum(tr[m]*u[m],axis=1)),
                'tangential_traction_rms':float(np.sqrt(w[m]@np.sum(tang*tang,axis=1)/area_value))}
    for label in ('hydro_reference','dynamic'):
        reactions[label]['force_balance_relative']=None;reactions[label]['moment_balance_relative']=None
        reactions[label]['split_scope']='traction decomposition only; total-body balance is not a separate split balance'
    equilibrium_pass=(reactions['constrained']['force_balance_relative']<T['force_absolute_load_scaled'] and reactions['constrained']['moment_balance_relative']<T['moment_absolute_load_length_scaled'])
    mesh=sorted((k,[float(v) for v in np.round(row[:26],12)]) for k,row in zip(data['cellkeys'],cells))
    field_order=sorted(range(N),key=stable.get);field_payload={'keys':[stable[j] for j in field_order],'values':d[field_order][:,[5,6,7,9,13,15]].tolist()}
    report={'screen_pass':equilibrium_pass,'trace_algebra_pass':True,'equilibrium_pass':equilibrium_pass,'spec':spec,'cells':len(cells),'velocity_dofs':N,'boundary_hanging_nodes':int(summary[:,5].sum()),'trace_dofs':len(active),'trace_offdiagonal_nnz':int(off.nnz),'trace_scaled_min_eigenvalue':eigmin,'trace_independent_solve_relative':trace_delta,'trace_CG_residual':cg_res,'constraint_solution_relative':constraint_u,'ghost_relative':ghost_delta,'native_dof_relative':native_dof,'native_face_relative':native_face,'weak_work':weak,'dissipation':D,'body_work':B,'pressure_work':P,'volume_work_replay_relative':work_replay,'adjoint_solution_relative':adjoint,'adjoint_random_virtual_relative':virtual_max,'rigid_rotation_relative':rotations,'force_scale_absolute':loadscale,'body_force':body.tolist(),'body_moment':bodytorque.tolist(),'reactions':reactions,'cell_imbalance_max_over_mean':float(summary[:,1].max()/summary[:,1].mean()),'owned_dof_counts':summary[:,3].astype(int).tolist(),'owned_cell_counts':summary[:,1].astype(int).tolist(),'mesh_sha256':hashlib.sha256(json.dumps(mesh,separators=(',',':')).encode()).hexdigest()}
    return report,field_payload

def enforce(report):
    require(report['trace_algebra_pass'] and report['equilibrium_pass'],'CONSTRAINED_FORCE_OR_MOMENT_BALANCE')
    return report

def datum(base,shifted):
    a=load(base);b=load(shifted)
    def ordered(d):return sorted(zip(d['facekeys'],d['faces']),key=lambda x:(x[0],x[1][0],x[1][1]))
    oa,ob=ordered(a),ordered(b);require([k for k,v in oa]==[k for k,v in ob],'DATUM_MESH')
    fa=np.array([v for k,v in oa]);fb=np.array([v for k,v in ob]);require(np.allclose(fa[:,:10],fb[:,:10],rtol=0,atol=1e-12),'DATUM_FACE_IDENTITY')
    error=relative(fb[:,22:25]-fa[:,22:25],-10*fa[:,7:10]);velocity=relative(fb[:,10:13],fa[:,10:13]);dissipation=abs(b['cells'][:,27].sum()/a['cells'][:,27].sum()-1);require(error<T['datum_relative_projected_minus10n'] and velocity<T['same_mesh_rank_relative'] and dissipation<T['same_mesh_rank_relative'],'DATUM_GAUGE_SHIFT')
    return {'screen_pass':True,'datum_minus10n_relative':error,'velocity_relative':velocity,'dissipation_relative':float(dissipation)}

# Contract reference is projected -10*n on the constrained trace. Retain the
# old pointwise diagnostic separately; it is not the AMR acceptance operator.
datum_pointwise_diagnostic=datum

def datum(base,shifted,require_pass=True):
    a=load(base);b=load(shifted);d=a['dofs'];ids=d[:,0].astype(np.int64);position={int(i):j for j,i in enumerate(ids)};N=len(ids)
    rr=[];cc=[];vv=[];slaves=set()
    for slave,master,value in a['H_entries']:
        slaves.add(int(slave));rr.append(position[int(slave)]);cc.append(position[int(master)]);vv.append(value)
    for i in ids:
        if int(i) not in slaves:rr.append(position[int(i)]);cc.append(position[int(i)]);vv.append(1.)
    H=sparse.coo_matrix((vv,(rr,cc)),shape=(N,N)).tocsr();f=a['faces'];node=np.array([[position[int(v)] for v in row] for row in f[:,34:37]])
    target=-10*f[:,7:10];load_vector=np.zeros(N)
    for k in range(3):np.add.at(load_vector,node[:,k],f[:,3]*target[:,k])
    active,M,rhs=trace_operator(H,d[:,9],load_vector);projected=(H[:,active]@spsolve(M,rhs))[node]
    ia=sorted(range(len(f)),key=lambda i:(a['facekeys'][i],f[i,0],f[i,1]));fb=b['faces'];ib=sorted(range(len(fb)),key=lambda i:(b['facekeys'][i],fb[i,0],fb[i,1]))
    require([(a['facekeys'][i],f[i,0],f[i,1]) for i in ia]==[(b['facekeys'][i],fb[i,0],fb[i,1]) for i in ib],'DATUM_MESH')
    fa=f[ia];fb=fb[ib];require(np.allclose(fa[:,:10],fb[:,:10],rtol=0,atol=1e-12),'DATUM_FACE_IDENTITY')
    delta=fb[:,22:25]-fa[:,22:25];error=relative(delta,projected[ia]);pointwise=relative(delta,-10*fa[:,7:10]);velocity=relative(fb[:,10:13],fa[:,10:13]);dissipation=float(abs(b['cells'][:,27].sum()/a['cells'][:,27].sum()-1))
    passed=bool(error<T['datum_relative_projected_minus10n'] and velocity<T['same_mesh_rank_relative'] and dissipation<T['same_mesh_rank_relative'])
    if require_pass:require(passed,'DATUM_GAUGE_SHIFT')
    return {'screen_pass':passed,'datum_projected_minus10n_relative':error,'datum_pointwise_minus10n_diagnostic':pointwise,'velocity_relative':velocity,'dissipation_relative':dissipation,'reference':'H_trace (H_trace^T M_GLL H_trace)^-1 H_trace^T integral(phi*(-10*n)); no RHS balancing or fitted correction'}
