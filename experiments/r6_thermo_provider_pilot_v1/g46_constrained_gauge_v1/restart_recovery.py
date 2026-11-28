"""Finish restart qualification using already successful native runs, no duplication."""
import sys,re,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
sys.path.insert(0,str(c.CODE));import restart as r

def main():
 c.check();ref=c.ROOT/'restart_reference_p1_NEW03';first=c.ROOT/'restart_first_p1_NEW03';same=c.ROOT/'restart_resume_p1_NEW03';results=[];fail=[]
 for p in [ref,first,same]:
  ident=c.read(p/'G46_EXECUTED_IDENTITY.json');c.need(c.sha(p/'input.prm')==ident['input_sha256'] and ident['G46_contract_sha256']==c.PIN,'RECOVERY_NATIVE_INPUT_DRIFT');c.need(c.read(p/'RESTART_NATIVE_GATE.json')['screen_pass'] and c.read(p/'RUN_EXIT.json')['exit_code']==0,'RECOVERY_NATIVE_GATE')
 c.need(c.sha(c.CODE/'restart_realization_contract.json')==r.REALIZATION_PIN,'RESTART_REALIZATION')
 inv=c.prior.old.g25.inventory(first/'output/restart');r.clock_gate(c.read(first/'CHECKPOINT_LINEAGE.json'),inv)
 result=r.compare(ref,same);c.write(same/'RESTART_COMPARISON_NEW02.json',result);results.append(result);print('G46_RESTART_REUSED_P1',result['screen_pass'],max(result['fields_relative'].values()),flush=True)
 plugin=c.ROOT/'plugin_build_NEW04/build/libarcana_g46.release.so'
 for n in [2,4,8]:
  case=None
  try:
   r.clock_gate(c.read(first/'CHECKPOINT_LINEAGE.json'),c.prior.old.g25.inventory(first/'output/restart'))
   label=f'restart_resume_p{n}_NEW03';case,row=c.execute(label,{'name':label,'family':'analytic','kind':'restart','base_refinement':2,'adaptive_cycles':0,'ranks':n,'synthetic_positive_time_only':True,'stop_s':.002,'max_accepted_native_clock_increments':2},plugin,text=r.prm(True),extra_env={'ARCANA_G46_STOP_TIME':'.002'},checkpoint=first/'output')
   c.need(row['screen_pass'],'RESTART_NATIVE_EXIT');text=(case/'STDOUT.txt').read_text();c.need(not re.search(r'WARNING:.*solver failures occurred',text),'RESTART_NATIVE_WARNING');clocks=re.findall(r'\*\*\* Timestep (\d+):\s*t=([\d.eE+-]+)',text);c.need(clocks==[('1','0.001')],'RESTART_NEXT_STEP_CLOCK')
   result=r.compare(ref,case);c.write(case/'RESTART_COMPARISON.json',result);results.append(result);print('G46_RESTART_CHANGED_RANK',n,result['screen_pass'],max(result['fields_relative'].values()),flush=True)
  except Exception as e:
   fail.append({'ranks':n,'case':case.name if case else None,'error':repr(e),'traceback':traceback.format_exc()});print('G46_RESTART_RETAINED_FAIL',n,repr(e),flush=True)
 k,a,s=r.load(ref);k0,b,s0=r.load(first,step=1);c.need(k==k0,'RESTART_INITIAL_FINAL_IDENTITY');import numpy as np
 change={str(comp):float(np.linalg.norm(a[a[:,0]==comp,1]-b[b[:,0]==comp,1])) for comp in [4,5]};nontrivial=all(x>1e-10 for x in change.values())
 report={'status':'PASS_NATIVE_SAME_AND_CHANGED_RANK_RESTART_ONLY' if len(results)==4 and all(x['screen_pass'] for x in results) and not fail and nontrivial else 'BLOCKED_OR_FAILED_NATIVE_RESTART','results':results,'failed_branches':fail,'nontrivial_field_change':change,'max_accepted_native_clock_increments_per_lineage':2,'serialized_clock_s':.002,'last_computed_transport_field_time_s':.001,'reused_native_runs':[ref.name,first.name,same.name],'recovery':'only NumPy bool JSON receipt conversion; failed partial JSON preserved; no repeated successful native solve','restart_parent_inventory_unchanged':c.prior.old.g25.inventory(first/'output/restart')==inv,**c.SCOPE};c.write(c.ROOT/'RESTART_QUALIFICATION_NEW01.json',report)
if __name__=='__main__':main()
