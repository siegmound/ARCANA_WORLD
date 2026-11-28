#!/usr/bin/env python3
"""Seal measured G46 outcomes, preserving failures and all historical authority."""
import argparse,json,os,subprocess,csv,xml.etree.ElementTree as ET
from pathlib import Path
import arcana_g46_campaign as c

def guards():
 c.check();verified={}
 for d in [c.read(c.CODE/'contract.json')['parents'],{r['path']:r['manifest_sha256'] for r in c.read(c.CODE/'g15_corrected_executable_contract.json')['parents']}]:
  for name,pin in d.items():
   if name in verified:continue
   m=c.prior.old.g38.verified_bundle(c.EV/name,pin);verified[name]={'manifest_sha256':pin,'files':len(m['files'])};print('FINAL_PARENT_VERIFIED',name,flush=True)
 _,container,*_=c.prior.old.runtime();before=c.read(c.ROOT/'HISTORICAL_METADATA_BEFORE.json');after=c.prior.old.ar.tree_metadata(container);c.need(before==after,'HISTORICAL_RUNTIME_METADATA_CHANGED')
 runtime=c.read(c.ROOT/'RUNTIME_READONLY_IDENTITY.json');checks=[]
 for name,pin in runtime['binary_sha256'].items():c.need(c.sha(c.PARENT/'native_runtime/bin'/name)==pin,'READONLY_G45_RUNTIME_CHANGED');checks.append(name)
 protected=['arcana_g41_native_quadrature.py','arcana_g42_consistent_boundary_flux.py','arcana_hpc_supervisor.py']
 for name in protected:
  p=Path(__file__).with_name(name);old=subprocess.check_output(['git','show','03190254ff4843cbabd8dd7c8891cea291a67e27:experiments/r6_thermo_provider_pilot_v1/'+name]);c.need(p.read_bytes()==old,'PROTECTED_HELPER_CHANGED:'+name)
 old=subprocess.check_output(['git','show','03190254ff4843cbabd8dd7c8891cea291a67e27:experiments/r6_thermo_provider_pilot_v1/g45_distributed_cbf_v1/audit.py']);c.need((c.prior.CODE/'audit.py').read_bytes()==old,'G45_AUDIT_CHANGED')
 for file,pin in [('contract.json',c.PIN),('restart_realization_contract.json','e31767b6f33ac5f651bba622cddce766420b909654af40fd1a5fe5a0e71350cd'),('small_amr_instrumentation_contract.json','d3afb0d98ab2d8f9d6b74101538b3f0000097a444bab685f0c9a0d65e75f1efb'),('retained_norms_contract.json','61e8fb2a09c55a789307b4c3bd4f7f47906a57c426d86d89857c039009573501')]:c.need(c.sha(c.CODE/file)==pin,'G46_CONTRACT_CHANGED:'+file)
 seen=set();exits=[]
 for p in c.ROOT.rglob('RUN_EXIT.json'):
  row=c.read(p);c.need(not row['remaining'],'LIVE_PROCESS_REMAINS:'+str(p));exits.append({'case':str(p.parent.relative_to(c.ROOT)),'exit_code':row['exit_code']})
 for p in c.ROOT.rglob('PROCESS_SAMPLES.jsonl'):
  for line in p.open():
   for row in json.loads(line)['processes']:seen.add((row['pid'],row['starttime']))
 live=[]
 for pid,start in seen:
  try:
   s=Path('/proc',str(pid),'stat').read_text();s=s[s.rfind(')')+2:].split()
   if int(s[19])==start and s[0] not in ('Z','X'):live.append([pid,start])
  except (FileNotFoundError,ProcessLookupError):pass
 c.need(not live,'G46_OBSERVED_JOB_STILL_LIVE');c.prior.old.source_check()
 return {'screen_pass':True,'full_parent_inventory_verifications':verified,'historical_runtime_metadata_unchanged':True,'historical_metadata_entries':len(before),'G45_readonly_runtime_binary_checks':checks,'protected_G41_G42_supervisor_G45audit_unchanged':True,'frozen_SOURCE_clean':True,'SOURCE_sha':c.prior.old.g25.SOURCE,'all_contracts_unchanged':True,'observed_process_identities':len(seen),'observed_live_remaining':live,'supervised_exits':exits,**c.SCOPE}

def prepare():
 c.check();r=c.read(c.ROOT/'RESTART_QUALIFICATION_NEW01.json');c.need(r['status']=='PASS_NATIVE_SAME_AND_CHANGED_RANK_RESTART_ONLY','RESTART_NOT_QUALIFIED');c.need(c.read(c.ROOT/'RESTART_NATIVE_CONVERGENCE_FINAL.json')['screen_pass'],'NATIVE_RESTART_CONVERGENCE')
 for p in ['NEGATIVE_OPERATOR_DATUM_NEW01/REPORT.json','NEGATIVE_RESTART_NEW01/REPORT_ADJUDICATED_NEW01.json','FINAL_PRODUCTION_EXPORT_GATES.json']:c.need(c.read(c.ROOT/p)['screen_pass'],'FINAL_CHECK:'+p)
 test=ET.parse(c.ROOT/'FINAL_UNIT_TESTS.xml').getroot();suites=list(test) if test.tag=='testsuites' else [test];n=sum(int(x.attrib['tests']) for x in suites);c.need(n==17 and all(int(x.attrib.get('failures',0))==int(x.attrib.get('errors',0))==0 for x in suites),'FINAL_UNIT_TESTS')
 guard=guards();c.write(c.ROOT/'FINAL_GUARDS.json',guard)
 cases=[];runrows=[]
 for p in sorted(c.ROOT.glob('*/CASE_SPEC.json')):
  case=p.parent;s=c.read(p);run=c.read(case/'RUN_EXIT.json');times=[json.loads(l)['elapsed_s'] for l in (case/'PROCESS_SAMPLES.jsonl').open()];row={'case':case.name,'family':s['family'],'kind':s.get('kind','static'),'level':s['base_refinement'],'ranks':s['ranks'],'exit_code':run['exit_code'],'native_converged':c.read(case/'EXECUTION_REPORT.json')['screen_pass'],'peak_PSS_GiB':run['peak_aggregate_pss_observed_bytes']/2**30,'peak_RSS_GiB':run['peak_aggregate_rss_observed_bytes']/2**30,'wall_s':run['wall_s'],'max_sampling_gap_s':max((b-a for a,b in zip(times,times[1:])),default=0.)};cases.append(row)
 with (c.ROOT/'NUMERICAL_CAMPAIGN.csv').open('x',newline='') as f:
  w=csv.DictWriter(f,fieldnames=list(cases[0]));w.writeheader();w.writerows(cases)
 snap=c.ROOT/'COMMITTED_G46_CODE_SNAPSHOTS';snap.mkdir();commits=subprocess.check_output(['git','rev-list','--reverse','03190254ff4843cbabd8dd7c8891cea291a67e27..HEAD'],text=True).splitlines();ident={}
 for rev in commits:
  paths=subprocess.check_output(['git','ls-tree','-r','--name-only',rev,'experiments/r6_thermo_provider_pilot_v1','tests/test_g46_acceptance.py'],text=True).splitlines();items={}
  for path in paths:
   if 'g46' not in path.lower():continue
   raw=subprocess.check_output(['git','show',rev+':'+path]);dest=snap/rev/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);items[path]=c.sha(dest)
  ident[rev]=items
 c.write(c.ROOT/'COMMITTED_G46_CODE_IDENTITY.json',ident)
 c.write(c.ROOT/'EXECUTED_STAGE_PROVENANCE.json',{'preflight':'e693ebaf','initial_plugin_build_and_operator':'7d5344a0','AMR_diagnostic_driver':'9b8f51fa','restart_initial':'4d396d98','restart_setup_retry':'e94f6d07','successful_native_reference_first_same_rank':'0fe56c33','restart_rank_recovery':'7ef7aedc','decisive_small_AMR_flux_analytic':'fb62bb98','negative_restart_driver':'7d3696fc','negative_operator_driver':'5e6d6789','retained_norms_driver':'000413e1','note':'running Python modules remain those loaded at process start; on-disk hashes from later concurrent documentation commits do not establish loaded version. Build source copies, all committed revisions and stage attribution retained. Inherited supervisor CODE_IDENTITY names G45 helper/contract; G46_EXECUTED_IDENTITY binds actual G46 contract/input/plugin/runner; supervisor implementation unchanged.'})
 report={'status':'G46_SYNTHETIC_CAMPAIGN_COMPLETED_RESTART_PASS_GAUGE_DATUM_BLOCKED','completed_authorized_campaign':True,'all_gates_pass':False,'gates':{'retained_G45_diagnosis':'PASS_READONLY_WITH_NATIVE_VOLUME_NORM_COMPLETION','native_same_rank_restart':'PASS_BOUND_SYNTHETIC_CONFIGURATION','native_changed_rank_restart_1_to_2_4_8':'PASS_BOUND_SYNTHETIC_CONFIGURATION','exact_rotational_kernel':'BLOCKED_POSITIVE_DISCRETE_STRAIN_AND_NONZERO_OPERATOR_ACTION','near_null_saddle_gauge':'FAIL_ORIGINAL_MOMENTUM_RESIDUAL_THRESHOLD','original_net_rotation_AMR_convergence':'FAIL_RETAINED_HYDRO_AND_FORCED_CONTROLS','coarse_original_G45_pressure_datum':'FAIL_UNCHANGED_0.005_THRESHOLD','higher_order_cellwise_divergence_identity':'PASS_WITHIN_PREDECLARED_1e-10','AMR_internal_face_cancellation_under_H':'FAIL_HIGHER_ORDER_INTERNAL_FLUX_REMAINS','full_free_slip_velocity_rank_parity':'NOT_RECOVERED_G45_FAILURES_CONFIRMED_BY_RAW_VOLUME_NORM','new_free_slip_rank_fine_extension':'NOT_RUN_AFTER_FAILED_EXACT_KERNEL_GATE','analytic_prescribed_velocity_regression':'PASS_NATIVE_AND_G45_TRACE_AUDIT_WITH_AFFINE_LIFT_ADJUDICATION','negative_operator_datum_gates':'PASS_10_NATIVE_ARTIFACT_REJECTIONS_PLUS_1_ALGEBRAIC_FORCING_FIXTURE','negative_restart_gates':'PASS_3_NATIVE_REJECTIONS_PLUS_1_PRE_RUN_CLOCK_GUARD','G15_executable_contract_preflight':'PASS_DESIGN_ONLY_EXECUTION_NOT_AUTHORIZED','T0_decision_matrix':'READY_10_UNSELECTED_CHOICES_NO_ASSIGNMENTS'},'native_case_invocations':len(cases),'cases':cases,'focused_tests_passed':n,'runtime':'read-only verified G45 private native deployment, historic ASPECT unchanged; isolated new plugins only','main_contract_sha256':c.PIN,'restart':r,'near_null_saddle':c.read(c.ROOT/'NEAR_NULL_SADDLE_CANDIDATE_AMR.json'),'datum_geometry':c.read(c.ROOT/'DATUM_INTERIOR_GEOMETRY_ADJUDICATION.json'),'raw_retained_volume_norms':c.read(c.ROOT/'RETAINED_RAW_FIELD_VOLUME_NORMS.json'),'negative_operator_datum':c.read(c.ROOT/'NEGATIVE_OPERATOR_DATUM_NEW01/REPORT.json'),'negative_restart':c.read(c.ROOT/'NEGATIVE_RESTART_NEW01/REPORT_ADJUDICATED_NEW01.json'),'G15_contract_preflight':c.read(c.ROOT/'G15_CONTRACT_PREFLIGHT.json'),'code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_sha':c.prior.old.g25.SOURCE,'publication_plan':'separate GitHub evidence/g46-20261128-new01 LFS branch, complete materialized archive and manifest; final delivery receipt outside sealed root binds actual commit','limits':['synthetic Q2 incompressible shells; no compressible or physical mantle qualification','small velocity-strain spectra, not asserted complete saddle singular spectra on fine meshes','live state admissibility alone does not uniquely identify nonlinear failure; original native interpolation already distributes hanging-node constraints','native copy-of-final-state rotation diagnostic is not a captured pre/post history of every internal Stokes correction','near-null saddle is independent sparse oracle with explicitly separate pressure-mean auxiliary row; no changed native provider deployed','high-order quadrature diagnostics do not alter native operator or substitute original datum screen','restart two native clock increments include initialization advance; only one actual nonzero transport solve at.001s, serialized.002s; no mature BDF2 or global physical history claim','same-rank histories exact; changed-rank all fields/integrals compared within scope; raw checkpoint bytes need not match across partitions','sampled PSS guard is not kernel hard limit, may miss short peaks; RSS includes shared pages; bounded offline coordinator outside native guard','G15 executable proposal validator implemented; future corrected T0 mechanical initialization/trajectory adapter and separate author authorization remain required','all ten author choices/assigned T0 values remain null; M01 not selected or executed','failures and partial JSON retained; later adjudications never overwrite old verdicts'],**c.SCOPE}
 c.write(c.ROOT/'REPORT.json',report);c.write(c.ROOT/'HARDWARE_AFTER.json',c.prior.old.g44.host());print('G46_PREPARED',len(cases),'native invocations',n,'tests',flush=True)

def seal():
 report=c.read(c.ROOT/'REPORT.json');c.need(report['completed_authorized_campaign'],'INCOMPLETE_REPORT');files={};links={};cache={}
 for p in sorted(c.ROOT.rglob('*')):
  if p==c.ROOT/'MANIFEST.json':continue
  rel=str(p.relative_to(c.ROOT))
  if p.is_symlink():links[rel]=os.readlink(p)
  if p.is_file():
   st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
   if key not in cache:cache[key]=c.sha(p)
   files[rel]=cache[key]
 c.write(c.ROOT/'MANIFEST.json',{'status':report['status'],'source_sha':c.prior.old.g25.SOURCE,'report_sha256':c.sha(c.ROOT/'REPORT.json'),'files':files,'symlink_targets':links,**c.SCOPE});print('G46_SEALED',c.sha(c.ROOT/'MANIFEST.json'),len(files),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','seal']);a=p.parse_args();(prepare if a.action=='prepare' else seal)()
