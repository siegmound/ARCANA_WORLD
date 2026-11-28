// SPDX-License-Identifier: GPL-2.0-or-later
// Bounded single-rank native FE integration of immutable G45 field differences.
#include <aspect/postprocess/interface.h>
#include <aspect/simulator_access.h>
#include <aspect/material_model/interface.h>
#include <deal.II/dofs/dof_tools.h>
#include <deal.II/fe/fe_values.h>
#include <deal.II/base/quadrature_lib.h>
#include <fstream>
#include <iomanip>
#include <map>
#include <cstdlib>
namespace aspect {namespace Postprocess {
template<int dim> class G46Norms : public Interface<dim>, public SimulatorAccess<dim> {
 using BV=LinearAlgebra::BlockVector;using I=types::global_dof_index;
 public:std::pair<std::string,std::string> execute(TableHandler &) override {
  const auto comm=this->get_mpi_communicator();AssertThrow(dim==3&&Utilities::MPI::n_mpi_processes(comm)==1,ExcMessage("G46 bounded retained-field coordinator only, not replicated MPI arrays"));
  const auto &dh=this->get_dof_handler();const auto &el=this->get_fe();const auto &in=this->introspection();const auto &vel=in.extractors.velocities;const auto owned=dh.locally_owned_dofs();const auto relevant=in.index_sets.system_relevant_set;
  std::vector<I> ids(el.dofs_per_cell);std::map<I,std::string> stable;std::map<I,unsigned> comp;
  for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){cell->get_dof_indices(ids);for(unsigned i=0;i<ids.size();++i)if(el.system_to_component_index(i).first<dim){auto id=ids[i];std::string key=cell->id().to_string()+"/"+std::to_string(i);if(!stable.count(id)||key<stable[id])stable[id]=key;comp[id]=el.system_to_component_index(i).first;}}
  const char *source=std::getenv("ARCANA_G46_RETAINED_FIELDS");AssertThrow(source,ExcMessage("G46 immutable retained-field input required"));std::ifstream file(source);unsigned count,nfield;file>>count>>nfield;AssertThrow(file.good()&&nfield>0&&nfield<=8&&count==stable.size(),ExcMessage("G46 retained input header"));std::map<std::string,std::vector<double>> data;
  for(unsigned i=0;i<count;++i){std::string key;file>>key;std::vector<double> values(nfield);for(double &x:values)file>>x;AssertThrow(file.good()&&!data.count(key),ExcMessage("G46 retained key/value"));data.emplace(key,std::move(values));}
  std::vector<std::unique_ptr<BV>> fields;std::vector<double> cdef(nfield),hdef(nfield);AffineConstraints<double> H(owned,relevant);DoFTools::make_hanging_node_constraints(dh,H);H.close();
  for(unsigned j=0;j<nfield;++j){BV v(in.index_sets.system_partitioning,comm);for(auto &p:stable){AssertThrow(data.count(p.second),ExcMessage("G46 stable cross-case identity"));v[p.first]=data.at(p.second)[j];}v.compress(VectorOperation::insert);BV hv(v),cv(v);H.distribute(hv);this->get_current_constraints().distribute(cv);hv.add(-1.,v);cv.add(-1.,v);hdef[j]=hv.l2_norm()/std::max(v.l2_norm(),1.);cdef[j]=cv.l2_norm()/std::max(v.l2_norm(),1.);auto g=std::make_unique<BV>(in.index_sets.system_partitioning,in.index_sets.system_relevant_partitioning,comm);*g=v;g->update_ghost_values();fields.push_back(std::move(g));}
  const auto &q=in.quadratures.velocities;FEValues<dim> fe(this->get_mapping(),el,q,update_values|update_gradients|update_quadrature_points|update_JxW_values);FEFaceValues<dim> ff(this->get_mapping(),el,QGauss<dim-1>(5),update_values|update_normal_vectors|update_JxW_values);
  std::vector<double> total(7*nfield,0.);
  for(const auto &cell:dh.active_cell_iterators())if(cell->is_locally_owned()){
   fe.reinit(cell);MaterialModel::MaterialModelInputs<dim> input(q.size(),this->n_compositional_fields());MaterialModel::MaterialModelOutputs<dim> out(q.size(),this->n_compositional_fields());input.reinit(fe,cell,in,this->get_solution());input.requested_properties=MaterialModel::MaterialProperties::viscosity;this->get_material_model().evaluate(input,out);
   for(unsigned j=0;j<nfield;++j){std::vector<Tensor<1,dim>> u(q.size());std::vector<SymmetricTensor<2,dim>> eps(q.size());fe[vel].get_function_values(*fields[j],u);fe[vel].get_function_symmetric_gradients(*fields[j],eps);const unsigned p=7*j;
    for(unsigned k=0;k<q.size();++k){double w=fe.JxW(k);total[p]+=w*u[k].norm_square();total[p+1]+=w*2*out.viscosities[k]*(eps[k]*eps[k]);total[p+2]+=w*trace(eps[k])*trace(eps[k]);auto L=cross_product_3d(Tensor<1,dim>(fe.quadrature_point(k)),u[k]);for(unsigned a=0;a<dim;++a)total[p+3+a]+=w*L[a];}
    for(auto face:cell->face_indices())if(cell->at_boundary(face)){ff.reinit(cell,face);std::vector<Tensor<1,dim>> v(ff.n_quadrature_points);ff[vel].get_function_values(*fields[j],v);for(unsigned k=0;k<ff.n_quadrature_points;++k){double n=v[k]*ff.normal_vector(k);total[p+6]+=ff.JxW(k)*n*n;}}
   }
  }
  std::ofstream out(this->get_output_directory()+"G46_RETAINED_NORMS.dat");out<<std::scientific<<std::setprecision(17);for(unsigned j=0;j<nfield;++j){out<<j<<' '<<cdef[j]<<' '<<hdef[j];for(unsigned k=0;k<7;++k)out<<' '<<total[7*j+k];out<<'\n';}out.close();AssertThrow(out.good(),ExcMessage("G46 norms write"));return {"G46 retained raw field norms:",std::to_string(nfield)};
 }
};
ASPECT_REGISTER_POSTPROCESSOR(G46Norms,"arcana g46 retained norms","Single-rank actual FE norms of retained raw G45 differences; never adjusts native solution.")
}}
