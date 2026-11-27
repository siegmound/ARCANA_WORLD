#!/usr/bin/env python3
"""G41: native ASPECT FE quadrature export, independent mechanical work audit.
Synthetic G39 replays only. Plugin outside historical container; no solver patch.
Raw face stresses are not equilibrated reactions or physical ARCANA loads.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import signal
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32
import arcana_aspect_recovery_preflight as ar
import arcana_g38_aspect_hollow_sphere as g38
import arcana_g39_aspect_free_slip as g39
import arcana_g40_aspect_snapshot_balance as g40

PIN='0acb0654e962bbc387677acd2fe0e08f3bdbed7e7615609bb857d8b463d255ad'
STATUS='G40_ASPECT_EXPORTED_BALANCE_PASS__NATIVE_TRACTION_AND_STATE_REQUIRED'
AUTH='G41_SYNTHETIC_NATIVE_QUADRATURE_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
CASES=('hydro_3','forced_volume_2','forced_volume_3','forced_datum_3')
CPP=r'''
#include <aspect/postprocess/interface.h>
#include <aspect/simulator_access.h>
#include <aspect/material_model/interface.h>
#include <aspect/gravity_model/interface.h>
#include <aspect/geometry_model/interface.h>
#include <deal.II/base/quadrature_lib.h>
#include <deal.II/fe/fe_values.h>
#include <fstream>
#include <iomanip>
namespace aspect { namespace Postprocess {
template <int dim>
class ArcanaG41 : public Interface<dim>, public SimulatorAccess<dim>
{
public:
  std::pair<std::string,std::string> execute(TableHandler &) override
  {
    AssertThrow(dim==3, ExcMessage("G41 requires 3D"));
    AssertThrow(Utilities::MPI::n_mpi_processes(this->get_mpi_communicator())==1,
                ExcMessage("G41 requires singleton"));
    AssertThrow(!this->get_material_model().is_compressible(),
                ExcMessage("G41 requires incompressible material"));
    const auto &quad=this->introspection().quadratures.velocities;
    const unsigned int degree=this->get_fe().base_element(this->introspection().base_elements.velocities).degree;
    const QGauss<dim-1> fq(degree+1);
    const UpdateFlags flags=update_values|update_gradients|update_quadrature_points|update_JxW_values;
    FEValues<dim> fe(this->get_mapping(),this->get_fe(),quad,flags);
    FEFaceValues<dim> ff(this->get_mapping(),this->get_fe(),fq,flags|update_normal_vectors);
    const unsigned int nc=this->n_compositional_fields();
    const auto inner=this->get_geometry_model().translate_symbolic_boundary_name_to_id("bottom");
    const auto outer=this->get_geometry_model().translate_symbolic_boundary_name_to_id("top");
    std::ofstream vol(this->get_output_directory()+"G41_VOLUME.dat");
    std::ofstream fac(this->get_output_directory()+"G41_FACE.dat");
    AssertThrow(vol.good() && fac.good(),ExcMessage("G41 output open"));
    vol<<std::setprecision(17)<<std::scientific;
    fac<<std::setprecision(17)<<std::scientific;
    unsigned int ci=0, nv=0, nf=0;
    for (const auto &cell:this->get_dof_handler().active_cell_iterators())
      if(cell->is_locally_owned())
      {
        ++ci; fe.reinit(cell);
        auto dump=[&](const FEValuesBase<dim> &f,std::ostream &o,
                      const FEFaceValues<dim> *face,int side)
        {
          MaterialModel::MaterialModelInputs<dim> in(f.n_quadrature_points,nc);
          MaterialModel::MaterialModelOutputs<dim> out(f.n_quadrature_points,nc);
          in.requested_properties=MaterialModel::MaterialProperties::density | MaterialModel::MaterialProperties::viscosity;
          in.reinit(f,cell,this->introspection(),this->get_solution());
          this->get_material_model().fill_additional_material_model_inputs(in,this->get_solution(),f,this->introspection());
          this->get_material_model().evaluate(in,out);
          for(unsigned int q=0;q<f.n_quadrature_points;++q)
          {
            o<<ci<<' '<<q<<' '<<f.JxW(q);
            for(unsigned int i=0;i<dim;++i) o<<' '<<in.position[q][i];
            for(unsigned int i=0;i<dim;++i) o<<' '<<in.velocity[q][i];
            o<<' '<<in.pressure[q]<<' '<<in.temperature[q]<<' '<<out.densities[q]<<' '<<out.viscosities[q];
            const auto g=this->get_gravity_model().gravity_vector(in.position[q]);
            for(unsigned int i=0;i<dim;++i) o<<' '<<g[i];
            for(unsigned int i=0;i<dim;++i)
              for(unsigned int j=0;j<dim;++j) o<<' '<<in.strain_rate[q][i][j];
            if(face)
            {
              o<<' '<<side;
              for(unsigned int i=0;i<dim;++i) o<<' '<<face->normal_vector(q)[i];
              ++nf;
            }
            else ++nv;
            o<<'\n';
          }
        };
        dump(fe,vol,nullptr,0);
        for(unsigned int f=0;f<GeometryInfo<dim>::faces_per_cell;++f)
          if(cell->at_boundary(f))
          {
            const auto id=cell->face(f)->boundary_id();
            AssertThrow(id==inner || id==outer,ExcMessage("G41 unexpected boundary"));
            ff.reinit(cell,f); dump(ff,fac,&ff,id==inner?0:1);
          }
      }
    vol.close(); fac.close();
    AssertThrow(vol.good() && fac.good(),ExcMessage("G41 output failure"));
    return {"G41 native quadrature records:",std::to_string(nv)+" "+std::to_string(nf)};
  }
};
ASPECT_REGISTER_POSTPROCESSOR(ArcanaG41,"arcana g41 native quadrature","Synthetic native quadrature export.")
}}
'''
CMAKE='''cmake_minimum_required(VERSION 3.13.4)
find_package(Aspect 2.4.0 REQUIRED HINTS /home/dealii/aspect)
DEAL_II_INITIALIZE_CACHED_VARIABLES()
project(arcana_g41)
add_library(arcana_g41 SHARED arcana_g41.cc)
ASPECT_SETUP_PLUGIN(arcana_g41)
'''
def launch(work,state,root,args,label,timeout):
    cmd=[str(state/'bin/proot-x86_64-4_8_0'),'-r',str(root),'-b','/proc','-b','/dev',
         '-b',str(work)+':/tmp','-w','/tmp',*args]
    env=dict(os.environ,HOME='/home/dealii',USER='dealii',PATH='/usr/bin:/bin',
        OMPI_MCA_btl='^vader',HWLOC_HIDE_ERRORS='2',OMP_NUM_THREADS='1',
        OPENBLAS_NUM_THREADS='1',MKL_NUM_THREADS='1',TMPDIR='/tmp',PYTHONDONTWRITEBYTECODE='1')
    write(work/(label+'_COMMAND.json'),{'argv':cmd,'timeout_s':timeout,'rank_policy':'singleton',
        'address_space_limit_bytes_per_process':8*1024**3,'file_size_limit_bytes':1024**3})
    with (work/(label+'_STDOUT.txt')).open('x') as so,(work/(label+'_STDERR.txt')).open('x') as se:
        proc=subprocess.Popen(['/usr/bin/time','-v','-o',str(work/(label+'_TIME.txt')),*cmd],cwd=work,
            env=env,stdout=so,stderr=se,start_new_session=True,preexec_fn=g38.limits)
        try: rc=proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid,signal.SIGKILL);proc.wait();rc=124
    (work/(label+'_EXIT.txt')).write_text(str(rc)+'\n')
    need(rc==0,label+'_EXIT:'+str(rc))
def build(out,state,root,src,hs):
    work=out/'plugin';work.mkdir()
    (work/'arcana_g41.cc').write_text(CPP)
    (work/'CMakeLists.txt').write_text(CMAKE)
    # Reuse the exact historical CMake package path, if recorded.
    import re
    configs=set()
    for p in hs.rglob('CMakeCache.txt'):
        configs.update(re.findall(r'^Aspect_DIR:PATH=(.+)$',p.read_text(),re.M))
    configs={p for p in configs if p.startswith('/') and (root/p.lstrip('/')/'AspectConfig.cmake').is_file()}
    need(len(configs)<=1,'AMBIGUOUS_ASPECT_CMAKE')
    opts=['-DAspect_DIR='+next(iter(configs))] if configs else []
    launch(work,state,root,['/usr/bin/cmake','-S','/tmp','-B','/tmp/build',*opts],'CONFIGURE',180)
    # Both DEBUG and OPTIMIZED executables were recovered. The upstream macro
    # defines arcana_g41.release when both variants are enabled.
    launch(work,state,root,['/usr/bin/cmake','--build','/tmp/build','--target','arcana_g41.release','--parallel','1'],'BUILD',600)
    lib=work/'build/libarcana_g41.release.so'
    need(lib.is_file() and lib.stat().st_size>0,'PLUGIN_BUILD_OUTPUT')
    write(work/'PLUGIN_IDENTITY.json',{'source_sha256':sha(work/'arcana_g41.cc'),'cmake_sha256':sha(work/'CMakeLists.txt'),
        'plugin_sha256':sha(lib),'ASPECT_source_sha':ar.ASPECT_SHA})
    return lib
def prm_for(name):
    if name=='forced_volume_2':
        txt=g39.make_prm(g39.CASES[2])
        need(txt.count('set Initial global refinement = 3')==1,'LEVEL_PATCH')
        txt=txt.replace('set Initial global refinement = 3','set Initial global refinement = 2')
    else: txt=g39.make_prm(next(c for c in g39.CASES if c[0]==name))
    need(txt.count('viscous dissipation statistics')==1,'POSTPROCESS_PATCH')
    return 'set Additional shared libraries = ./libarcana_g41.so\n'+txt.replace(
        'viscous dissipation statistics','viscous dissipation statistics, arcana g41 native quadrature')
def unpack(a):
    need(a.ndim==2 and a.shape[1] in (25,29) and np.isfinite(a).all() and np.all(a[:,2]>0),'RECORDS')
    return a[:,2],a[:,3:6],a[:,6:9],a[:,9],a[:,10],a[:,11],a[:,12],a[:,13:16],a[:,16:25].reshape(-1,3,3)
def integrate(v,f,datum):
    w,x,u,p,t,rho,eta,g,eps=unpack(v)
    need(np.max(abs(rho-1000*(1-.001*(t-1000))))<1e-8 and np.max(abs(eta-1))<1e-12,'MATERIAL_PARITY')
    need(np.max(abs(g+x/np.linalg.norm(x,axis=1)[:,None]))<1e-12,'GRAVITY_PARITY')
    need(np.max(abs(eps-eps.transpose(0,2,1)))<1e-12,'STRAIN_SYMMETRY')
    dot=lambda a,b:np.einsum('qi,qi->q',a,b)
    div=np.trace(eps,axis1=1,axis2=2)
    D=float(w@(2*eta*np.sum(eps*eps,axis=(1,2))))
    Ddev=float(w@(2*eta*np.sum((eps-div[:,None,None]*np.eye(3)/3)**2,axis=(1,2))))
    body=rho[:,None]*g
    B=float(w@dot(body,u)); P=float(w@(p*div))
    dbody=(rho-1000)[:,None]*g
    out={'volume_m3':float(w.sum()),'dissipation_W':D,'deviatoric_dissipation_W':Ddev,
         'body_work_W':B,'dynamic_body_work_W':float(w@dot(dbody,u)),
         'pressure_divergence_work_W':P,'weak_energy_residual_W':D-B-P,
         'body_force_N':(w@body).tolist(),'body_torque_Nm':(w@np.cross(x,body)).tolist(),
         'divergence_rms_s_inv':float(np.sqrt(w@(div**2)/w.sum())),'boundaries':{}}
    fw,fx,fu,fp,ft,frho,feta,fg,feps=unpack(f)
    need(np.max(abs(np.linalg.norm(f[:,26:29],axis=1)-1))<1e-12 and set(f[:,25])=={0.,1.},'NORMALS')
    n=f[:,26:29]
    sig=2*feta[:,None,None]*feps-fp[:,None,None]*np.eye(3)
    tr=np.einsum('qij,qj->qi',sig,n)
    pd=fp-1000*(1-np.linalg.norm(fx,axis=1))-datum
    td=np.einsum('qij,qj->qi',2*feta[:,None,None]*feps-pd[:,None,None]*np.eye(3),n)
    for side,name,r in ((0,'inner',.5),(1,'outer',1.)):
        m=f[:,25]==side;a=fw[m]; xx=fx[m]; nn=n[m]; uu=fu[m]; tt=tr[m]; dyn=td[m]
        need(np.max(abs(np.linalg.norm(xx,axis=1)-r))<.002,'FACE_RADIUS')
        need(np.min(dot(nn,xx/np.linalg.norm(xx,axis=1)[:,None])*(1 if side else -1))>.99,'FACE_SIGN')
        tan=tt-dot(tt,nn)[:,None]*nn
        out['boundaries'][name]={'records':int(m.sum()),'area_m2':float(a.sum()),
            'raw_force_N':(a@tt).tolist(),'raw_torque_Nm':(a@np.cross(xx,tt)).tolist(),
            'raw_work_W':float(a@dot(tt,uu)),'dynamic_force_N':(a@dyn).tolist(),
            'dynamic_work_W':float(a@dot(dyn,uu)),
            'normal_velocity_rms':float(np.sqrt(a@(dot(uu,nn)**2)/a.sum())),
            'tangential_traction_rms':float(np.sqrt(a@dot(tan,tan)/a.sum()))}
    W=sum(b['raw_work_W'] for b in out['boundaries'].values())
    out['raw_boundary_work_W']=W;out['raw_stress_energy_residual_W']=D-B-P-W
    out['raw_force_residual_N']=(w@body+sum(np.array(b['raw_force_N']) for b in out['boundaries'].values())).tolist()
    out['raw_torque_residual_Nm']=(w@np.cross(x,body)+sum(np.array(b['raw_torque_Nm']) for b in out['boundaries'].values())).tolist()
    return out
def run_case(out,name,lib,state,root,p39):
    work=out/name;work.mkdir()
    prm=work/'input.prm';prm.write_text(prm_for(name))
    shutil.copyfile(lib,work/lib.name)
    launch(work,state,root,['/home/dealii/aspect/bin/aspect-release','input.prm'],'RUN',600)
    text=(work/'RUN_STDOUT.txt').read_text()
    need(all(s in text for s in ('OPTIMIZED','3.2.0-pre','30eb77ee5','running with 1 MPI process','G41 native quadrature records:')),'NATIVE_IDENTITY')
    native=g39.parse_stats(work/'output/statistics')
    v=np.loadtxt(work/'output/G41_VOLUME.dat',ndmin=2);f=np.loadtxt(work/'output/G41_FACE.dat',ndmin=2)
    need(v.shape==(native['cells']*27,25) and f.ndim==2 and f.shape[1]==29,'QUADRATURE_SCHEMA')
    need(np.array_equal(v[:,0],np.repeat(np.arange(1,native['cells']+1),27)) and
         np.array_equal(v[:,1],np.tile(np.arange(27),native['cells'])),'VOLUME_IDS')
    need(np.all((f[:,0]>=1)&(f[:,0]<=native['cells'])) and np.all((f[:,1]>=0)&(f[:,1]<9)),'FACE_IDS')
    d=integrate(v,f,10 if name=='forced_datum_3' else 0)
    err=abs(d['dissipation_W']/native['dissipation']-1)
    weak=abs(d['weak_energy_residual_W'])/max(native['dissipation'],1e-300)
    checks={'native_dissipation_parity':err<1e-7,
        'volume':abs(d['volume_m3']/(4*np.pi/3*(1-.5**3))-1)<.005,
        'boundary_areas':all(abs(d['boundaries'][k]['area_m2']/a-1)<.005 for k,a in (('inner',np.pi),('outer',4*np.pi))),
        'radial_body_torque':np.linalg.norm(d['body_torque_Nm'])<1e-10}
    if name!='hydro_3': checks['weak_energy_screen']=weak<1e-4
    if name!='forced_volume_2':
        old=read(p39/name/'CASE_REPORT.json')
        checks['G39_replay']=all(abs(native[k]-old[k])/max(abs(old[k]),1e-10)<1e-6 for k in ('rms','dissipation','pmean'))
    row={'name':name,'native':native,'volume_records':len(v),'face_records':len(f),'audit':d,
        'native_dissipation_relative':err,'weak_energy_relative':weak,'checks':{k:bool(v) for k,v in checks.items()}}
    row['screen_pass']=all(row['checks'].values())
    write(work/'CASE_REPORT.json',row)
    print('G41_CASE',json.dumps(row,allow_nan=False),flush=True)
    return row
def main():
    ap=argparse.ArgumentParser()
    for k in ('base','recovery','inventory','g37b','g38','g39','g40','output'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-synthetic-native-quadrature-only',choices=[AUTH],required=True)
    a=ap.parse_args();base,rec,inv,b,p38,p39,p40,out=(x.resolve() for x in (a.base,a.recovery,a.inventory,a.g37b,a.g38,a.g39,a.g40,a.output))
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    def parents():return [g38.verified_bundle(rec,g38.PREC),g38.verified_bundle(inv,g38.PINV),
        g32.verify(b,g38.P37B,g38.S37B),g32.verify(p38,g39.PIN,g39.STATUS),g32.verify(p39,g40.PIN,g40.STATUS),g32.verify(p40,PIN,STATUS)]
    check();before=parents()
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in (source,rec,inv,b,p38,p39,p40,base/'ARCANA_ASPECT_TOOLS')),'OUTPUT')
    out.mkdir(); report={'source_sha':g25.SOURCE,'G40_manifest_sha256':PIN,'builds_attempted':0,'synthetic_solves_attempted':0,
        'ARCANA_solves':0,'additional_time_advance_years':0,'global_solve_authorized':False,'physical_acceptance':False,
        'mantle_provider_qualified':False,'native_equilibrated_traction_qualified':False,**g25.SCOPE}
    snapshot=None
    try:
        state,container,root,src,hs,_,_,_=g38.inputs(base,rec,inv)
        snapshot=ar.tree_metadata(container);g39.native_sources(src)
        report['builds_attempted']=1;lib=build(out,state,root,src,hs)
        report['cases']=[]
        for name in CASES:
            report['synthetic_solves_attempted']+=1;report['cases'].append(run_case(out,name,lib,state,root,p39))
        coarse,fine=report['cases'][1:3]
        report['raw_face_refinement']={k:{m:fine['audit']['boundaries'][k][m]/max(coarse['audit']['boundaries'][k][m],1e-300)
            for m in ('normal_velocity_rms','tangential_traction_rms')} for k in ('inner','outer')}
        need(all(r['screen_pass'] for r in report['cases']),'NATIVE_QUADRATURE_SCREEN')
        report.update(screen_pass=True,status='G41_NATIVE_QUADRATURE_WEAK_BALANCE_PASS__EQUILIBRATED_REACTION_AND_STATE_REQUIRED')
    except Exception as e:report.update(screen_pass=False,status='G41_NATIVE_QUADRATURE_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        check();need(parents()==before,'PARENT_MUTATION')
        if snapshot is not None:need(ar.tree_metadata(container)==snapshot,'CONTAINER_DRIFT');g38.inputs(base,rec,inv)
        report['source_and_parents_unchanged']=True
    except Exception as e:report.update(screen_pass=False,status='G41_NATIVE_QUADRATURE_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['Native quadrature of synthetic incompressible cases only.',
        'Weak work balance is distinct from raw stress-face closure; raw face tractions not admitted.',
        'No consistent boundary reaction reconstruction or ARCANA mantle state.',
        'G40 deviatoric dissipation differs from native full symmetric strain for incompressible material.']
    # CMake macro may create executable symlinks in the isolated build tree;
    # never include links into the container in the evidence inventory.
    for link in out.rglob('*'):
        if link.is_symlink():
            need(link.name in ('aspect','aspect-debug','aspect-release'),'UNEXPECTED_BUILD_LINK')
            link.unlink()
    write(out/'REPORT.json',report);write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G41_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
