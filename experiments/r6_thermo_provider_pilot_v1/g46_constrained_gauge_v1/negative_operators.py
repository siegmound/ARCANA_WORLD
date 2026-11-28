"""Real artifact overlays through production loaders; never mutate source shards."""
import sys,shutil,json
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
sys.path.insert(0,str(c.CODE));import oracle,datum
sys.path.insert(0,str(c.prior.CODE));import audit

def main():
 c.check();out=c.ROOT/'NEGATIVE_OPERATOR_DATUM_NEW01';out.mkdir();coarse=c.ROOT/'forced_l2_a1_p1_interior_flux_NEW01';mpi=c.ROOT/'forced_l2_a1_p4_original_NEW01';small=c.ROOT/'forced_l1_a1_p1_small_matrix_NEW01';before={str(p):c.prior.old.g25.inventory(p/'output') for p in [coarse,mpi,small]};rows=[]
 def overlay(kind,source):
  p=out/kind;p.mkdir();shutil.copy2(source/'CASE_SPEC.json',p/'CASE_SPEC.json');(p/'output').mkdir()
  for f in (source/'output').iterdir():
   if f.is_file():(p/'output'/f.name).symlink_to(f)
  return p
 def replace(p,text):
  c.need(p.is_symlink(),'OVERLAY_NOT_SYMLINK');p.unlink();p.write_text(text)
 def reject(name,call,expected):
  try:call();error=None;ok=False
  except Exception as e:error=repr(e);ok=expected in str(e)
  rows.append({'name':name,'expected_gate':expected,'error':error,'screen_pass':ok});print('G46_NEGATIVE',name,ok,flush=True)
 # Candidate modes are actual native FE vectors; no fitted velocity enters admission.
 modes=c.read(small/'G46_OPERATOR_ORACLE.json')['modes']
 reject('unconstrained_rigid_candidate',lambda:oracle.exact_gauge_admission(modes[0]),'GAUGE_UNCONSTRAINED_MODE')
 reject('non_null_gauge_perturbation',lambda:oracle.exact_gauge_admission(modes[6]),'GAUGE_NON_NULL_MODE')
 x={'C_defect':0.,'H_defect':0.,'operator_relative':0.,'divergence_operator_relative':0.,'energy_relative':0.,'forcing_compatibility_relative':1e-5}
 reject('incompatible_forcing_exact_oracle_fixture',lambda:oracle.exact_gauge_admission(x),'GAUGE_INCOMPATIBLE_FORCING');rows[-1]['scope']='algebraic exact-mode oracle fixture, not native physical kernel certification'
 p=overlay('broken_H',coarse);f=p/'output/G46_s0_r0_H.dat';lines=f.read_text().splitlines();j=next(i for i,s in enumerate(lines) if float(s.split()[1])>=0);v=lines[j].split();v[2]=str(float(v[2])+.2);lines[j]=' '.join(v);replace(f,'\n'.join(lines)+'\n');reject('broken_H',lambda:oracle.load(p),'H_PARTITION_OF_UNITY')
 p=overlay('broken_C',coarse);f=p/'output/G46_s0_r0_C.dat';lines=f.read_text().splitlines();j=next(i for i,s in enumerate(lines) if float(s.split()[1])>=0);v=lines[j].split();v[2]=str(float(v[2])+.2);lines[j]=' '.join(v);replace(f,'\n'.join(lines)+'\n');reject('broken_C',lambda:oracle.load(p),'EXPORTED_C_MODE_VIOLATION')
 p=overlay('omitted_MPI_contribution',mpi);f=p/'output/G46_s0_r0_ACTION.dat';v=np.loadtxt(f,ndmin=2);v[:,3:]=0.;replace(f,'\n'.join(' '.join(format(x,'.17g') for x in row) for row in v)+'\n');reject('omitted_MPI_contribution',lambda:oracle.load(p),'OMITTED_OR_WRONG_OPERATOR_CONTRIBUTION')
 p=overlay('rank_ID_mismatch',mpi);f=p/'output/G46_s0_r0_SUMMARY.dat';v=f.read_text().split();v[0]='3';replace(f,' '.join(v)+'\n');reject('rank_ID_mismatch',lambda:oracle.load(p),'RANK_IDENTITY')
 for kind in ['wrong_sign','nonconstant_shift','mismatched_quadrature','dropped_face']:
  p=overlay('datum_'+kind,coarse)
  if kind=='wrong_sign':
   f=p/'output/G46_s0_r0_PV3.dat';v=np.loadtxt(f,ndmin=2);v[:,1]*=-1;replace(f,'\n'.join(f'{int(a)} {b:.17g}' for a,b in v)+'\n')
  elif kind=='nonconstant_shift':
   f=p/'CASE_SPEC.json';spec=c.read(f);spec['pressure_increment_expression']='10+x';f.write_text(json.dumps(spec))
  elif kind=='mismatched_quadrature':
   f=p/'output/G46_s0_r0_PV3.dat';replace(f,(p/'output/G46_s0_r0_PV7.dat').read_text())
  else:
   f=p/'output/G45_s0_r0_FACES.dat';replace(f,'\n'.join(f.read_text().splitlines()[1:])+'\n')
  if kind=='dropped_face':reject('datum_'+kind,lambda:audit.evaluate(p),'FACE_COVERAGE')
  else:
   def check():
    a,z,act,*_=oracle.load(p);datum.pressure_preflight(p,a[:,0].astype(int),act)
   reject('datum_'+kind,check,'DATUM_NONCONSTANT_SHIFT' if kind=='nonconstant_shift' else 'DATUM_NATIVE_PRESSURE_LOAD')
 for p in [coarse,mpi,small]:c.need(c.prior.old.g25.inventory(p/'output')==before[str(p)],'NEGATIVE_MUTATED_PARENT')
 c.write(out/'REPORT.json',{'screen_pass':all(x['screen_pass'] for x in rows),'tests':rows,'real_native_artifact_negatives':10,'algebraic_exact_null_compatibility_fixture':1,'all_source_outputs_byte_unchanged':True,**c.SCOPE})
if __name__=='__main__':main()
