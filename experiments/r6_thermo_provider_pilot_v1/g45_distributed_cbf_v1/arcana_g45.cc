// SPDX-License-Identifier: GPL-2.0-or-later
// Independent all-cell residual and topology-only distributed trace solve.
// Native-parity branch follows ASPECT DynamicTopography, commit 30eb77ee5.
#include <aspect/postprocess/interface.h>
#include <aspect/postprocess/dynamic_topography.h>
#include <aspect/simulator_access.h>
#include <aspect/material_model/interface.h>
#include <aspect/gravity_model/interface.h>
#include <aspect/geometry_model/interface.h>
#include <aspect/mesh_refinement/interface.h>
#include <deal.II/base/quadrature_lib.h>
#include <deal.II/fe/fe_values.h>
#include <deal.II/dofs/dof_tools.h>
#include <deal.II/lac/affine_constraints.h>
#include <fstream>
#include <iomanip>
#include <map>
#include <set>
#include <cmath>
namespace aspect {
namespace MeshRefinement {
template <int dim> class ArcanaG45Refine : public Interface<dim>, public SimulatorAccess<dim> {
 public:
 void execute(Vector<float> &v) const override {v=0.;}
 void tag_additional_cells() const override {
  if(this->get_dof_handler().n_dofs()==0) return;
  for(const auto &cell:this->get_triangulation().active_cell_iterators()) if(cell->is_locally_owned()) {
   cell->clear_refine_flag();cell->clear_coarsen_flag();
   if(cell->center()[0]>0.1 && cell->center()[1]>-0.2)cell->set_refine_flag();
  }
 }
};
ASPECT_REGISTER_MESH_REFINEMENT_CRITERION(ArcanaG45Refine,"arcana g45 deterministic","Synthetic geometric local refinement, independent of partition.")
}
namespace Postprocess {
template <int dim> class ArcanaG45 : public Interface<dim>, public SimulatorAccess<dim> {
 using BV=LinearAlgebra::BlockVector;using I=types::global_dof_index;
 struct FaceMass {std::vector<I> ids;Vector<double> m;};
 public:
 std::list<std::string> required_other_postprocessors() const override {return {"dynamic topography"};}
 std::pair<std::string,std::string> execute(TableHandler &) override {
  AssertThrow(dim==3,ExcMessage("G45 3D only"));
  AssertThrow(!this->get_material_model().is_compressible(),ExcMessage("G45 incompressible only"));
  const auto comm=this->get_mpi_communicator();const auto rank=Utilities::MPI::this_mpi_process(comm);
  const auto &dh=this->get_dof_handler();const auto &elem=this->get_fe();const auto &vel=this->introspection().extractors.velocities;
  const auto &part=this->introspection().index_sets.system_partitioning;
  const auto &relpart=this->introspection().index_sets.system_relevant_partitioning;
  const auto &relevant=this->introspection().index_sets.system_relevant_set;
  const auto owned=dh.locally_owned_dofs();const unsigned nd=elem.dofs_per_cell;
  AssertThrow(elem.base_element(this->introspection().base_elements.velocities).degree==2,ExcMessage("G45 Q2 only"));
  AffineConstraints<double> H(owned,relevant);DoFTools::make_hanging_node_constraints(dh,H);H.close();
  AssertThrow(!H.has_inhomogeneities(),ExcMessage("G45 affine topology not supported"));
  const QGauss<dim> vq(3);const QGaussLobatto<dim-1> fq(3);
  FEValues<dim> fe(this->get_mapping(),elem,vq,update_values|update_gradients|update_quadrature_points|update_JxW_values);
  FEFaceValues<dim> ff(this->get_mapping(),elem,fq,update_values|update_gradients|update_normal_vectors|update_quadrature_points|update_JxW_values);
  const auto inner=this->get_geometry_model().translate_symbolic_boundary_name_to_id("bottom");
  const auto outer=this->get_geometry_model().translate_symbolic_boundary_name_to_id("top");
  const auto &native=this->get_postprocess_manager().template get_matching_active_plugin<DynamicTopography<dim>>().topography_vector();
  BV r(part,comm),rb(part,comm),mass(part,comm),rh(part,comm),b(part,comm),bh(part,comm),diag(part,comm);
  std::vector<FaceMass> boundary;std::vector<I> ids(nd);std::vector<unsigned> active;
  for(unsigned i=0;i<nd;++i)if(elem.system_to_component_index(i).first<dim)active.push_back(i);
  std::map<I,unsigned> components;std::map<I,Point<dim>> points;
  DoFTools::map_dofs_to_support_points(this->get_mapping(),dh,points);
  for(const auto &cell:dh.active_cell_iterators()) if(!cell->is_artificial()){
   cell->get_dof_indices(ids);for(auto i:active)components[ids[i]]=elem.system_to_component_index(i).first;
  }
  auto expand=[&](I id,const BV &x){double value=0.;const auto *entries=H.get_constraint_entries(id);
   if(entries){for(const auto &e:*entries)value+=e.second*x[e.first];}else value=x[id];return value;};
  const std::string prefix=this->get_output_directory()+"G45_s"+std::to_string(this->get_timestep_number())+"_r"+std::to_string(rank);
  auto stream=[&](const std::string &suffix){std::ofstream o(prefix+suffix);AssertThrow(o.good(),ExcMessage("G45 output open"));o<<std::scientific<<std::setprecision(17);return o;};
  auto cells=stream("_CELLS.dat");auto basis=stream("_BASIS.dat");
  unsigned ncells=0,nfaces=0;const unsigned nc=this->n_compositional_fields();
  for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){
   ++ncells;cell->get_dof_indices(ids);fe.reinit(cell);Vector<double> lr(nd),lh(nd);
   unsigned nf=0;for(auto f:cell->face_indices())if(cell->at_boundary(f)){
    AssertThrow(cell->face(f)->boundary_id()==inner||cell->face(f)->boundary_id()==outer,ExcMessage("G45 boundary identity"));++nf;
   }
   AssertThrow(nf<=1,ExcMessage("G45 native single-boundary-face assumption"));
   MaterialModel::MaterialModelInputs<dim> in(vq.size(),nc);MaterialModel::MaterialModelOutputs<dim> out(vq.size(),nc);
   in.requested_properties=MaterialModel::MaterialProperties::density|MaterialModel::MaterialProperties::viscosity;
   in.reinit(fe,cell,this->introspection(),this->get_solution());
   this->get_material_model().fill_additional_material_model_inputs(in,this->get_solution(),fe,this->introspection());this->get_material_model().evaluate(in,out);
   double volume=0.,D=0.,B=0.,P=0.,Fabs=0.,Wabs=0.;Tensor<1,dim> force,torque;
   for(unsigned q=0;q<vq.size();++q){const double w=fe.JxW(q);AssertThrow(w>0,ExcMessage("G45 positive volume Jacobian"));
    const auto gravity=this->get_gravity_model().gravity_vector(in.position[q]);const auto body=out.densities[q]*gravity;
    const double ph=1000*(1-in.position[q].norm());
    volume+=w;D+=w*2*out.viscosities[q]*(in.strain_rate[q]*in.strain_rate[q]);B+=w*(body*in.velocity[q]);P+=w*in.pressure[q]*trace(in.strain_rate[q]);
    force+=w*body;if constexpr(dim==3)torque+=w*cross_product_3d(Tensor<1,dim>(in.position[q]),body);Fabs+=w*body.norm();Wabs+=w*std::abs(body*in.velocity[q]);
    for(auto i:active){lr[i]+=w*(2*out.viscosities[q]*(fe[vel].symmetric_gradient(i,q)*in.strain_rate[q])-in.pressure[q]*fe[vel].divergence(i,q)-body*fe[vel].value(i,q));
     lh[i]+=w*(-ph*fe[vel].divergence(i,q)-1000*gravity*fe[vel].value(i,q));}
   }
   cell->distribute_local_to_global(lr,r);cell->distribute_local_to_global(lh,rh);
   H.distribute_local_to_global(lr,ids,b);H.distribute_local_to_global(lh,ids,bh);
   if(nf)cell->distribute_local_to_global(lr,rb);
   for(auto f:cell->face_indices())if(cell->at_boundary(f)){
    ++nfaces;ff.reinit(cell,f);FaceMass fm;fm.ids=ids;fm.m.reinit(nd);
    for(auto i:active)for(unsigned q=0;q<fq.size();++q)fm.m[i]+=ff.JxW(q)*ff[vel].value(i,q).norm_square();
    cell->distribute_local_to_global(fm.m,mass);
    for(auto i:active)if(fm.m[i]>0){const auto *entries=H.get_constraint_entries(ids[i]);
     if(entries)for(const auto &e:*entries)diag[e.first]+=fm.m[i]*e.second*e.second;
     else diag[ids[i]]+=fm.m[i];}
    boundary.push_back(std::move(fm));
   }
   cells<<cell->id().to_string()<<' '<<cell->level()<<' '<<nf;
   for(unsigned v=0;v<GeometryInfo<dim>::vertices_per_cell;++v)for(unsigned k=0;k<dim;++k)cells<<' '<<cell->vertex(v)[k];
   cells<<' '<<volume<<' '<<D<<' '<<B<<' '<<P;for(unsigned k=0;k<dim;++k)cells<<' '<<force[k];for(unsigned k=0;k<dim;++k)cells<<' '<<torque[k];cells<<' '<<Fabs<<' '<<Wabs<<'\n';
   for(auto i:active){basis<<cell->id().to_string()<<' '<<i<<' '<<ids[i]<<' '<<elem.system_to_component_index(i).first;
    for(unsigned k=0;k<dim;++k)basis<<' '<<points.at(ids[i])[k];basis<<'\n';}
  }
  for(auto *v:{&r,&rb,&mass,&rh,&b,&bh,&diag})v->compress(VectorOperation::add);
  for(auto id:owned)if(diag[id]<=1e-20){b[id]=0.;bh[id]=0.;}
  b.compress(VectorOperation::insert);bh.compress(VectorOperation::insert);
  auto ghost=[&](const BV &x,BV &g){g.reinit(part,relpart,comm);g=x;g.update_ghost_values();};
  auto apply=[&](const BV &x,BV &y){BV gx;ghost(x,gx);y=0.;
   for(const auto &fm:boundary){Vector<double> local(nd);for(auto i:active)if(fm.m[i]>0)local[i]=fm.m[i]*expand(fm.ids[i],gx);H.distribute_local_to_global(local,fm.ids,y);}
   y.compress(VectorOperation::add);for(auto id:owned)if(diag[id]<=1e-20)y[id]=x[id];y.compress(VectorOperation::insert);
  };
  auto solve=[&](const BV &rhs,BV &x){x.reinit(part,comm);BV res(rhs),z(part,comm),p(part,comm),ap(part,comm);double norm=rhs.l2_norm();if(norm==0)return std::make_pair(0u,0.);
   for(auto id:owned)if(diag[id]>1e-20)z[id]=res[id]/diag[id];z.compress(VectorOperation::insert);p=z;double rz=res*z;unsigned it=0;
   for(;it<2000;++it){apply(p,ap);const double pap=p*ap;AssertThrow(pap>0&&std::isfinite(pap),ExcMessage("G45 trace SPD violation"));const double alpha=rz/pap;x.add(alpha,p);res.add(-alpha,ap);
    if(res.l2_norm()<=1e-13*norm){++it;break;}z=0.;for(auto id:owned)if(diag[id]>1e-20)z[id]=res[id]/diag[id];z.compress(VectorOperation::insert);const double next=res*z;p.sadd(next/rz,1.,z);rz=next;
   }
   apply(x,ap);ap.add(-1.,rhs);const double error=ap.l2_norm()/norm;AssertThrow(error<=1e-12,ExcMessage("G45 trace CG convergence"));return std::make_pair(it,error);
  };
  BV x,hx;auto cg=solve(b,x);auto cgh=solve(bh,hx);
  BV gx,gh;ghost(x,gx);ghost(hx,gh);BV full(part,comm),fullh(part,comm),raw(part,comm),replica(part,comm);
  for(auto id:owned){full[id]=expand(id,gx);fullh[id]=expand(id,gh);if(mass[id]>1e-15){raw[id]=r[id]/mass[id];replica[id]=rb[id]/mass[id];}}
  for(auto *v:{&full,&fullh,&raw,&replica})v->compress(VectorOperation::insert);
  BV gfull,gfullh,graw,greplica;ghost(full,gfull);ghost(fullh,gfullh);ghost(raw,graw);ghost(replica,greplica);
  auto dofs=stream("_DOFS.dat");auto constraints=stream("_H.dat");auto ghosts=stream("_GHOSTS.dat");
  unsigned nowned=0,nh=0,nbh=0,ntrace=0;
  for(auto id:owned)if(components.count(id)){
   ++nowned;const auto *entries=H.get_constraint_entries(id);if(entries){++nh;if(mass[id]>1e-15)++nbh;for(const auto &e:*entries)constraints<<id<<' '<<e.first<<' '<<e.second<<'\n';}
   if(diag[id]>1e-20)++ntrace;
   dofs<<id<<' '<<components.at(id);for(unsigned k=0;k<dim;++k)dofs<<' '<<points.at(id)[k];
   dofs<<' '<<this->get_solution()[id]<<' '<<native[id]<<' '<<r[id]<<' '<<rb[id]<<' '<<mass[id]<<' '<<b[id]<<' '<<diag[id]<<' '<<x[id]<<' '<<full[id]<<' '<<rh[id]<<' '<<fullh[id]<<' '<<(entries?1:0)<<'\n';
  }
  for(auto id:relevant)if(!owned.is_element(id)&&components.count(id))ghosts<<id<<' '<<this->get_solution()[id]<<' '<<gfull[id]<<' '<<graw[id]<<'\n';
  auto faces=stream("_FACES.dat");std::vector<Tensor<1,dim>> u(fq.size()),nt(fq.size()),rt(fq.size()),ct(fq.size()),ht(fq.size()),nr(fq.size());
  for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){
   cell->get_dof_indices(ids);for(auto f:cell->face_indices())if(cell->at_boundary(f)){
    ff.reinit(cell,f);ff[vel].get_function_values(this->get_solution(),u);ff[vel].get_function_values(native,nt);ff[vel].get_function_values(graw,rt);ff[vel].get_function_values(gfull,ct);ff[vel].get_function_values(gfullh,ht);ff[vel].get_function_values(greplica,nr);
    MaterialModel::MaterialModelInputs<dim> in(fq.size(),nc);MaterialModel::MaterialModelOutputs<dim> out(fq.size(),nc);in.requested_properties=MaterialModel::MaterialProperties::density|MaterialModel::MaterialProperties::viscosity;
    in.reinit(ff,cell,this->introspection(),this->get_solution());this->get_material_model().evaluate(in,out);
    for(unsigned q=0;q<fq.size();++q){faces<<cell->id().to_string()<<' '<<f<<' '<<q<<' '<<(cell->face(f)->boundary_id()==inner?0:1)<<' '<<ff.JxW(q);
     for(unsigned k=0;k<dim;++k)faces<<' '<<ff.quadrature_point(q)[k];for(unsigned k=0;k<dim;++k)faces<<' '<<ff.normal_vector(q)[k];
     for(const auto &value:{u[q],nt[q],nr[q],rt[q],ct[q],ht[q]})for(unsigned k=0;k<dim;++k)faces<<' '<<value[k];
     const auto stress=2*out.viscosities[q]*in.strain_rate[q]-in.pressure[q]*unit_symmetric_tensor<dim>();const auto traction=stress*ff.normal_vector(q);
     for(unsigned k=0;k<dim;++k)faces<<' '<<traction[k];faces<<' '<<in.pressure[q]<<' '<<out.densities[q]<<' '<<out.viscosities[q];
     for(unsigned k=0;k<dim;++k){I node=numbers::invalid_dof_index;for(auto i:active)if(elem.system_to_component_index(i).first==k&&std::abs(ff[vel].value(i,q)[k]-1)<1e-10){AssertThrow(node==numbers::invalid_dof_index,ExcMessage("G45 GLL duplicate support"));node=ids[i];}AssertThrow(node!=numbers::invalid_dof_index,ExcMessage("G45 GLL not nodal"));faces<<' '<<node;}faces<<'\n';
    }
   }
  }
  auto summary=stream("_SUMMARY.dat");summary<<rank<<' '<<ncells<<' '<<nfaces<<' '<<nowned<<' '<<nh<<' '<<nbh<<' '<<ntrace<<' '<<dh.n_dofs()<<' '<<cg.first<<' '<<cg.second<<' '<<cgh.first<<' '<<cgh.second<<' '<<this->get_time()<<' '<<this->get_timestep_number()<<'\n';
  for(auto *o:{&cells,&basis,&dofs,&constraints,&ghosts,&faces,&summary}){o->close();AssertThrow(o->good(),ExcMessage("G45 output write"));}
  return {"G45 distributed constrained CBF:",std::to_string(rank)+" cells="+std::to_string(ncells)+" traceCG="+std::to_string(cg.first)};
 }
};
ASPECT_REGISTER_POSTPROCESSOR(ArcanaG45,"arcana g45 distributed cbf","Synthetic distributed raw CBF and topology-condensed trace; no physical admission.")
}}
