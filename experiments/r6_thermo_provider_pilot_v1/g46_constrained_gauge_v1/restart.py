"""Actual native checkpoint/resume, two clock increments per synthetic lineage."""
import sys,re,json,hashlib,shutil
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
REALIZATION_PIN='e31767b6f33ac5f651bba622cddce766420b909654af40fd1a5fe5a0e71350cd'

def prm(resume=False):
 s={'family':'analytic','base_refinement':2,'adaptive_cycles':0,'ranks':1}
 text=c.prior.prm_for(s).replace('./libarcana_g45.so','./libarcana_g45.so, ./libarcana_g46.so')
 text=re.sub(r'(?m)^(set End time\s*=).*$',r'\1 0.002',text)
 text=re.sub(r'(?m)^(set Nonlinear solver scheme\s*=).*$',r'\1 single Advection, iterated Stokes',text)
 text=text.replace('set Model name = HollowSphereMaterial','set Model name = arcana g46 thermal hollow')
 text=re.sub(r'(?m)^(\s*set List of postprocessors\s*=).*$',r'\1 velocity statistics, temperature statistics, composition statistics, pressure statistics, viscous dissipation statistics, arcana g46 restart state',text)
 text=text.replace('set Linear solver tolerance = 1e-6','set Linear solver tolerance = 1e-7')
 return text+'''
set Resume computation = RESUME
set Maximum time step = 0.001
set Nonlinear solver tolerance = 1e-6
subsection Time stepping
 set List of model names = function
 subsection Function
  set Function expression = 0.001
 end
end
subsection Termination criteria
 set Termination criteria = end time, arcana g46 bound
end
subsection Checkpointing
 set Steps between checkpoint = 1
 set Number of checkpoints to keep = 2
end
subsection Initial temperature model
 set List of model names = function
 subsection Function
  set Coordinate system = cartesian
  set Function expression = 1000+20*x*y+10*z
 end
end
subsection Compositional fields
 set Number of fields = 1
 set Names of fields = synthetic_marker
end
subsection Initial composition model
 set List of model names = function
 subsection Function
  set Coordinate system = cartesian
  set Function expression = 0.5+0.1*x*y+0.05*z
 end
end
subsection Heating model
 set List of model names =
end
'''.replace('RESUME','true' if resume else 'false')

def clock_gate(receipt,expected_inventory):
 c.need(receipt['contract_sha256']==c.PIN and receipt['realization_sha256']==REALIZATION_PIN,'RESTART_SCHEMA')
 c.need(receipt['accepted_native_clock_increments']==1 and receipt['serialized_time_s']==.001 and receipt['next_step_s']==.001,'RESTART_CLOCK')
 c.need(receipt['files']==expected_inventory,'RESTART_INVENTORY')

def load(case,kind='checkpoint',step=2):
 n=c.read(case/'CASE_SPEC.json')['ranks'];states=[];keys={};summ=[]
 for rank in range(n):
  p=case/'output'/f'G46R_{kind}_s{step}_r{rank}';d=np.loadtxt(str(p)+'_STATE.dat',ndmin=2);states.append(d);summ.append(np.loadtxt(str(p)+'_SUMMARY.dat',ndmin=2)[0])
  for line in Path(str(p)+'_BASIS.dat').read_text().splitlines():
   cell,basis,idx,comp=line.split();idx=int(idx);key=cell+'/'+basis+'/'+comp;keys[idx]=min(keys.get(idx,key),key)
 d=np.vstack(states);c.need(len(set(d[:,0]))==len(d),'RESTART_OWNERSHIP');lookup={int(row[0]):row for row in d};c.need(set(keys)==set(lookup),'RESTART_DOF_COVERAGE');order=sorted(keys,key=keys.get)
 return [keys[i] for i in order],np.array([lookup[i][1:] for i in order]),np.vstack(summ)

def compare(ref,case):
 ka,a,sa=load(ref);kb,b,sb=load(case);c.need(ka==kb and np.array_equal(a[:,0],b[:,0]),'RESTART_STABLE_IDENTITY')
 c.need(np.all(sa[:,1]==.002) and np.all(sb[:,1]==.002) and np.all(sb[:,2]==2),'RESTART_FINAL_CLOCK')
 fields={}
 for comp in sorted(set(a[:,0].astype(int))):
  mask=a[:,0]==comp
  for j,name in enumerate(['current','old','old_old'],1):fields[f'component{comp}_{name}']=float(np.linalg.norm(a[mask,j]-b[mask,j])/max(np.linalg.norm(a[mask,j]),1.))
 integ=sa[:,5:].sum(axis=0);other=sb[:,5:].sum(axis=0);delta=(abs(integ-other)/np.maximum(abs(integ),1.));limit=1e-8 if len(sb)==1 else 1e-4
 return {'reference':ref.name,'case':case.name,'fields_relative':fields,'integrals_relative':delta.tolist(),'serialized_clock_s':.002,'next_pending_step_not_executed':True,'field_limit':limit,'screen_pass':max(fields.values())<=limit and max(delta)<=1e-8,'rank_count':len(sb)}

def run(suffix='NEW02'):
 c.check();c.need(c.sha(c.CODE/'restart_realization_contract.json')==REALIZATION_PIN and c.sha(c.ROOT/'FROZEN_RESTART_REALIZATION_CONTRACT.json')==REALIZATION_PIN,'RESTART_REALIZATION_DRIFT')
 plugin=c.ROOT/'plugin_build_NEW03/build/libarcana_g46.release.so';attempt=[]
 def execute(label,n,stop,resume=False,checkpoint=None):
  case,row=c.execute(label,{'name':label,'family':'analytic','kind':'restart','base_refinement':2,'adaptive_cycles':0,'ranks':n,'synthetic_positive_time_only':True,'stop_s':stop,'max_accepted_native_clock_increments':2},plugin,text=prm(resume),extra_env={'ARCANA_G46_STOP_TIME':str(stop)},checkpoint=checkpoint)
  attempt.append({'case':case.name,'exit_code':row['exit_code']})
  c.need(row['screen_pass'],'RESTART_NATIVE_EXIT:'+case.name)
  text=(case/'STDOUT.txt').read_text();c.need(not re.search(r'WARNING:.*solver failures occurred',text),'RESTART_NATIVE_CONVERGENCE_WARNING')
  clocks=re.findall(r'\*\*\* Timestep (\d+):\s*t=([\d.eE+-]+)',text);c.need(clocks and max(int(i) for i,t in clocks)<=1 and max(float(t) for i,t in clocks)<=.001+1e-14,'RESTART_ACCEPTED_STEP_BUDGET')
  c.write(case/'RESTART_NATIVE_GATE.json',{'screen_pass':True,'solve_clocks':clocks,'stop_s':stop,'accepted_clock_cap':2,**c.SCOPE});return case
 try:
  ref=execute('restart_reference_p1_'+suffix,1,.002)
  first=execute('restart_first_p1_'+suffix,1,.001)
  _,_,sumfirst=load(first,step=1);c.need(np.all(sumfirst[:,1]==.001),'CHECKPOINT_FIRST_CLOCK')
  inv=c.prior.old.g25.inventory(first/'output/restart');receipt={'contract_sha256':c.PIN,'realization_sha256':REALIZATION_PIN,'serialized_time_s':.001,'next_step_s':.001,'accepted_native_clock_increments':1,'files':inv};c.write(first/'CHECKPOINT_LINEAGE.json',receipt);clock_gate(receipt,inv)
  results=[]
  for n in [1,2,4,8]:
   clock_gate(c.read(first/'CHECKPOINT_LINEAGE.json'),c.prior.old.g25.inventory(first/'output/restart'))
   case=execute(f'restart_resume_p{n}_'+suffix,n,.002,True,first/'output');result=compare(ref,case);c.write(case/'RESTART_COMPARISON.json',result);results.append(result);print('G46_RESTART',n,result['screen_pass'],max(result['fields_relative'].values()),flush=True)
  # A genuine state change excludes a vacuous state-only restart test.
  k,a,s=load(ref);k0,b,s0=load(first,step=1);c.need(k==k0,'FIRST_FINAL_SUPPORT');change={str(comp):float(np.linalg.norm(a[a[:,0]==comp,1]-b[b[:,0]==comp,1])) for comp in [4,5]};c.need(all(v>1e-10 for v in change.values()),'VACUOUS_THERMAL_OR_COMPOSITION_RESTART')
  report={'status':'PASS_NATIVE_RESTART_ONLY' if all(r['screen_pass'] for r in results) else 'FAIL_NATIVE_RESTART_COMPARISON','results':results,'attempts':attempt,'nontrivial_field_change':change,'accepted_native_clock_increments_per_lineage':2,'serialized_clock_s':.002,'last_computed_transport_field_time_s':.001,'synthetic_only':True,**c.SCOPE}
 except Exception as e:
  import traceback
  report={'status':'BLOCKED_NATIVE_RESTART','attempts':attempt,'error':repr(e),'traceback':traceback.format_exc(),**c.SCOPE};print(report['traceback'],flush=True)
 c.write(c.ROOT/('RESTART_PHASE_REPORT_'+suffix+'.json'),report)
if __name__=='__main__':run()
