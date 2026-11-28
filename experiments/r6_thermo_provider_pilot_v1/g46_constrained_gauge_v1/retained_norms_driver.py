"""Stage G45 immutable raw fields, integrate on actual native mapping once per mesh."""
import sys,re
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
PIN='61e8fb2a09c55a789307b4c3bd4f7f47906a57c426d86d89857c039009573501'

def main():
 c.check();c.need(c.sha(c.CODE/'retained_norms_contract.json')==PIN and c.sha(c.ROOT/'FROZEN_RETAINED_NORMS_CONTRACT.json')==PIN,'NORMS_CONTRACT')
 results=[]
 for spec in c.read(c.CODE/'retained_norms_contract.json')['cases']:
  level=spec['base_refinement'];cache={};source=[];keys=None
  def field(family,n):
   nonlocal keys
   name=f'G45R1_{family}_l{level}_a1_p{n}_unremoved_NEW01';p=c.PARENT/name/'G45R1_FIELDS.json';d=c.read(p)
   if keys is None:keys=d['keys']
   c.need(keys==d['keys'],'NORMS_CROSS_RANK_STABLE_IDENTITIES');source.append({'case':name,'file':str(p),'sha256':c.sha(p)});return np.array(d['values'])[:,0]
  forced=field('forced',1);data=[forced,field('forced',4 if level==2 else 8)-forced];d1=field('datum',1);data.append(d1)
  if level==2:data.append(d1-forced)
  else:
   d4=field('datum',4);data.extend([d4-d1,d4-field('forced',4)])
  c.need(len(data)==len(spec['fields']),'NORM_FIELD_SCHEMA');data=np.column_stack(data);staged=c.ROOT/f'RETAINED_FIELDS_L{level}_NEW01.dat'
  with staged.open('x') as f:
   f.write(f'{len(keys)} {data.shape[1]}\n')
   for key,row in zip(keys,data):f.write(key+' '+' '.join(format(x,'.17g') for x in row)+'\n')
  c.write(c.ROOT/f'RETAINED_FIELDS_L{level}_IDENTITY.json',{'sha256':c.sha(staged),'contract_sha256':PIN,'fields':spec['fields'],'sources':source,'stable_dofs':len(keys),'all_differences_raw_no_fitting':True})
  text=c.prior.prm_for(spec).replace('./libarcana_g45.so','./libarcana_g45.so, ./libarcana_g46.so').replace('set Remove nullspace = net rotation','set Remove nullspace = ')
  text=re.sub(r'(?m)^(\s*set List of postprocessors\s*=).*$',r'\1 velocity statistics, pressure statistics, viscous dissipation statistics, arcana g46 retained norms',text)
  case,run=c.execute(spec['name'],spec,c.ROOT/'retained_norms_plugin_NEW01/build/libarcana_g46.release.so',text=text,extra_env={'ARCANA_G46_RETAINED_FIELDS':str(staged)})
  c.need(run['screen_pass'],'NORMS_NATIVE_FAILURE');a=np.loadtxt(case/'output/G46_RETAINED_NORMS.dat',ndmin=2);c.need(a.shape==(len(spec['fields']),10) and np.isfinite(a).all(),'NORMS_RESULT_SCHEMA')
  rows=[]
  for name,row in zip(spec['fields'],a):rows.append({'field':name,'C_defect':float(row[1]),'H_defect':float(row[2]),'volume_mass_L2':float(np.sqrt(max(row[3],0.))),'strain_energy':float(row[4]),'divergence_L2':float(np.sqrt(max(row[5],0.))),'angular_momentum':row[6:9].tolist(),'surface_normal_L2_Gauss5':float(np.sqrt(max(row[9],0.)))})
  ratios={'raw_forced_rank_volume_relative':rows[1]['volume_mass_L2']/rows[0]['volume_mass_L2']}
  if level==3:ratios['raw_datum_rank_volume_relative']=rows[3]['volume_mass_L2']/rows[2]['volume_mass_L2']
  result={'case':case.name,'level':level,'fields':rows,'volume_ratios':ratios,'norms_are_diagnostics_not_substitution_for_frozen_historical_gate':True,'source_data_sha256':c.sha(staged),**c.SCOPE};c.write(case/'RETAINED_NORMS_REPORT.json',result);results.append(result);print('RAW_VOLUME_NORMS',level,ratios,flush=True)
 c.write(c.ROOT/'RETAINED_RAW_FIELD_VOLUME_NORMS.json',{'cases':results,'no_corrected_or_quotient_velocity_used':True,'same_equations_RHS_BC_tolerances':True,**c.SCOPE})
if __name__=='__main__':main()
