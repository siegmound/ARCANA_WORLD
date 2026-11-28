"""Independent component-wise rigid-motion/virtual-trace audit of retained data."""
import json
from pathlib import Path
import sys
import numpy as np
from scipy import sparse
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g45_distributed_amr_cbf as c
sys.path.insert(0,str(c.CODE));import audit


def translations(H,components):
    errors=[]
    for axis in range(3):
        values=(components==axis).astype(float);errors.append(float(np.max(abs(H@values-values))))
    audit.require(max(errors)<audit.T['rigid_translation_reproduction_relative'],'COMPONENT_TRANSLATION_REPRODUCTION')
    return errors


def main():
    rows=[]
    paths=set(c.ROOT.glob('*/G45R1_AUDIT_REPORT.json'))|set(c.ROOT.glob('*/AUDIT_V2_REPORT.json'))
    for report in sorted(paths):
        case=report.parent;old=c.read(report)
        if not old['screen_pass'] or not c.native_convergence(case)['screen_pass']:continue
        spec=c.read(case/'CASE_SPEC.json');d=[];h=[];f=[]
        for rank in range(spec['ranks']):
            pre=case/'output'/f'G45_s0_r{rank}';d.append(audit.numeric(Path(str(pre)+'_DOFS.dat'),17));h.append(audit.numeric(Path(str(pre)+'_H.dat'),3));_,ff=audit.keyed(Path(str(pre)+'_FACES.dat'),37);f.append(ff)
        d=np.vstack(d);h=np.vstack(h);f=np.vstack(f);N=len(d);idx={int(v):i for i,v in enumerate(d[:,0])};components=d[:,1].astype(int);rr=[];cc=[];vv=[];slaves=set()
        for slave,master,w in h:
            i,j=idx[int(slave)],idx[int(master)];audit.require(components[i]==components[j],'HANGING_COMPONENT_MIX');rr.append(i);cc.append(j);vv.append(w);slaves.add(i)
        for i in range(N):
            if i not in slaves:rr.append(i);cc.append(i);vv.append(1.)
        H=sparse.coo_matrix((vv,(rr,cc)),shape=(N,N)).tocsr();terr=translations(H,components);active=np.flatnonzero(d[:,11]>1e-20);node=np.array([[idx[int(v)] for v in row] for row in f[:,34:37]]);motions=[]
        for axis in range(3):
            motions.append(('translation_'+str(axis),(components==axis).astype(float)))
            rotation=np.cross(np.broadcast_to(np.eye(3)[axis],(N,3)),d[:,2:5])[np.arange(N),components];motions.append(('rotation_'+str(axis),rotation))
        checks=[]
        for name,coefficients in motions:
            represented=H@coefficients;reproduction=float(np.linalg.norm(represented-coefficients)/max(np.linalg.norm(coefficients),1.))
            extension=H[:,active]@coefficients[active];trace=extension[node];work_face=float(f[:,3]@np.sum(trace*f[:,22:25],axis=1));work_volume=float(d[:,7]@extension);scale=max(old['force_scale_absolute']*max(float(np.max(abs(extension))),1.),1.);error=abs(work_face-work_volume)/scale
            audit.require(error<audit.T['adjoint_virtual_relative_absolute_power'],'RIGID_TRACE_ADJOINT')
            audit.require(reproduction<(audit.T['rigid_rotation_reproduction_relative'] if name.startswith('rotation') else audit.T['rigid_translation_reproduction_relative']),'RIGID_FIELD_REPRODUCTION')
            checks.append({'motion':name,'full_field_reproduction_relative':reproduction,'boundary_work':work_face,'all_cell_residual_work':work_volume,'absolute_power_scale':scale,'adjoint_relative':error})
        rows.append({'case':case.name,'screen_pass':True,'translation_component_max_errors':terr,'motions':checks})
    c.need(len(rows)>=16,'RIGID_AUDIT_COVERAGE')
    c.write(c.ROOT/'RIGID_MOTION_AND_VIRTUAL_WORK.json',{'screen_pass':True,'cases':rows,'scope':'component-wise global topology reproduction; rigid boundary traces with zero independent-interior extension for adjoint identity; full physical geometric force/moment separately screened','limits':'curved AMR rotation reproduction has measured discretization error, not claimed exact; no velocity or RHS correction',**c.SCOPE});print('RIGID_MOTION_PASS',len(rows),flush=True)
if __name__=='__main__':main()
