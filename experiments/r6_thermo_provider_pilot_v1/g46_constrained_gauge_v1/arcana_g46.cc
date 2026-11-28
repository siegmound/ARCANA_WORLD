// SPDX-License-Identifier: GPL-2.0-or-later
// G46 read-only diagnostics. No live velocity, force or pressure correction.
#include <aspect/postprocess/interface.h>
#include <aspect/simulator_access.h>
#include <aspect/material_model/interface.h>
#include <aspect/gravity_model/interface.h>
#include <aspect/termination_criteria/interface.h>
#include <deal.II/dofs/dof_tools.h>
#include <deal.II/fe/fe_values.h>
#include <deal.II/base/quadrature_lib.h>
#include <fstream>
#include <iomanip>
#include <cstdlib>
#include <map>
#include <memory>
namespace aspect {
namespace TerminationCriteria {
template<int dim> class G46Bound : public Interface<dim>, public SimulatorAccess<dim> {
 public:bool execute() override {
  const char *s=std::getenv("ARCANA_G46_STOP_TIME");AssertThrow(s,ExcMessage("G46 stop clock required"));double stop=std::stod(s);
  AssertThrow(stop>0&&stop<=.002,ExcMessage("G46 clock scope"));
  AssertThrow(this->get_time()<=.002+1e-14&&this->get_timestep_number()<=2,ExcMessage("G46 two-step hard guard"));
  return this->get_time()>=stop-1e-14;
 }
};
ASPECT_REGISTER_TERMINATION_CRITERION(G46Bound,"arcana g46 bound","Author-authorized synthetic two-step clock bound, no ARCANA evolution.")
}
namespace MaterialModel {
template<int dim> class G46Thermal : public Interface<dim>, public SimulatorAccess<dim> {
 std::unique_ptr<Interface<dim>> base;
 public:
 void parse_parameters(ParameterHandler &p) override {
  base=create_material_model<dim>("HollowSphereMaterial");
  if(auto *s=dynamic_cast<SimulatorAccess<dim>*>(base.get()))s->initialize_simulator(this->get_simulator());
  base->parse_parameters(p);this->model_dependence=base->get_model_dependence();
 }
 void initialize() override {base->initialize();}
 bool is_compressible() const override {return base->is_compressible();}
 void evaluate(const MaterialModelInputs<dim> &in,MaterialModelOutputs<dim> &out) const override {
  base->evaluate(in,out);for(unsigned i=0;i<in.n_evaluation_points();++i){out.specific_heat[i]=1.;out.thermal_conductivities[i]=.001;for(unsigned j=0;j<in.composition[i].size();++j)out.reaction_terms[i][j]=0.;}
 }
};
ASPECT_REGISTER_MATERIAL_MODEL(G46Thermal,"arcana g46 thermal hollow","Synthetic cp/conductivity wrapper only; native hollow sphere mechanics unchanged.")
}
namespace Postprocess {
template<int dim> class G46Restart : public Interface<dim>, public SimulatorAccess<dim> {
 void dump(std::string kind) const {
  const auto &dh=this->get_dof_handler();const auto &el=this->get_fe();const auto &intro=this->introspection();const auto owned=dh.locally_owned_dofs();unsigned rank=Utilities::MPI::this_mpi_process(this->get_mpi_communicator());
  std::string prefix=this->get_output_directory()+"G46R_"+kind+"_s"+std::to_string(this->get_timestep_number())+"_r"+std::to_string(rank);
  auto stream=[&](std::string suffix){std::ofstream f(prefix+suffix);AssertThrow(f.good(),ExcMessage("G46R write"));f<<std::scientific<<std::setprecision(17);return f;};
  std::vector<types::global_dof_index> ids(el.dofs_per_cell);std::map<types::global_dof_index,unsigned> comp;
  auto basis=stream("_BASIS.dat");for(const auto &cell:dh.active_cell_iterators())if(!cell->is_artificial()){
   cell->get_dof_indices(ids);for(unsigned i=0;i<ids.size();++i){comp[ids[i]]=el.system_to_component_index(i).first;if(cell->is_locally_owned())basis<<cell->id().to_string()<<' '<<i<<' '<<ids[i]<<' '<<comp[ids[i]]<<'\n';}}
  auto state=stream("_STATE.dat");for(auto id:owned)state<<id<<' '<<comp.at(id)<<' '<<this->get_solution()[id]<<' '<<this->get_old_solution()[id]<<' '<<this->get_old_old_solution()[id]<<'\n';
  std::vector<double> sum(2+intro.n_components,0.);FEValues<dim> fe(this->get_mapping(),el,intro.quadratures.system,update_values|update_JxW_values);std::vector<Vector<double>> v(fe.n_quadrature_points,Vector<double>(intro.n_components));
  for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){fe.reinit(cell);fe.get_function_values(this->get_solution(),v);MaterialModel::MaterialModelInputs<dim> in(fe.n_quadrature_points,this->n_compositional_fields());MaterialModel::MaterialModelOutputs<dim> out(fe.n_quadrature_points,this->n_compositional_fields());in.reinit(fe,cell,intro,this->get_solution());this->get_material_model().evaluate(in,out);for(unsigned q=0;q<fe.n_quadrature_points;++q){sum[0]+=fe.JxW(q)*out.densities[q];sum[1]+=fe.JxW(q)*out.densities[q]*out.specific_heat[q]*in.temperature[q];for(unsigned k=0;k<intro.n_components;++k)sum[2+k]+=fe.JxW(q)*v[q][k];}}
  auto summary=stream("_SUMMARY.dat");summary<<rank<<' '<<this->get_time()<<' '<<this->get_timestep_number()<<' '<<this->get_timestep()<<' '<<dh.n_dofs();for(auto x:sum)summary<<' '<<x;summary<<'\n';
 }
 public:void initialize() override {this->get_signals().pre_checkpoint_store_user_data.connect([this](parallel::distributed::Triangulation<dim> &){dump("checkpoint");});}
 std::pair<std::string,std::string> execute(TableHandler &) override {dump("postprocess");return {"G46R snapshot:",std::to_string(this->get_timestep_number())};}
};
ASPECT_REGISTER_POSTPROCESSOR(G46Restart,"arcana g46 restart state","All solution histories and integrals at actual native pre-checkpoint signal and postprocess.")

template<int dim> class G46 : public Interface<dim>, public SimulatorAccess<dim> {
 using BV=LinearAlgebra::BlockVector;using I=types::global_dof_index;
 public:std::pair<std::string,std::string> execute(TableHandler &) override {
  AssertThrow(dim==3,ExcMessage("G46 3D"));const auto comm=this->get_mpi_communicator();const unsigned rank=Utilities::MPI::this_mpi_process(comm);
  const auto &dh=this->get_dof_handler();const auto &el=this->get_fe();const auto &intro=this->introspection();const auto &vel=intro.extractors.velocities;
  const auto &part=intro.index_sets.system_partitioning;const auto &relpart=intro.index_sets.system_relevant_partitioning;
  const auto owned=dh.locally_owned_dofs();const auto relevant=intro.index_sets.system_relevant_set;const unsigned nd=el.dofs_per_cell;
  const auto &nativeC=this->get_current_constraints();AffineConstraints<double> H(owned,relevant),C(owned,relevant);
  DoFTools::make_hanging_node_constraints(dh,H);H.close();std::map<I,unsigned> comp;std::map<I,Point<dim>> pts;
  DoFTools::map_dofs_to_support_points(this->get_mapping(),dh,pts);std::vector<I> ids(nd);std::vector<unsigned> vi,pi;
  for(unsigned i=0;i<nd;++i){unsigned k=el.system_to_component_index(i).first;if(k<dim)vi.push_back(i);if(k==intro.component_indices.pressure)pi.push_back(i);}
  for(const auto &cell:dh.active_cell_iterators())if(!cell->is_artificial()){
   cell->get_dof_indices(ids);for(unsigned i=0;i<nd;++i)comp[ids[i]]=el.system_to_component_index(i).first;
  }
  for(const auto &line:nativeC.get_lines())if(comp.count(line.index)&&comp.at(line.index)<dim){C.add_line(line.index);for(const auto &e:line.entries)C.add_entry(line.index,e.first,e.second);}
  C.close();
  auto ghost=[&](const BV &x){auto p=std::make_unique<BV>(part,relpart,comm);*p=x;p->update_ghost_values();return p;};
  std::vector<std::unique_ptr<BV>> z;
  for(unsigned mode=0;mode<9;++mode){BV x(part,comm);const unsigned axis=mode%3;Tensor<1,dim> e;e[axis]=1.;
   for(auto id:owned)if(comp.count(id)&&comp.at(id)<dim)x[id]=cross_product_3d(e,Tensor<1,dim>(pts.at(id)))[comp.at(id)];
   x.compress(VectorOperation::insert);if(mode>=6)C.distribute(x);else if(mode>=3)H.distribute(x);z.push_back(ghost(x));
  }
  // Native nullspace acts on copies only: reconstruct difference from the live state.
  BV copy(part,comm);copy=this->get_solution();auto before=ghost(copy);auto after=ghost(copy);
  this->remove_nullspace(*after,copy);BV delta(part,comm);delta=copy;BV base(part,comm);base=this->get_solution();delta.add(-1.,base);z.push_back(ghost(delta));
  std::string prefix=this->get_output_directory()+"G46_s"+std::to_string(this->get_timestep_number())+"_r"+std::to_string(rank);
  auto stream=[&](std::string suffix){std::ofstream f(prefix+suffix);AssertThrow(f.good(),ExcMessage("G46 output"));f<<std::scientific<<std::setprecision(17);return f;};
  auto cs=stream("_C.dat"),hs=stream("_H.dat"),state=stream("_STATE.dat"),basis=stream("_BASIS.dat"),modes=stream("_MODES.dat");
  for(auto id:owned)if(comp.count(id)){
   state<<id<<' '<<comp.at(id);for(unsigned k=0;k<dim;++k)state<<' '<<pts.at(id)[k];state<<' '<<this->get_solution()[id]<<' '<<this->get_old_solution()[id]<<' '<<this->get_old_old_solution()[id]<<'\n';
   if(comp.at(id)<dim){for(auto *q:{&H,&C})if(q->is_constrained(id)){auto &f=(q==&H?hs:cs);f<<id<<" -1 "<<(q==&C?nativeC.get_inhomogeneity(id):0.)<<'\n';for(auto e:*q->get_constraint_entries(id))f<<id<<' '<<e.first<<' '<<e.second<<'\n';}
    modes<<id;for(auto &v:z)modes<<' '<<(*v)[id];modes<<'\n';}
  }
  const bool matrix=std::getenv("ARCANA_G46_MATRIX")!=nullptr;
  auto mat=stream("_KM.dat"),bmat=stream("_B.dat");
  std::vector<std::unique_ptr<BV>> actions;for(unsigned j=0;j<z.size();++j)actions.push_back(std::make_unique<BV>(part,comm));
  BV body(part,comm),pressure(part,comm);std::vector<double> totals(12*z.size()+12,0.);
  const auto &q=intro.quadratures.velocities;
  FEValues<dim> fe(this->get_mapping(),el,q,update_values|update_gradients|update_quadrature_points|update_JxW_values);
  FEFaceValues<dim> ff(this->get_mapping(),el,QGauss<dim-1>(5),update_values|update_normal_vectors|update_quadrature_points|update_JxW_values);
  auto faces=stream("_BOUNDARY.dat");
  for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){
   cell->get_dof_indices(ids);fe.reinit(cell);
   for(unsigned i=0;i<nd;++i)basis<<cell->id().to_string()<<' '<<i<<' '<<ids[i]<<' '<<el.system_to_component_index(i).first<<'\n';
   MaterialModel::MaterialModelInputs<dim> in(q.size(),this->n_compositional_fields());MaterialModel::MaterialModelOutputs<dim> out(q.size(),this->n_compositional_fields());in.requested_properties=MaterialModel::MaterialProperties::density|MaterialModel::MaterialProperties::viscosity;in.reinit(fe,cell,intro,this->get_solution());this->get_material_model().evaluate(in,out);
   std::vector<std::vector<Tensor<1,dim>>> values(z.size(),std::vector<Tensor<1,dim>>(q.size()));
   std::vector<std::vector<SymmetricTensor<2,dim>>> strains(z.size(),std::vector<SymmetricTensor<2,dim>>(q.size()));
   for(unsigned j=0;j<z.size();++j){fe[vel].get_function_values(*z[j],values[j]);fe[vel].get_function_symmetric_gradients(*z[j],strains[j]);}
   std::vector<Vector<double>> local(z.size(),Vector<double>(nd));Vector<double> lf(nd),lp(nd);
   for(unsigned k=0;k<q.size();++k){const double w=fe.JxW(k);auto f=out.densities[k]*this->get_gravity_model().gravity_vector(fe.quadrature_point(k));
    for(auto i:vi){lf[i]+=w*f*fe[vel].value(i,k);lp[i]+=-10*w*fe[vel].divergence(i,k);for(unsigned j=0;j<z.size();++j)local[j][i]+=w*2*out.viscosities[k]*(fe[vel].symmetric_gradient(i,k)*strains[j][k]);}
    for(unsigned j=0;j<z.size();++j){const unsigned t=12*j;totals[t]+=w*values[j][k].norm_square();totals[t+1]+=w*2*out.viscosities[k]*(strains[j][k]*strains[j][k]);totals[t+2]+=w*trace(strains[j][k])*trace(strains[j][k]);totals[t+3]+=w*f*values[j][k];auto L=cross_product_3d(Tensor<1,dim>(fe.quadrature_point(k)),values[j][k]);for(unsigned a=0;a<dim;++a)totals[t+4+a]+=w*L[a];}
    const unsigned t=12*z.size();totals[t]+=w;totals[t+1]+=w*in.velocity[k].norm_square();totals[t+2]+=w*2*out.viscosities[k]*(in.strain_rate[k]*in.strain_rate[k]);totals[t+3]+=w*trace(in.strain_rate[k])*trace(in.strain_rate[k]);auto L=cross_product_3d(Tensor<1,dim>(fe.quadrature_point(k)),in.velocity[k]);for(unsigned a=0;a<dim;++a)totals[t+4+a]+=w*L[a];
   }
   for(unsigned j=0;j<z.size();++j)cell->distribute_local_to_global(local[j],*actions[j]);cell->distribute_local_to_global(lf,body);cell->distribute_local_to_global(lp,pressure);
   if(matrix){for(auto i:vi)for(auto j:vi){double a=0,m=0;for(unsigned k=0;k<q.size();++k){a+=fe.JxW(k)*2*out.viscosities[k]*(fe[vel].symmetric_gradient(i,k)*fe[vel].symmetric_gradient(j,k));m+=fe.JxW(k)*fe[vel].value(i,k)*fe[vel].value(j,k);}if(a!=0||m!=0)mat<<ids[i]<<' '<<ids[j]<<' '<<a<<' '<<m<<'\n';}
    for(auto i:pi)for(auto j:vi){double a=0;for(unsigned k=0;k<q.size();++k)a-=fe.JxW(k)*fe.shape_value_component(i,k,intro.component_indices.pressure)*fe[vel].divergence(j,k);if(a!=0)bmat<<ids[i]<<' '<<ids[j]<<' '<<a<<'\n';}}
   for(auto face:cell->face_indices())if(cell->at_boundary(face)){ff.reinit(cell,face);std::vector<Tensor<1,dim>> u(ff.n_quadrature_points);ff[vel].get_function_values(this->get_solution(),u);
    std::vector<std::vector<Tensor<1,dim>>> v(z.size(),std::vector<Tensor<1,dim>>(ff.n_quadrature_points));for(unsigned j=0;j<z.size();++j)ff[vel].get_function_values(*z[j],v[j]);
    for(unsigned k=0;k<ff.n_quadrature_points;++k){faces<<cell->id().to_string()<<' '<<face<<' '<<k<<' '<<ff.JxW(k)<<' '<<u[k]*ff.normal_vector(k);for(unsigned j=0;j<z.size();++j)faces<<' '<<v[j][k]*ff.normal_vector(k);faces<<'\n';}}
  }
  for(auto &v:actions)v->compress(VectorOperation::add);body.compress(VectorOperation::add);pressure.compress(VectorOperation::add);
  auto act=stream("_ACTION.dat");for(auto id:owned)if(comp.count(id)&&comp.at(id)<dim){act<<id<<' '<<body[id]<<' '<<pressure[id];for(auto &v:actions)act<<' '<<(*v)[id];act<<'\n';}
  // Constant-pressure divergence theorem, same mesh/mapping, independent quadratures.
  for(unsigned order:{3u,5u,7u}){BV r(part,comm);FEValues<dim> fv(this->get_mapping(),el,QGauss<dim>(order),update_gradients|update_JxW_values);
   for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){cell->get_dof_indices(ids);fv.reinit(cell);Vector<double> l(nd);for(auto i:vi)for(unsigned k=0;k<fv.n_quadrature_points;++k)l[i]-=10*fv.JxW(k)*fv[vel].divergence(i,k);cell->distribute_local_to_global(l,r);}r.compress(VectorOperation::add);auto f=stream("_PV"+std::to_string(order)+".dat");for(auto id:owned)if(comp.count(id)&&comp.at(id)<dim)f<<id<<' '<<r[id]<<'\n';}
  for(unsigned rule:{0u,3u,5u,7u}){BV r(part,comm);std::unique_ptr<Quadrature<dim-1>> fq;if(rule==0)fq=std::make_unique<QGaussLobatto<dim-1>>(3);else fq=std::make_unique<QGauss<dim-1>>(rule);FEFaceValues<dim> fv(this->get_mapping(),el,*fq,update_values|update_normal_vectors|update_JxW_values);
   for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){cell->get_dof_indices(ids);Vector<double> l(nd);for(auto face:cell->face_indices())if(cell->at_boundary(face)){fv.reinit(cell,face);for(auto i:vi)for(unsigned k=0;k<fv.n_quadrature_points;++k)l[i]-=10*fv.JxW(k)*fv[vel].value(i,k)*fv.normal_vector(k);}cell->distribute_local_to_global(l,r);}r.compress(VectorOperation::add);auto f=stream("_PS"+std::to_string(rule)+".dat");for(auto id:owned)if(comp.count(id)&&comp.at(id)<dim)f<<id<<' '<<r[id]<<'\n';}
  auto summary=stream("_SUMMARY.dat");summary<<rank<<' '<<this->get_time()<<' '<<this->get_timestep_number()<<' '<<q.size()<<' '<<this->get_pressure_scaling()<<' '<<dh.n_dofs();for(double t:totals)summary<<' '<<t;summary<<'\n';
  return {"G46 diagnostic only:",std::to_string(rank)};
 }
};
ASPECT_REGISTER_POSTPROCESSOR(G46,"arcana g46 operator","Read-only C/H, native operator action, spectrum exports and quadrature diagnosis; no gauge repair assumed.")
}}
