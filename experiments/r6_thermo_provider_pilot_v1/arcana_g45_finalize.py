#!/usr/bin/env python3
"""Append-only closure of exactly evidenced G45 gates; never force ALL_PASS."""
import argparse
import csv
import json
import os
from pathlib import Path
import subprocess
import arcana_g45_distributed_amr_cbf as c
import arcana_native_runtime_candidate as native


def guards():
    c.check();_,container,root,*_=c.old.runtime();before=c.read(c.ROOT/'CONTAINER_METADATA_BEFORE.json');after=c.old.ar.tree_metadata(container)
    c.need(after==before,'HISTORICAL_RUNTIME_METADATA_DRIFT')
    parents=c.read(c.ROOT/'PARENT_PREFLIGHT.json')['parents'];verified=[]
    for row in parents:
        m=c.old.g38.verified_bundle(c.EV/row['path'],row['manifest_sha256']);verified.append({**row,'members':len(m['files']),'final_complete_inventory_verified':True})
    authority=c.read(c.ROOT/'T0_G15_AUTHORITY_INVENTORY.json')
    for row in authority['documentary_parent_inventories']:
        if row.get('complete_inventory_verified'):c.old.g38.verified_bundle(Path(row['path']),row['manifest_sha256'])
    sourcefiles=[]
    for name,identity in authority['source_files'].items():
        if 'sha256' in identity:c.need(c.sha(Path(name))==identity['sha256'],'DOCUMENTARY_SOURCE_CHANGED:'+name);sourcefiles.append(name)
    for name in ('arcana_g41_native_quadrature.py','arcana_g42_consistent_boundary_flux.py','arcana_hpc_supervisor.py'):
        p=Path(__file__).with_name(name);original=subprocess.check_output(['git','show','2ff7f77a92365dd955d48fcdacfa8ee14d5d168a:experiments/r6_thermo_provider_pilot_v1/'+name]);c.need(p.read_bytes()==original,'PROTECTED_HELPER_CHANGED:'+name)
    identity=c.read(c.ROOT/'NATIVE_RUNTIME_BUILD.json');binary=[]
    for name,row in identity['binary_identity'].items():
        p=c.ROOT/'native_runtime/bin'/name;source=Path(row['source']);c.need(c.sha(source)==row['source_sha256'] and c.sha(p)==row['private_sha256'] and native.text_sha(p)==row['text_sha256'],'NATIVE_RUNTIME_IDENTITY');binary.append(name)
    observed=set();exits=[]
    for p in c.ROOT.rglob('RUN_EXIT.json'):
        row=c.read(p);c.need(not row['remaining'],'LIVE_REMAINS:'+str(p));exits.append({'case':str(p.parent.relative_to(c.ROOT)),'exit_code':row['exit_code']})
        for q in row.get('per_process_peak_pss_samples',{}).values():observed.add((q['pid'],q['starttime']))
    for p in c.ROOT.rglob('PROCESS_SAMPLES.jsonl'):
        for line in p.open():
            for row in json.loads(line)['processes']:observed.add((row['pid'],row['starttime']))
    live=[]
    for pid,start in observed:
        try:
            raw=Path('/proc',str(pid),'stat').read_text();fields=raw[raw.rfind(')')+2:].split()
            if int(fields[19])==start and fields[0] not in ('Z','X'):live.append({'pid':pid,'starttime':start})
        except (FileNotFoundError,ProcessLookupError):pass
    c.need(not live,'OBSERVED_JOB_STILL_LIVE')
    return {'screen_pass':True,'parents':verified,'documentary_sources_unchanged':sourcefiles,'historical_runtime_metadata_equal':True,'historical_metadata_entries':len(before),'protected_helpers_unchanged':True,'private_binary_identities_unchanged':binary,'source_sha':c.old.g25.SOURCE,'frozen_source_clean':True,'execution_exits':exits,'observed_process_identities_checked':len(observed),'observed_live_remaining':live,**c.SCOPE}


def snapshots():
    out=c.ROOT/'COMMITTED_CODE_SNAPSHOTS';out.mkdir();base='experiments/r6_thermo_provider_pilot_v1/';rows={}
    commits=subprocess.check_output(['git','rev-list','--reverse','2ff7f77a92365dd955d48fcdacfa8ee14d5d168a..HEAD'],text=True).splitlines()
    for commit in commits:
        folder=out/commit;folder.mkdir();items={}
        paths=subprocess.check_output(['git','ls-tree','-r','--name-only',commit,base],text=True).splitlines()
        for name in paths:
            rel=name[len(base):]
            if not(rel.startswith('g45_distributed_cbf_v1/') or rel.startswith('arcana_g45') or rel=='arcana_hpc_supervisor.py'):continue
            raw=subprocess.check_output(['git','show',commit+':'+name]);dest=folder/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);items[rel]=c.sha(dest)
        rows[commit]=items
    c.write(c.ROOT/'COMMITTED_CODE_IDENTITY.json',rows)
    c.write(c.ROOT/'EXECUTED_STAGE_PROVENANCE.json',{'uniform_initial':'eef292b4','uniform_recovery':'24d46d5c','AMR_initial':'8aaebfb6','AMR_enable_recovery':'63a8fe53','G45R1_recovery':c.read(c.ROOT/'GAUGE_R1_RECOVERY_CODE_IDENTITY.json'),'G45R1_driver_loaded_at':'863c94e0','G45R1_audit_loaded_at':'863c94e0','G45R1_datum_projection_readjudication':'audit.py later pinned commit; original raw-pointwise diagnostic retained','compiled_plugin':'plugin_build_NEW02/PLUGIN_IDENTITY.json','notes':'Python modules remain those loaded at process start even if unrelated code commits occur; snapshots preserve stage revisions'})


def prepare():
    uniform=c.read(c.ROOT/'UNIFORM_PHASE_REPORT.json');adaptive=c.read(c.ROOT/'GAUGE_R1_PHASE_REPORT.json');neg=c.read(c.ROOT/'NEGATIVE_TESTS_NEW01/REPORT.json');restart=c.read(c.ROOT/'RESTART_GATE.json')
    c.need(uniform['execution_and_algebra_pass'] and uniform['equilibrium_pass'] and adaptive['completed_matrix'] and adaptive['execution_and_trace_algebra_pass'] and neg['screen_pass'],'FINAL_PHASE_GATE')
    snapshots();guard=guards();c.write(c.ROOT/'FINAL_GUARDS.json',guard);c.write(c.ROOT/'HARDWARE_AFTER.json',c.old.g44.host())
    rows=[];fields=['case','variant','cells','velocity_dofs','boundary_hanging_dofs','trace_dofs','native_converged','last_native_residual','native_cbf_relative','trace_sparse_solve_relative','virtual_adjoint_relative','native_force_relative','constrained_force_relative','constrained_moment_relative','PSS_GiB','RSS_GiB','wall_s','sample_gap_max_s']
    for case in sorted(c.ROOT.glob('*/CASE_SPEC.json')):
        folder=case.parent;spec=c.read(case);run=folder/'RUN_EXIT.json'
        if not run.exists():continue
        execution=c.read(run);row={'case':folder.name,'variant':c.read(folder/'CASE_VARIANT.json')['gauge_variant'] if (folder/'CASE_VARIANT.json').exists() else 'original','PSS_GiB':execution['peak_aggregate_pss_observed_bytes']/2**30,'RSS_GiB':execution['peak_aggregate_rss_observed_bytes']/2**30,'wall_s':execution['wall_s'],'exit_code':execution['exit_code'],'spec':spec}
        times=[json.loads(line)['elapsed_s'] for line in (folder/'PROCESS_SAMPLES.jsonl').open()];row['sample_gap_max_s']=max((b-a for a,b in zip(times,times[1:])),default=0.)
        if execution['exit_code']==0:
            conv=c.native_convergence(folder);row.update(native_converged=conv['screen_pass'],last_native_residual=conv['last_residual'])
        for name in ('G45R1_AUDIT_REPORT.json','AUDIT_V2_REPORT.json','AUDIT_REPORT.json','INTERRUPTED_CONTROLLER_AUDIT_RECOVERY.json'):
            p=folder/name
            if p.exists():
                audit=c.read(p);audit=audit.get('audit',audit)
                row.update(cells=audit['cells'],velocity_dofs=audit['velocity_dofs'],boundary_hanging_dofs=audit['boundary_hanging_nodes'],trace_dofs=audit['trace_dofs'],native_cbf_relative=audit['native_face_relative'],trace_sparse_solve_relative=audit['trace_independent_solve_relative'],virtual_adjoint_relative=audit['adjoint_random_virtual_relative'],native_force_relative=audit['reactions']['native']['force_balance_relative'],constrained_force_relative=audit['reactions']['constrained']['force_balance_relative'],constrained_moment_relative=audit['reactions']['constrained']['moment_balance_relative']);break
        rows.append(row)
    with (c.ROOT/'NUMERICAL_CAMPAIGN.csv').open('x',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    original=c.read(c.ROOT/'ORIGINAL_AMR_NATIVE_ADJUDICATION.json')
    report={'status':'G45_SYNTHETIC_QUALIFICATION_COMPLETED_WITH_GAUGE_AND_RESTART_BLOCKERS','completed_authorized_work':True,'all_gates_pass':False,
        'gates':{'uniform_MPI_CBF':'PASS','AMR_condensed_trace_G45R1_unremoved_gauge':'PASS_ALGEBRA_AND_EQUILIBRIUM_WITHIN_DECLARED_VARIANT_SCOPE','AMR_full_velocity_rank_parity':'PASS' if all(x['screen_pass'] for x in adaptive['rank_parity']) else 'BLOCKED_FROZEN_VELOCITY_PARITY_THRESHOLD','AMR_datum':'PASS' if all(x['screen_pass'] for x in adaptive['datum']) else 'BLOCKED_FROZEN_DATUM_OR_VELOCITY_THRESHOLD','original_net_rotation_forced_AMR':'BLOCKED_NATIVE_NONLINEAR_CONVERGENCE','hydrostatic_AMR_controls':'BLOCKED_NATIVE_NONLINEAR_CONVERGENCE' if adaptive.get('blocked_cases') else 'PASS','native_raw_AMR_force_conservation':'FAIL_FROZEN_SCREEN_IN_RETAINED_CASES','production_negative_tests':'PASS','native_checkpoint_restart':restart['same_rank_restart'],'rank_change_restart':'UNQUALIFIED'},
        'uniform_cases':len(uniform['cases']),'G45R1_adaptive_cases':len(adaptive['cases']),'negative_cases':len(neg['tests']),'native_case_invocations':len(rows),'cases':rows,
        'AMR_variant_blocked_cases':adaptive.get('blocked_cases',[]),'rigid_motion_checks':c.read(c.ROOT/'RIGID_MOTION_AND_VIRTUAL_WORK.json'),'B6K_documentary_provenance':c.read(c.ROOT/'B6K_SOURCE_PROVENANCE_ADJUDICATION.json'),'uniform_rank_parity':uniform['rank_parity'],'AMR_rank_parity':adaptive['rank_parity'],'uniform_datum':uniform['datum'],'AMR_datum':adaptive['datum'],'uniform_analytic_convergence':uniform['analytic_convergence'],'AMR_analytic_convergence':adaptive['analytic_convergence'],
        'original_AMR_failures':original,'restart_gate':restart,'contract_sha256':c.CONTRACT_PIN,'supplement_contract_sha256':c.sha(c.CODE/'gauge_diagnostic_contract_v1.json'),
        'plugin_identity':c.read(c.ROOT/'plugin_build_NEW02/PLUGIN_IDENTITY.json'),'closure_code_commit':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'source_sha':c.old.g25.SOURCE,
        'limitations':['full original net-rotation AMR matrix was stopped after nonlinear failure; G45R1 is a separate predeclared gauge variant, not retroactive PASS',
          'unremoved rotation reported explicitly; rotational gauge policy not generally qualified, no artificial pin/RHS/torque fit',
          'native CBF parity is distinct from equilibrium under topology constraints; native raw path fails the force screen on specific AMR cases',
          'homogeneous topology-only Q2, synthetic incompressible shell, bounded refinement rules and two mesh resolutions only',
          'coordinator SciPy audit uses consolidated arrays and is not scalable distributed postprocessing; plugin assembly/CG are distributed',
          'PSS/RSS sampled under native supervisor; short peaks may be missed, RSS double counts shared pages; coordinator audit outside native-process guard',
          'no native checkpoint at synthetic t0 via standard loop, positive synthetic time not authorized; exports/replays not called restart',
          'no physical mantle initializer, constitutive/normal-reaction authority, real SHELLS/ASPECT transfer or WORLD_HISTORY run'],**c.SCOPE}
    c.write(c.ROOT/'REPORT.json',report);print('G45_FINAL_PREPARED',len(rows),report['gates'],flush=True)


def seal():
    report=c.read(c.ROOT/'REPORT.json');c.need(report['completed_authorized_work'],'REPORT_NOT_READY');files={};links={};cache={}
    for p in sorted(c.ROOT.rglob('*')):
        if p==c.ROOT/'MANIFEST.json':continue
        rel=str(p.relative_to(c.ROOT))
        if p.is_symlink():links[rel]=os.readlink(p)
        if p.is_file():
            st=p.stat();key=(st.st_dev,st.st_ino,st.st_size,st.st_mtime_ns)
            if key not in cache:cache[key]=c.sha(p)
            files[rel]=cache[key]
    c.write(c.ROOT/'MANIFEST.json',{'status':report['status'],'source_sha':c.old.g25.SOURCE,'report_sha256':c.sha(c.ROOT/'REPORT.json'),'files':files,'symlink_targets':links,**c.SCOPE});print('G45_MANIFEST',c.sha(c.ROOT/'MANIFEST.json'),len(files),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','seal']);args=p.parse_args();(prepare if args.action=='prepare' else seal)()
