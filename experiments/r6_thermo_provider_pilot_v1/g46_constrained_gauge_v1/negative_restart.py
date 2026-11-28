"""Actual native restart failures plus production pre-run clock rejection."""
import sys,shutil,re,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]));import arcana_g46_campaign as c
sys.path.insert(0,str(c.CODE));import restart as r

def main():
 c.check();first=c.ROOT/'restart_first_p1_NEW03';inv=c.prior.old.g25.inventory(first/'output/restart');out=c.ROOT/'NEGATIVE_RESTART_NEW01';out.mkdir();rows=[];plugin=c.ROOT/'plugin_build_NEW04/build/libarcana_g46.release.so'
 for kind in ['missing_checkpoint','corrupted_checkpoint','incompatible_fields']:
  parent=None;text=r.prm(True)
  if kind!='missing_checkpoint':
   parent=out/(kind+'_source_output');parent.mkdir();shutil.copytree(first/'output/restart',parent/'restart')
  if kind=='corrupted_checkpoint':
   files=list((parent/'restart').rglob('resume.z'));c.need(len(files)==1,'CORRUPTION_SINGLE_CHECKPOINT');files[0].write_bytes(b'G46 intentionally corrupted compressed checkpoint\n')
  if kind=='incompatible_fields':
   text=text.replace('set Number of fields = 1','set Number of fields = 2').replace('set Names of fields = synthetic_marker','set Names of fields = synthetic_marker, incompatible_marker').replace('set Function expression = 0.5+0.1*x*y+0.05*z','set Function expression = 0.5+0.1*x*y+0.05*z; 0.25')
  label='negative_restart_'+kind+'_NEW01';case,run=c.execute(label,{'name':label,'family':'analytic','kind':'restart_negative','base_refinement':2,'adaptive_cycles':0,'ranks':1,'max_accepted_native_clock_increments':2,'expected_failure':kind},plugin,text=text,extra_env={'ARCANA_G46_STOP_TIME':'.002'},checkpoint=parent)
  err=(case/'STDERR.txt').read_text();stdout=(case/'STDOUT.txt').read_text();expected={'missing_checkpoint':'no matching written checkpoint','corrupted_checkpoint':'decompress','incompatible_fields':'number of compositional fields'}[kind]
  match=expected.lower() in err.lower()
  if kind=='incompatible_fields':match=match or ('load_and_check_critical_parameters' in err and 'use_discontinuous_composition_discretization ==' in ' '.join(err.split()))
  if kind=='corrupted_checkpoint':match=match or any(x in err.lower() for x in ['uncompress','deserialize','zlib','compressed','corrupt'])
  no_step=not re.search(r'\*\*\* Timestep\s+\d+',stdout)
  row={'name':kind,'case':case.name,'native_exit':run['exit_code'],'expected_native_diagnostic_found':match,'no_accepted_time_step':no_step,'screen_pass':bool(run['exit_code']!=0 and match and no_step)};rows.append(row);print('NEGATIVE_RESTART',kind,row['screen_pass'],flush=True)
 bad=dict(c.read(first/'CHECKPOINT_LINEAGE.json'),serialized_time_s=.002)
 try:r.clock_gate(bad,inv);rejected=False;error=None
 except RuntimeError as e:rejected='RESTART_CLOCK' in str(e);error=str(e)
 rows.append({'name':'inconsistent_clock','gate':'production pre-run lineage receipt, not native checkpoint reader','native_run':False,'error':error,'screen_pass':rejected})
 c.need(c.prior.old.g25.inventory(first/'output/restart')==inv,'NEGATIVE_MUTATED_RESTART_PARENT')
 report={'screen_pass':all(x['screen_pass'] for x in rows),'tests':rows,'baseline_checkpoint_unchanged':True,'negative_native_time_increments':0,**c.SCOPE};c.write(out/'REPORT.json',report)
if __name__=='__main__':main()
