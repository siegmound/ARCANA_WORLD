#!/usr/bin/env python3
"""G42: synthetic native CBF parity against independently assembled FE residual.
Uniform rank-one Q2 shells only; no post-hoc balancing or ARCANA reaction.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import traceback
import numpy as np
import arcana_g25_fixed_load_decomposition as g25
import arcana_g32_corrected_global_operator as g32
import arcana_aspect_recovery_preflight as ar
import arcana_g38_aspect_hollow_sphere as g38
import arcana_g39_aspect_free_slip as g39
import arcana_g41_native_quadrature as g41

PIN='a7c95cf40aebf36f037d92b8553058e1f4916eaee53929d2d4c6df71bd11b9e6'
STATUS='G41_NATIVE_QUADRATURE_WEAK_BALANCE_PASS__EQUILIBRATED_REACTION_AND_STATE_REQUIRED'
AUTH='G42_SYNTHETIC_CBF_PARITY_ONLY_V1'
need,sha,read,write,inventory=g25.need,g25.sha,g25.read,g25.write,g25.inventory
CASES=g41.CASES
CPP=r'''
// SPDX-License-Identifier: GPL-2.0-or-later
// CBF formulation following ASPECT DynamicTopography (ASPECT authors,
// source/postprocess/dynamic_topography.cc, commit 30eb77ee5).
// Independently assemble the unconstrained residual over ALL cells, not
// just the boundary cells. No force or torque fit.
#include <aspect/postprocess/interface.h>
#include <aspect/postprocess/dynamic_topography.h>
#include <aspect/simulator_access.h>
#include <aspect/material_model/interface.h>
#include <aspect/gravity_model/interface.h>
#include <aspect/geometry_model/interface.h>
#include <deal.II/base/quadrature_lib.h>
#include <deal.II/fe/fe_values.h>
#include <fstream>
#include <iomanip>
#include <vector>
namespace aspect { namespace Postprocess {
template <int dim>
class ArcanaG42 : public Interface<dim>, public SimulatorAccess<dim>
{
public:
  std::list<std::string> required_other_postprocessors() const override
  { return {"dynamic topography"}; }
  std::pair<std::string,std::string> execute(TableHandler &) override
  {
    AssertThrow(dim==3 && Utilities::MPI::n_mpi_processes(this->get_mpi_communicator())==1,
                ExcMessage("G42 requires 3D singleton"));
    AssertThrow(!this->get_material_model().is_compressible(),ExcMessage("G42 incompressible only"));
    const auto &dh=this->get_dof_handler();
    const auto &elem=this->get_fe();
    const auto &vel=this->introspection().extractors.velocities;
    const unsigned int degree=elem.base_element(this->introspection().base_elements.velocities).degree;
    AssertThrow(degree==2,ExcMessage("G42 Q2 only"));
    const QGauss<dim> vq(degree+1);
    const QGaussLobatto<dim-1> fq(degree+1);
    FEValues<dim> fe(this->get_mapping(),elem,vq,
                      update_values|update_gradients|update_quadrature_points|update_JxW_values);
    FEFaceValues<dim> ff(this->get_mapping(),elem,fq,
                       update_values|update_quadrature_points|update_normal_vectors|update_JxW_values);
    const auto &native=this->get_postprocess_manager().template get_matching_active_plugin<DynamicTopography<dim>>().topography_vector();
    const auto inner=this->get_geometry_model().translate_symbolic_boundary_name_to_id("bottom");
    const auto outer=this->get_geometry_model().translate_symbolic_boundary_name_to_id("top");
    const unsigned int nd=elem.dofs_per_cell;
    const unsigned int nc=this->n_compositional_fields();
    std::vector<double> residual(dh.n_dofs(),0.),mass(dh.n_dofs(),0.);
    std::vector<int> component(dh.n_dofs(),-1);
    std::vector<types::global_dof_index> ids(nd);
    std::vector<unsigned int> active;
    for(unsigned int i=0;i<nd;++i)
      if(elem.system_to_component_index(i).first<dim) active.push_back(i);
    for(const auto &cell:dh.active_cell_iterators())
      if(cell->is_locally_owned())
      {
        cell->get_dof_indices(ids);
        fe.reinit(cell);
        MaterialModel::MaterialModelInputs<dim> in(vq.size(),nc);
        MaterialModel::MaterialModelOutputs<dim> out(vq.size(),nc);
        in.requested_properties=MaterialModel::MaterialProperties::density|MaterialModel::MaterialProperties::viscosity;
        in.reinit(fe,cell,this->introspection(),this->get_solution());
        this->get_material_model().fill_additional_material_model_inputs(in,this->get_solution(),fe,this->introspection());
        this->get_material_model().evaluate(in,out);
        for(const auto i:active)
        {
          component[ids[i]]=elem.system_to_component_index(i).first;
          double r=0.;
          for(unsigned int q=0;q<vq.size();++q)
          {
            const auto body=out.densities[q]*this->get_gravity_model().gravity_vector(in.position[q]);
            r+=fe.JxW(q)*(2*out.viscosities[q]*(fe[vel].symmetric_gradient(i,q)*in.strain_rate[q])
                -in.pressure[q]*fe[vel].divergence(i,q)-body*fe[vel].value(i,q));
          }
          residual[ids[i]]+=r;
        }
        for(const unsigned int face:cell->face_indices())
          if(cell->at_boundary(face))
          {
            const auto id=cell->face(face)->boundary_id();
            AssertThrow(id==inner || id==outer,ExcMessage("G42 unexpected boundary"));
            ff.reinit(cell,face);
            for(const auto i:active)
              for(unsigned int q=0;q<fq.size();++q)
                mass[ids[i]]+=ff.JxW(q)*ff[vel].value(i,q).norm_square();
          }
      }
    std::ofstream dofs(this->get_output_directory()+"G42_DOFS.dat");
    std::ofstream faces(this->get_output_directory()+"G42_FACES.dat");
    AssertThrow(dofs.good() && faces.good(),ExcMessage("G42 file open"));
    dofs<<std::scientific<<std::setprecision(17);
    faces<<std::scientific<<std::setprecision(17);
    unsigned int nv=0,nf=0;
    for(types::global_dof_index j=0;j<dh.n_dofs();++j)
      if(component[j]>=0)
      {
        dofs<<j<<' '<<component[j]<<' '<<mass[j]<<' '<<residual[j]<<' '
            <<this->get_solution()[j]<<' '<<native[j]<<'\n';
        ++nv;
      }
    unsigned int ci=0;
    std::vector<Tensor<1,dim>> u(fq.size()),cbf(fq.size());
    for(const auto &cell:dh.active_cell_iterators())
      if(cell->is_locally_owned())
      {
        ++ci;cell->get_dof_indices(ids);
        for(const unsigned int face:cell->face_indices())
          if(cell->at_boundary(face))
          {
            ff.reinit(cell,face);
            const int side=cell->face(face)->boundary_id()==inner?0:1;
            ff[vel].get_function_values(this->get_solution(),u);
            ff[vel].get_function_values(native,cbf);
            for(unsigned int q=0;q<fq.size();++q)
            {
              Tensor<1,dim> independent;
              for(const auto i:active)
                if(mass[ids[i]]>1.e-15)
                  independent+=ff[vel].value(i,q)*(residual[ids[i]]/mass[ids[i]]);
              faces<<ci<<' '<<face<<' '<<q<<' '<<side<<' '<<ff.JxW(q);
              for(unsigned int k=0;k<dim;++k) faces<<' '<<ff.quadrature_point(q)[k];
              for(unsigned int k=0;k<dim;++k) faces<<' '<<ff.normal_vector(q)[k];
              for(unsigned int k=0;k<dim;++k) faces<<' '<<u[q][k];
              for(unsigned int k=0;k<dim;++k) faces<<' '<<cbf[q][k];
              for(unsigned int k=0;k<dim;++k) faces<<' '<<independent[k];
              faces<<'\n';++nf;
            }
          }
      }
    dofs.close();faces.close();
    AssertThrow(dofs.good() && faces.good(),ExcMessage("G42 file write"));
    return {"G42 CBF records:",std::to_string(nv)+" "+std::to_string(nf)};
  }
};
ASPECT_REGISTER_POSTPROCESSOR(ArcanaG42,"arcana g42 cbf audit","Independent residual and native consistent boundary flux audit.")
}}
'''
CMAKE=g41.CMAKE.replace('arcana_g41','arcana_g42')

def build(out,state,root,hs):
    work=out/'plugin';work.mkdir()
    (work/'arcana_g42.cc').write_text(CPP)
    (work/'CMakeLists.txt').write_text(CMAKE)
    configs=set()
    for p in hs.rglob('CMakeCache.txt'):
        configs.update(re.findall(r'^Aspect_DIR:PATH=(.+)$',p.read_text(),re.M))
    configs={p for p in configs if p.startswith('/') and (root/p.lstrip('/')/'AspectConfig.cmake').is_file()}
    need(len(configs)<=1,'AMBIGUOUS_ASPECT_CMAKE')
    opts=['-DAspect_DIR='+next(iter(configs))] if configs else []
    g41.launch(work,state,root,['/usr/bin/cmake','-S','/tmp','-B','/tmp/build',*opts],'CONFIGURE',180)
    g41.launch(work,state,root,['/usr/bin/cmake','--build','/tmp/build','--target','arcana_g42.release','--parallel','1'],'BUILD',600)
    lib=work/'build/libarcana_g42.release.so'
    need(lib.is_file() and lib.stat().st_size>0,'PLUGIN_BUILD_OUTPUT')
    write(work/'PLUGIN_IDENTITY.json',{'source_sha256':sha(work/'arcana_g42.cc'),'cmake_sha256':sha(work/'CMakeLists.txt'),
        'plugin_sha256':sha(lib),'ASPECT_source_sha':ar.ASPECT_SHA})
    return lib

def prm_for(name):
    txt=g41.prm_for(name)
    need(txt.count('arcana g41 native quadrature')==1 and txt.count('./libarcana_g41.so')==1,'PRM_SCOPE')
    return txt.replace('./libarcana_g41.so','./libarcana_g42.so').replace('arcana g41 native quadrature','dynamic topography, arcana g42 cbf audit')

def norm(x):return float(np.linalg.norm(x))
def relative(a,b):return norm(a-b)/max(norm(b),1e-300)
def audit(d,f,old):
    need(d.ndim==2 and d.shape[1]==6 and f.ndim==2 and f.shape[1]==20,'SCHEMA')
    need(np.isfinite(d).all() and np.isfinite(f).all(),'FINITE')
    need(np.all(np.diff(d[:,0])>0) and set(d[:,1])=={0.,1.,2.} and np.min(d[:,2])>=0,'DOF_IDS')
    m,r,u,native=d[:,2:].T
    boundary=m>1e-15
    need(np.count_nonzero(boundary)>0 and np.count_nonzero(~boundary)>0,'DOF_PARTITION')
    need(np.max(m[~boundary])<1e-15,'MASS_COVERAGE')
    need(set(f[:,3])=={0.,1.} and np.all(f[:,4]>0),'FACE_SCHEMA')
    need(len(np.unique(f[:,:3],axis=0))==len(f),'DUPLICATE_FACE_IP')
    w,x,n,v,t,ind=f[:,4],f[:,5:8],f[:,8:11],f[:,11:14],f[:,14:17],f[:,17:20]
    need(np.max(abs(np.linalg.norm(n,axis=1)-1))<1e-12,'NORMALS')
    row_err=relative(r[boundary],m[boundary]*native[boundary])
    face_err=relative(ind,t)
    # These are distinct identities: work of the unconstrained residual on
    # the solution, and work of the native boundary CBF on the same trace.
    total_work=float(r@u)
    boundary_work=float(r[boundary]@u[boundary])
    interior_work=float(r[~boundary]@u[~boundary])
    face_work=float(np.sum(w*np.einsum('qi,qi->q',v,t)))
    D=old['audit']['dissipation_W']
    weak=old['audit']['weak_energy_residual_W']
    force=w@t
    moment=w@np.cross(x,t)
    body=np.array(old['audit']['body_force_N'])
    bodytorque=np.array(old['audit']['body_torque_Nm'])
    scale=max(norm(body),1.)
    sides={}
    for sid,label in ((0,'inner'),(1,'outer')):
        a=f[:,3]==sid
        radial=x[a]/np.linalg.norm(x[a],axis=1)[:,None]
        need(np.min(np.sum(n[a]*radial,axis=1)*(1 if sid else -1))>.99,'FACE_ORIENTATION')
        tr=t[a];nn=n[a];wa=w[a];vv=v[a]
        tangent=tr-np.sum(tr*nn,axis=1)[:,None]*nn
        sides[label]={'records':int(a.sum()),'area':float(wa.sum()),'force_N':(wa@tr).tolist(),
            'moment_Nm':(wa@np.cross(x[a],tr)).tolist(),'work_W':float(wa@np.sum(vv*tr,axis=1)),
            'tangential_traction_rms':float(np.sqrt(wa@np.sum(tangent*tangent,axis=1)/wa.sum())),
            'normal_velocity_rms':float(np.sqrt(wa@np.sum(vv*nn,axis=1)**2/wa.sum()))}
    checks={'native_CBF_dof_parity':row_err<1e-10,'native_CBF_face_parity':face_err<1e-10,
        'weak_work_replay':abs(total_work-weak)/max(D,1e-300)<1e-6,
        'adjoint_boundary_work':abs(face_work-boundary_work)/max(D,1e-300)<1e-8,
        'interior_work_small':abs(interior_work)/max(D,1e-300)<1e-5,
        'boundary_work_small':abs(boundary_work)/max(D,1e-300)<1e-5,
        'resultant_force_screen':norm(force+body)/scale<1e-4,
        'resultant_torque_screen':norm(moment+bodytorque)/scale<1e-4,
        'surface_area':all(abs(sides[k]['area']/a-1)<.005 for k,a in (('inner',np.pi),('outer',4*np.pi)))}
    return {'checks':{k:bool(v) for k,v in checks.items()},'screen_pass':all(checks.values()),
        'velocity_dofs':len(d),'boundary_dofs':int(boundary.sum()),'face_records':len(f),
        'native_CBF_dof_relative':row_err,'native_CBF_face_relative':face_err,
        'interior_residual_l2_N':norm(r[~boundary]),'boundary_residual_l2_N':norm(r[boundary]),
        'total_weak_work_W':total_work,'G41_weak_work_W':weak,'interior_work_W':interior_work,
        'boundary_dof_work_W':boundary_work,'boundary_quadrature_work_W':face_work,
        'force_residual_N':(force+body).tolist(),'moment_residual_Nm':(moment+bodytorque).tolist(),
        'force_relative':norm(force+body)/scale,'moment_relative':norm(moment+bodytorque)/scale,
        'G41_raw_face_work_W':old['audit']['raw_boundary_work_W'],'boundaries':sides}

def run_case(out,name,lib,state,root,p41):
    work=out/name;work.mkdir()
    prm=work/'input.prm';prm.write_text(prm_for(name))
    shutil.copyfile(lib,work/lib.name)
    g41.launch(work,state,root,['/home/dealii/aspect/bin/aspect-release','input.prm'],'RUN',600)
    s=(work/'RUN_STDOUT.txt').read_text()
    need(all(x in s for x in ('OPTIMIZED','3.2.0-pre','30eb77ee5','running with 1 MPI process','G42 CBF records:')),'RUNTIME_IDENTITY')
    old=read(p41/name/'CASE_REPORT.json')
    native=g39.parse_stats(work/'output/statistics')
    need(native['cells']==old['native']['cells'] and all(abs(native[k]-old['native'][k])/max(abs(old['native'][k]),1e-10)<1e-6 for k in ('rms','pmean','dissipation')),'G41_REPLAY')
    d=np.loadtxt(work/'output/G42_DOFS.dat',ndmin=2);f=np.loadtxt(work/'output/G42_FACES.dat',ndmin=2)
    need(len(f)==old['face_records'],'FACE_COUNT')
    row={'name':name,'native':native,'audit':audit(d,f,old)}
    write(work/'CASE_REPORT.json',row)
    print('G42_CASE',json.dumps(row,allow_nan=False),flush=True)
    return row
def main():
    ap=argparse.ArgumentParser()
    for k in ('base','recovery','inventory','g41','output'):ap.add_argument('--'+k,type=Path,required=True)
    ap.add_argument('--authorize-synthetic-cbf-only',choices=[AUTH],required=True)
    a=ap.parse_args();base,rec,inv,p41,out=(x.resolve() for x in (a.base,a.recovery,a.inventory,a.g41,a.output))
    source=Path(subprocess.check_output(['git','rev-parse','--show-toplevel'],text=True).strip()).resolve()
    def check():
        need(subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==g25.SOURCE and not subprocess.check_output(['git','status','--porcelain'],text=True).strip(),'SOURCE')
    def parents():return [g38.verified_bundle(rec,g38.PREC),g38.verified_bundle(inv,g38.PINV),g32.verify(p41,PIN,STATUS)]
    check();before=parents()
    need(not out.exists() and not any(out.is_relative_to(x) or x.is_relative_to(out) for x in (source,rec,inv,p41,base/'ARCANA_ASPECT_TOOLS')),'OUTPUT')
    out.mkdir();report={'source_sha':g25.SOURCE,'G41_manifest_sha256':PIN,'builds_attempted':0,'synthetic_solves_attempted':0,
        'ARCANA_solves':0,'additional_time_advance_years':0,'global_solve_authorized':False,'physical_acceptance':False,
        'mantle_provider_qualified':False,'physical_normal_reaction_authority':False,**g25.SCOPE}
    snapshot=None
    try:
        state,container,root,src,hs,_,_,_=g38.inputs(base,rec,inv)
        snapshot=ar.tree_metadata(container)
        for path in ('source/postprocess/dynamic_topography.cc','include/aspect/postprocess/dynamic_topography.h'):
            need((src/path).read_bytes()==subprocess.check_output(['git','-C',str(src),'show',ar.ASPECT_SHA+':'+path]),'CBF_SOURCE_DRIFT')
        report['builds_attempted']=1;lib=build(out,state,root,hs)
        report['cases']=[]
        for name in CASES:
            report['synthetic_solves_attempted']+=1
            report['cases'].append(run_case(out,name,lib,state,root,p41))
        # Pressure datum changes total traction, not the physical solution.
        # Compare its effect pointwise against -10*n; geometry and shape
        # functions may introduce a finite discretization error.
        v=np.loadtxt(out/'forced_volume_3/output/G42_FACES.dat')
        p=np.loadtxt(out/'forced_datum_3/output/G42_FACES.dat')
        need(np.array_equal(v[:,:11],p[:,:11]),'DATUM_FACE_IDENTITY')
        diff=p[:,14:17]-v[:,14:17]
        error=relative(diff,-10*v[:,8:11])
        report['datum_shift_relative']=error
        report['datum_shift_screen_pass']=error<.005
        need(all(r['audit']['screen_pass'] for r in report['cases']) and report['datum_shift_screen_pass'],'CBF_SCREEN')
        report.update(screen_pass=True,status='G42_SYNTHETIC_CBF_PARITY_PASS__MANTLE_STATE_AND_REAL_INTERFACE_REQUIRED')
    except Exception as e:report.update(screen_pass=False,status='G42_SYNTHETIC_CBF_BLOCKED',error=repr(e),traceback=traceback.format_exc())
    try:
        check();need(parents()==before,'PARENT_MUTATION')
        if snapshot is not None:need(ar.tree_metadata(container)==snapshot,'CONTAINER_DRIFT');g38.inputs(base,rec,inv)
        report['source_and_parents_unchanged']=True
    except Exception as e:report.update(screen_pass=False,status='G42_SYNTHETIC_CBF_BLOCKED',postcheck_error=repr(e))
    report['limitations']=['Uniform rank-one Q2 synthetic shells; no hanging-node or MPI verification.',
        'CBF uses unconstrained FE residual with GLL boundary mass; not pointwise exact stress.',
        'Force, torque and work screens are synthetic discrete integral checks, not physical reaction authority.',
        'No ARCANA load admission, no torque fitting, no absolute pressure authority.']
    for link in out.rglob('*'):
        if link.is_symlink():
            need(link.name in ('aspect','aspect-debug','aspect-release'),'UNEXPECTED_BUILD_LINK')
            link.unlink()
    write(out/'REPORT.json',report);write(out/'MANIFEST.json',{**report,'runner_sha256':sha(Path(__file__)),'files':inventory(out)})
    print(json.dumps(report,indent=2,allow_nan=False),flush=True)
    print('G42_MANIFEST_SHA256',sha(out/'MANIFEST.json'),flush=True)
    return 0 if report['screen_pass'] else 2
if __name__=='__main__':raise SystemExit(main())
