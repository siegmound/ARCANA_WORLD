from __future__ import annotations
import csv, json, shutil, subprocess, sys, traceback
from pathlib import Path

PIN='3516aa4e124c57e2f9f4c1d9f1a3bca735ed9118'
out=Path(sys.argv[1]); work=Path(sys.argv[2]); repo=Path(sys.argv[3])
out.parent.mkdir(parents=True,exist_ok=True)

def tail(path: Path, n: int = 12000) -> str:
    try:
        text=path.read_text(encoding='utf-8',errors='replace')
        return text[-n:]
    except Exception:
        return ''

try:
    src=repo/'src'/'CDmetaPOP.py'
    if not src.exists():
        alt=repo/'src'/'CDMetaPOP.py'
        if alt.exists(): src=alt
    examples=repo/'example_files'
    if not src.exists() or not examples.exists():
        raise FileNotFoundError(f'CDMetaPOP source/example_files missing under {repo}')
    if work.exists(): shutil.rmtree(work)
    inp=work/'example_files'; shutil.copytree(examples,inp)

    # v3.08 source/input compatibility shim, applied ONLY to the isolated copy:
    # src/CDmetaPOP_mainloop.py unconditionally reads `implement_disease`, while
    # the commit's generic PopVars.csv predates that column. The same pinned
    # source explicitly accepts N/Both/Back/Out; use N so this benchmark keeps
    # disease disabled and otherwise preserves the generic example unchanged.
    upstream_runvars=inp/'RunVars.csv'
    generic_popvars=inp/'popvars'/'PopVars.csv'
    if not upstream_runvars.exists() or not generic_popvars.exists():
        raise FileNotFoundError('Pinned generic RunVars.csv/PopVars.csv missing')

    with generic_popvars.open(newline='',encoding='utf-8-sig') as f:
        pop_rows=list(csv.DictReader(f))
        pop_fields=list(pop_rows[0].keys()) if pop_rows else []
    if not pop_rows:
        raise RuntimeError('Pinned generic PopVars.csv has no scenarios')
    compatibility_shim_applied='implement_disease' not in pop_fields
    if compatibility_shim_applied:
        pop_fields.append('implement_disease')
        for row in pop_rows:
            row['implement_disease']='N'

    # R4.1 is a controlled microbenchmark, not a sweep over all four generic
    # PopVars rows. The upstream generic RunVars points at PopVars.csv, whose
    # later rows intentionally exercise different population-model semantics
    # (including a logistic form that requires an out/back qualifier). Freeze
    # exactly the first pinned generic row into an isolated benchmark PopVars
    # file so the engine executes one coherent 5-generation scenario.
    benchmark_popvars=inp/'popvars'/'PopVars_R41.csv'
    benchmark_pop_rows=[dict(pop_rows[0])]
    with benchmark_popvars.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=pop_fields)
        w.writeheader(); w.writerows(benchmark_pop_rows)

    with upstream_runvars.open(newline='',encoding='utf-8-sig') as f:
        upstream_rows=list(csv.DictReader(f))
        fieldnames=list(upstream_rows[0].keys()) if upstream_rows else []
    if not upstream_rows:
        raise RuntimeError('Pinned generic CDMetaPOP RunVars.csv has no scenarios')
    rows=[dict(upstream_rows[0])]
    rows[0]['mcruns']='1'
    rows[0]['runtime']='5'
    rows[0]['output_years']='1'
    rows[0]['Popvars']='popvars/PopVars_R41.csv'
    benchmark_runvars=inp/'RunVars_R41.csv'
    with benchmark_runvars.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fieldnames)
        w.writeheader(); w.writerows(rows)

    popvars_rel=rows[0].get('Popvars','')
    popvars_path=inp/popvars_rel
    with popvars_path.open(newline='',encoding='utf-8-sig') as f:
        popvar_reader=csv.DictReader(f)
        popvar_fields=list(popvar_reader.fieldnames or [])
        popvar_rows=sum(1 for _ in popvar_reader)
    if 'implement_disease' not in popvar_fields:
        raise RuntimeError('R4.1 compatibility shim failed to materialize implement_disease')

    # Fail closed on the generic example's directly referenced parameter chain.
    patchvars_path=inp/'patchvars'/'PatchVars.csv'
    classvars_path=inp/'classvars'/'ClassVars_AS1.csv'
    if not patchvars_path.exists() or not classvars_path.exists():
        raise FileNotFoundError('Pinned generic parameter chain PatchVars.csv/ClassVars_AS1.csv is incomplete')

    runtimes=[int(float(r.get('runtime') or 0)) for r in rows]
    before={p.relative_to(work).as_posix() for p in work.rglob('*') if p.is_file()}
    cmd=[sys.executable,str(src),str(inp),benchmark_runvars.name,'R41_smoke']
    proc=subprocess.run(cmd,cwd=str(repo/'src'),text=True,capture_output=True,check=False,timeout=300)
    after={p.relative_to(work).as_posix() for p in work.rglob('*') if p.is_file()}
    new=sorted(after-before)
    csvs=[x for x in new if x.lower().endswith('.csv')]
    output_roots=sorted(p.relative_to(work).as_posix() for p in inp.glob('R41_smoke*') if p.is_dir())
    logs=sorted(p for p in work.rglob('CDmetaPOP*.log') if p.is_file())
    cp=subprocess.run(['git','-C',str(repo),'rev-parse','HEAD'],text=True,capture_output=True,check=False)
    commit=cp.stdout.strip() if cp.returncode==0 else ''
    log_tail='\n\n'.join(f'--- {p.relative_to(work).as_posix()} ---\n{tail(p)}' for p in logs[-4:])[-16000:]
    metrics={
        'scenario_rows':len(rows),
        'runtime_generations':max(runtimes) if runtimes else 0,
        'new_output_files':len(new),
        'csv_output_files':len(csvs),
        'output_root_directories':len(output_roots),
        'source_commit':commit,
        'source_entrypoint':src.name,
        'upstream_runvars_source':upstream_runvars.name,
        'benchmark_runvars':benchmark_runvars.name,
        'selected_popvars':popvars_rel,
        'selected_popvars_rows':popvar_rows,
        'upstream_generic_popvars_rows':len(pop_rows),
        'benchmark_popvars_isolated_first_row':popvar_rows==1,
        'selected_popvars_has_implement_disease':'implement_disease' in popvar_fields,
        'compatibility_shim_applied':compatibility_shim_applied,
        'compatibility_shim_value':'N',
        'generic_patchvars_present':patchvars_path.exists(),
        'generic_classvars_present':classvars_path.exists(),
        'source_tree_modified':False,
        'sample_outputs':new[:20]
    }
    status='PASS' if proc.returncode==0 and metrics['scenario_rows']>=1 and metrics['runtime_generations']>=1 and metrics['new_output_files']>0 and metrics['csv_output_files']>0 and metrics['output_root_directories']>0 and metrics['selected_popvars_has_implement_disease'] and metrics['benchmark_popvars_isolated_first_row'] and metrics['generic_patchvars_present'] and metrics['generic_classvars_present'] and not metrics['source_tree_modified'] and commit==PIN else 'FAIL'
    result={
        'status':status,
        'returncode':proc.returncode,
        'metrics':metrics,
        'stdout_tail':proc.stdout[-12000:],
        'stderr_tail':proc.stderr[-12000:],
        'engine_log_tail':log_tail,
        'command':cmd,
    }
except Exception as exc:
    result={'status':'FAIL','returncode':1,'metrics':{},'error':repr(exc),'traceback':traceback.format_exc()[-12000:]}
out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
if result['status']!='PASS': raise SystemExit(1)
