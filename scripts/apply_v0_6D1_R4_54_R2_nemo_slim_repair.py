from __future__ import annotations
from pathlib import Path
import hashlib,json,shutil

STAGE="v0.6D1-R4.54-R2"
OUT=Path("outputs/v0_6D1_R4_54_R2")
MANIFEST=Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R4_54.json")
PRE={
  "benchmarks/r454/run_nemo_r454.sh": "19aecd524d8eb504a1852cec54bdd293ad5b7cc393b00b9ad57901886bd0936f",
  "benchmarks/r454/nemo_collect_r454.py": "d943f79905cbb08c12373275966a4fe6ee2e22cfe834be5c8873229d0da24a0e",
  "benchmarks/r454/slim_collect_r454.py": "2a8640b0fb28fb597b971411486e2dcb193bbfe5d7499b531f61b3d2f40ded43"
}
POST={
  "benchmarks/r454/run_nemo_r454.sh": "6b4cadda339c7c253a3bbde42fa45ad7a59173cb3284309c3691e2dbf7b3930c",
  "benchmarks/r454/nemo_collect_r454.py": "4e588c5ac9be22ef6a7de11f3f8611bd750d4d7f2a86c416ac9a73f7730c7ffb",
  "benchmarks/r454/slim_collect_r454.py": "91dd0851b709664ed51dffdce2c65ae34ff7a0418ead57aca16cef33adb41c6e"
}

PATCHED_CONTENT={"benchmarks/r454/run_nemo_r454.sh": "#!/usr/bin/env bash\nset -euo pipefail\nini_src=\"$1\"; work=\"$2\"; out_json=\"$3\"; seed=\"$4\"; job_id=\"$5\"; collector=\"$6\"\nrm -rf \"$work\"; mkdir -p \"$work\"\npython - \"$ini_src\" \"$work/Nemo2_R454.ini\" \"$seed\" <<'PY'\nfrom pathlib import Path\nimport re,sys\nsrc=Path(sys.argv[1]).read_text()\nseed=int(sys.argv[3])\nsrc=re.sub(r'(?m)^random_seed\\s+\\d+\\s*$',f'random_seed             {seed}',src)\nsrc=re.sub(r'(?m)^logfile\\s+.*$',r'logfile                 r454_nemo.log',src)\nsrc=re.sub(r'(?m)^filename\\s+.*$',r'filename                r454_nemo',src)\nsrc=re.sub(r'(?m)^stat_log_time\\s+\\d+\\s*$',r'stat_log_time           10',src)\nsrc=re.sub(r'(?m)^quanti_freq_logtime\\s+\\d+\\s*$',r'quanti_freq_logtime     10',src)\nPath(sys.argv[2]).write_text(src)\nPY\ncd \"$work\"\nset +e\nnemo2.4.2 Nemo2_R454.ini >engine.stdout.txt 2>engine.stderr.txt\nrc=$?\nset -e\nif [ \"$rc\" -ne 0 ]; then\n  python - \"$out_json\" \"$seed\" \"$job_id\" \"$rc\" <<'PY'\nfrom pathlib import Path\nimport json,sys\nout=Path(sys.argv[1]); seed=int(sys.argv[2]); job_id=sys.argv[3]; rc=int(sys.argv[4])\nstderr=Path(\"engine.stderr.txt\").read_text(errors=\"replace\")[-8000:] if Path(\"engine.stderr.txt\").exists() else \"\"\nstdout=Path(\"engine.stdout.txt\").read_text(errors=\"replace\")[-8000:] if Path(\"engine.stdout.txt\").exists() else \"\"\nresult={\n \"stage\":\"v0.6D1-R4.54\",\"engine\":\"NEMO\",\"probe_job_id\":job_id,\n \"frozen_seed\":seed,\"seed_injection_mode\":\"NEMO_RANDOM_SEED_INI_PARAMETER\",\n \"seed_binding_verified\":False,\"dry_run\":True,\"scientific_evidence\":False,\n \"status\":\"FAIL\",\"returncode\":rc,\"metrics\":[],\n \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n \"automatic_scientific_pass_fail_count\":0,\"artifact_hashes\":{},\n \"canonical_state_changed\":False,\"error\":\"NEMO execution failed\",\n \"engine_stdout_tail\":stdout,\"engine_stderr_tail\":stderr,\n}\nout.write_text(json.dumps(result,indent=2,sort_keys=True)+\"\\n\")\nPY\n  exit \"$rc\"\nfi\n\nqfreq=\"\"\nif [ -s \"r454_nemo_1.qfreq\" ]; then\n  qfreq=\"r454_nemo_1.qfreq\"\nelse\n  qfreq=\"$(find . -maxdepth 1 -type f -name '*.qfreq' -size +0c | sort | head -n 1 || true)\"\nfi\nif [ -z \"$qfreq\" ] || [ ! -s \"$qfreq\" ]; then\n  python - \"$out_json\" \"$seed\" \"$job_id\" <<'PY'\nfrom pathlib import Path\nimport json,sys\nout=Path(sys.argv[1]); seed=int(sys.argv[2]); job_id=sys.argv[3]\nfiles=sorted(p.name for p in Path(\".\").iterdir())\nstderr=Path(\"engine.stderr.txt\").read_text(errors=\"replace\")[-8000:] if Path(\"engine.stderr.txt\").exists() else \"\"\nstdout=Path(\"engine.stdout.txt\").read_text(errors=\"replace\")[-8000:] if Path(\"engine.stdout.txt\").exists() else \"\"\nresult={\n \"stage\":\"v0.6D1-R4.54\",\"engine\":\"NEMO\",\"probe_job_id\":job_id,\n \"frozen_seed\":seed,\"seed_injection_mode\":\"NEMO_RANDOM_SEED_INI_PARAMETER\",\n \"seed_binding_verified\":False,\"dry_run\":True,\"scientific_evidence\":False,\n \"status\":\"FAIL\",\"returncode\":20,\"metrics\":[],\n \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n \"automatic_scientific_pass_fail_count\":0,\"artifact_hashes\":{},\n \"canonical_state_changed\":False,\"error\":\"NEMO qfreq output missing\",\n \"runtime_file_listing\":files,\"engine_stdout_tail\":stdout,\"engine_stderr_tail\":stderr,\n}\nout.write_text(json.dumps(result,indent=2,sort_keys=True)+\"\\n\")\nPY\n  exit 20\nfi\n\nset +e\npython \"$collector\" \"$out_json\" \"$work/Nemo2_R454.ini\" \"$qfreq\" \\\n  \"$work/engine.stdout.txt\" \"$work/engine.stderr.txt\" \"$seed\" \"$job_id\"\ncrc=$?\nset -e\nif [ \"$crc\" -ne 0 ] && [ ! -s \"$out_json\" ]; then\n  python - \"$out_json\" \"$seed\" \"$job_id\" \"$crc\" \"$qfreq\" <<'PY'\nfrom pathlib import Path\nimport json,sys\nout=Path(sys.argv[1]); seed=int(sys.argv[2]); job_id=sys.argv[3]; rc=int(sys.argv[4]); qfreq=sys.argv[5]\nresult={\n \"stage\":\"v0.6D1-R4.54\",\"engine\":\"NEMO\",\"probe_job_id\":job_id,\n \"frozen_seed\":seed,\"seed_injection_mode\":\"NEMO_RANDOM_SEED_INI_PARAMETER\",\n \"seed_binding_verified\":False,\"dry_run\":True,\"scientific_evidence\":False,\n \"status\":\"FAIL\",\"returncode\":rc,\"metrics\":[],\n \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n \"automatic_scientific_pass_fail_count\":0,\"artifact_hashes\":{},\n \"canonical_state_changed\":False,\n \"error\":\"NEMO collector failed before result materialization\",\n \"qfreq_file\":qfreq,\n}\nout.write_text(json.dumps(result,indent=2,sort_keys=True)+\"\\n\")\nPY\nfi\nexit \"$crc\"\n", "benchmarks/r454/nemo_collect_r454.py": "from __future__ import annotations\nfrom pathlib import Path\nimport hashlib,json,math,re,sys,traceback\n\nout=Path(sys.argv[1]); ini=Path(sys.argv[2]); qfreq=Path(sys.argv[3])\nstdout_path=Path(sys.argv[4]); stderr_path=Path(sys.argv[5])\nseed=int(sys.argv[6]); job_id=sys.argv[7]\n\ntry:\n    text=ini.read_text()\n    m=re.search(r'(?m)^random_seed\\s+(\\d+)\\s*$',text)\n    bound_ini=int(m.group(1)) if m else None\n\n    stdout=stdout_path.read_text(errors=\"replace\") if stdout_path.exists() else \"\"\n    sm=re.search(r'setting\\s+random\\s+seed\\s+from\\s+input\\s+value:\\s*(\\d+)',stdout,re.I)\n    bound_stdout=int(sm.group(1)) if sm else None\n    seed_ok=(bound_ini==seed and bound_stdout==seed)\n\n    raw=[x.split() for x in qfreq.read_text().splitlines() if x.strip()]\n    if len(raw)<2:\n        raise RuntimeError(\"qfreq has no data rows\")\n    header=raw[0]\n    if header[:4] != [\"pop\",\"trait\",\"locus\",\"allele\"]:\n        raise RuntimeError(f\"unexpected qfreq leading schema: {header[:4]}\")\n    gen_cols=header[4:]\n    if not gen_cols:\n        raise RuntimeError(\"qfreq has no generation columns\")\n\n    values=[]\n    for ri,row in enumerate(raw[1:],1):\n        if len(row) != len(header):\n            raise RuntimeError(\n                f\"qfreq row {ri} width {len(row)} != header width {len(header)}\"\n            )\n        values.append({\n            \"population\":int(row[0]),\"trait\":int(row[1]),\"locus\":int(row[2]),\n            \"allele\":float(row[3]),\n            \"frequencies\":[float(x) for x in row[4:]],\n        })\n\n    flat=[x for r in values for x in r[\"frequencies\"]]\n    by={(r[\"population\"],r[\"locus\"]):r[\"frequencies\"] for r in values}\n    gaps=[]\n    loci=sorted({r[\"locus\"] for r in values})\n    for gi,_ in enumerate(gen_cols):\n        ds=[]\n        for locus in loci:\n            a=by.get((1,locus)); b=by.get((2,locus))\n            if a is not None and b is not None:\n                ds.append(abs(a[gi]-b[gi]))\n        if not ds:\n            raise RuntimeError(f\"no paired population frequencies for generation column {gen_cols[gi]}\")\n        gaps.append(sum(ds)/len(ds))\n\n    finite=(\n        all(math.isfinite(x) for x in flat)\n        and all(math.isfinite(x) for x in gaps)\n    )\n    qhash=hashlib.sha256(qfreq.read_bytes()).hexdigest()\n    result={\n      \"stage\":\"v0.6D1-R4.54\",\"engine\":\"NEMO\",\"probe_job_id\":job_id,\n      \"frozen_seed\":seed,\"seed_injection_mode\":\"NEMO_RANDOM_SEED_INI_PARAMETER\",\n      \"seed_binding_verified\":seed_ok,\"dry_run\":True,\"scientific_evidence\":False,\n      \"status\":\"PASS\" if seed_ok and finite and len(values)>0 else \"FAIL\",\n      \"returncode\":0,\n      \"metrics\":[\n        {\"metric_id\":\"NEMO_ALLELE_FREQUENCY_TRAJECTORY\",\n         \"metric_role\":\"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE\",\n         \"payload\":{\"generation_columns\":gen_cols,\"rows\":values},\n         \"finite\":finite,\"numeric_acceptance_threshold\":None,\n         \"automatic_pass_fail_from_value\":False},\n        {\"metric_id\":\"NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY\",\n         \"metric_role\":\"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE\",\n         \"payload\":{\"generation_columns\":gen_cols,\n                    \"mean_absolute_population_gap\":gaps},\n         \"finite\":finite,\"numeric_acceptance_threshold\":None,\n         \"automatic_pass_fail_from_value\":False},\n      ],\n      \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n      \"automatic_scientific_pass_fail_count\":0,\n      \"artifact_hashes\":{\"NEMO_NATIVE_QFREQ_OUTPUT\":qhash},\n      \"canonical_state_changed\":False,\n      \"seed_readback\":{\"ini\":bound_ini,\"engine_stdout\":bound_stdout},\n    }\nexcept Exception as exc:\n    result={\n      \"stage\":\"v0.6D1-R4.54\",\"engine\":\"NEMO\",\"probe_job_id\":job_id,\n      \"frozen_seed\":seed,\"seed_injection_mode\":\"NEMO_RANDOM_SEED_INI_PARAMETER\",\n      \"seed_binding_verified\":False,\"dry_run\":True,\"scientific_evidence\":False,\n      \"status\":\"FAIL\",\"returncode\":1,\"metrics\":[],\n      \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n      \"automatic_scientific_pass_fail_count\":0,\"artifact_hashes\":{},\n      \"canonical_state_changed\":False,\"error\":repr(exc),\n      \"traceback\":traceback.format_exc()[-10000:],\n      \"engine_stdout_tail\":\n          stdout_path.read_text(errors=\"replace\")[-8000:] if stdout_path.exists() else \"\",\n      \"engine_stderr_tail\":\n          stderr_path.read_text(errors=\"replace\")[-8000:] if stderr_path.exists() else \"\",\n    }\n\nout.write_text(json.dumps(result,indent=2,sort_keys=True)+\"\\n\")\nraise SystemExit(0 if result[\"status\"]==\"PASS\" else 1)\n", "benchmarks/r454/slim_collect_r454.py": "from __future__ import annotations\nimport hashlib,json,math,re,sys,traceback\nfrom pathlib import Path\n\nout=Path(sys.argv[1]); trees=Path(sys.argv[2]); stdout=Path(sys.argv[3])\nseed=int(sys.argv[4]); job_id=sys.argv[5]\n\ntry:\n    import numpy as np\n    import tskit\n\n    stdout_text=stdout.read_text(encoding=\"utf-8\",errors=\"replace\") if stdout.exists() else \"\"\n    sm=re.search(r'Initial\\s+random\\s+seed:\\s*(\\d+)',stdout_text,re.I|re.S)\n    seed_readback=int(sm.group(1)) if sm else None\n    seed_ok=(seed_readback==seed)\n\n    ts=tskit.load(str(trees))\n    pops=[\n        p.id for p in ts.populations()\n        if len(ts.samples(population=p.id))>0\n    ]\n    if len(pops)<2:\n        raise RuntimeError(f\"expected >=2 sampled populations, found {pops}\")\n\n    a=ts.samples(population=pops[0])\n    b=ts.samples(population=pops[1])\n    if len(a)<=0 or len(b)<=0:\n        raise RuntimeError(\"first two sampled populations must both contain samples\")\n\n    # Same intended R4.54 statistic as before, but use the documented\n    # two-sample-set calling form, which yields a scalar for one pair.\n    raw_div=ts.divergence(sample_sets=[a,b])\n    arr=np.asarray(raw_div)\n    if arr.size != 1:\n        raise RuntimeError(f\"unexpected divergence output shape {arr.shape}\")\n    divergence=float(arr.reshape(-1)[0])\n\n    structural={\n      \"nodes\":int(ts.num_nodes),\"edges\":int(ts.num_edges),\n      \"individuals\":int(ts.num_individuals),\"mutations\":int(ts.num_mutations),\n      \"sequence_length\":float(ts.sequence_length),\"trees\":int(ts.num_trees),\n    }\n    genealogy={\n      \"population_ids\":pops,\n      \"sample_counts\":[int(len(ts.samples(population=p))) for p in pops],\n      \"between_population_divergence\":divergence,\n      \"divergence_mode\":\"site\",\n      \"sample_set_pair\":[pops[0],pops[1]],\n    }\n    finite=(\n        all(math.isfinite(float(v)) for v in structural.values())\n        and math.isfinite(divergence)\n    )\n\n    result={\n      \"stage\":\"v0.6D1-R4.54\",\"engine\":\"SLiM\",\"probe_job_id\":job_id,\n      \"frozen_seed\":seed,\"seed_injection_mode\":\"SLIM_COMMAND_LINE_MINUS_S_SEED\",\n      \"seed_binding_verified\":seed_ok,\"dry_run\":True,\"scientific_evidence\":False,\n      \"status\":\"PASS\" if finite and seed_ok else \"FAIL\",\"returncode\":0,\n      \"metrics\":[\n       {\"metric_id\":\"SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY\",\n        \"metric_role\":\"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE\",\n        \"payload\":structural,\"finite\":finite,\"numeric_acceptance_threshold\":None,\n        \"automatic_pass_fail_from_value\":False},\n       {\"metric_id\":\"SLIM_ANCESTRY_GENE_FLOW_SUMMARY\",\n        \"metric_role\":\"SCIENTIFIC_DESCRIPTIVE_GENETIC_STATE\",\n        \"payload\":genealogy,\"finite\":finite,\"numeric_acceptance_threshold\":None,\n        \"automatic_pass_fail_from_value\":False},\n      ],\n      \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n      \"automatic_scientific_pass_fail_count\":0,\n      \"artifact_hashes\":{\n        \"SLIM_TREE_SEQUENCE_RAW\":\n            hashlib.sha256(trees.read_bytes()).hexdigest()\n      },\n      \"canonical_state_changed\":False,\n      \"seed_readback\":seed_readback,\n    }\nexcept Exception as exc:\n    result={\n      \"stage\":\"v0.6D1-R4.54\",\"engine\":\"SLiM\",\"probe_job_id\":job_id,\n      \"frozen_seed\":seed,\"seed_injection_mode\":\"SLIM_COMMAND_LINE_MINUS_S_SEED\",\n      \"seed_binding_verified\":False,\"dry_run\":True,\"scientific_evidence\":False,\n      \"status\":\"FAIL\",\"returncode\":1,\"metrics\":[],\n      \"unauthorized_metric_count\":0,\"numeric_acceptance_threshold_count\":0,\n      \"automatic_scientific_pass_fail_count\":0,\"artifact_hashes\":{},\n      \"canonical_state_changed\":False,\"error\":repr(exc),\n      \"traceback\":traceback.format_exc()[-10000:],\n      \"engine_stdout_tail\":\n          stdout.read_text(encoding=\"utf-8\",errors=\"replace\")[-8000:]\n          if stdout.exists() else \"\",\n    }\n\nout.write_text(json.dumps(result,indent=2,sort_keys=True)+\"\\n\")\nraise SystemExit(0 if result[\"status\"]==\"PASS\" else 1)\n"}

def sha(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def preserve(root:Path)->None:
    dst=root/OUT/"PREPATCH_BLOCKED_EVIDENCE"
    dst.mkdir(parents=True,exist_ok=True)
    files=[
      root/"outputs/v0_6D1_R4_54/R4_54_RUNTIME_IDENTITY_EVIDENCE.json",
      root/"outputs/v0_6D1_R4_54/R4_54_HOST_DRY_RUN_EVIDENCE.json",
      root/"outputs/v0_6D1_R4_54/R4_54_INTEGRATED_AUDIT.json",
      root/"outputs/v0_6D1_R4_54/R4_54_SCIENTIFIC_EXECUTION_AUTHORIZATION.json",
      root/"outputs/v0_6D1_R4_54_R1/R4_54_R1_REPAIR_APPLICATION.json",
    ]
    for p in files:
      if p.exists():
        q=dst/p.name
        if not q.exists(): shutil.copy2(p,q)
    for name in ("dry_runs","runtime_work"):
      p=root/"outputs/v0_6D1_R4_54"/name
      q=dst/name
      if p.exists() and not q.exists():
        shutil.copytree(p,q)
    sdst=root/OUT/"PREPATCH_SOURCE"
    sdst.mkdir(parents=True,exist_ok=True)
    for rel,expected in PRE.items():
      p=root/rel
      if p.exists() and sha(p)==expected:
        q=sdst/Path(rel).name
        if not q.exists(): shutil.copy2(p,q)

def main()->int:
    root=Path.cwd()
    preserve(root)
    for rel,pre in PRE.items():
      p=root/rel
      cur=sha(p)
      post=POST[rel]
      if cur==pre:
        p.write_text(PATCHED_CONTENT[rel],encoding="utf-8",newline="\n")
      elif cur==post:
        pass
      else:
        raise RuntimeError(
          f"R454_R2_SOURCE_HASH_NOT_AUTHORIZED {rel}: {cur} "
          f"expected pre={pre} or post={post}"
        )
      actual=sha(p)
      if actual!=post:
        raise RuntimeError(f"R454_R2_POSTPATCH_HASH_MISMATCH {rel} {actual} != {post}")

    mp=root/MANIFEST
    m=json.loads(mp.read_text(encoding="utf-8"))
    updated=set()
    for rec in m["files"]:
      rel=rec["path"]
      if rel in POST:
        p=root/rel
        rec["sha256"]=POST[rel]
        rec["bytes"]=p.stat().st_size
        updated.add(rel)
    if updated!=set(POST):
      raise RuntimeError(f"R454_R2_MANIFEST_TARGET_MISMATCH {updated}")
    mp.write_text(json.dumps(m,indent=2)+"\n",encoding="utf-8",newline="\n")

    result={
      "stage":STAGE,
      "status":"PASS_R454_R2_NEMO_RESULT_CAPTURE_AND_SLIM_DIVERGENCE_API_REPAIR_APPLIED",
      "root_causes":{
        "NEMO":"NEMO_DRY_RUN_PATH_COULD_EXIT_WITHOUT_STANDARD_RESULT_JSON_OBSCURING_QFREQ_OR_COLLECTOR_FAILURE",
        "SLiM":"SLIM_ANCESTRY_COLLECTOR_FAILED_INSIDE_NEW_DIVERGENCE_READOUT_PATH_BEFORE_METRIC_MATERIALIZATION"
      },
      "repairs":{
        "NEMO":[
          "ALWAYS_MATERIALIZE_STANDARD_FAILURE_JSON",
          "DISCOVER_EXACT_OR_ANY_NONEMPTY_QFREQ",
          "VERIFY_FROZEN_SEED_FROM_INI_AND_NATIVE_NEMO_STDOUT",
          "WRAP_QFREQ_COLLECTOR_WITH_SCHEMA_AND_TRACEBACK_DIAGNOSTICS"
        ],
        "SLiM":[
          "PRESERVE_SAME_BETWEEN_POPULATION_DIVERGENCE_STATISTIC",
          "USE_TSKIT_DOCUMENTED_TWO_SAMPLE_SET_DIVERGENCE_CALL",
          "NORMALIZE_SINGLE_SCALAR_RETURN_SHAPE",
          "VERIFY_FROZEN_SEED_FROM_NATIVE_SLIM_STDOUT"
        ]
      },
      "prepatch_sha256":PRE,
      "postpatch_sha256":POST,
      "governance":{
        "blocked_r454_evidence_preserved":True,
        "madingley_prior_dry_run_pass_preserved":True,
        "rangeshifter_prior_dry_run_pass_preserved":True,
        "cdmetapop_prior_dry_run_pass_preserved":True,
        "historical_scientific_execution_performed":False,
        "scientific_evidence_modified":False,
        "authorized_metric_ids_modified":False,
        "numeric_thresholds_added":False,
        "automatic_scientific_pass_fail_added":False,
        "canonical_state_changed":False,
        "gate_weakening_performed":False
      }
    }
    (root/OUT).mkdir(parents=True,exist_ok=True)
    (root/OUT/"R4_54_R2_REPAIR_APPLICATION.json").write_text(
      json.dumps(result,indent=2)+"\n",encoding="utf-8"
    )
    print(json.dumps(result,indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
