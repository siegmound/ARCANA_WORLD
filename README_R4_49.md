# ARCANA WorldSim v0.6D1-R4.49
## Geonomics J14/J18 Full-Job Revalidation Coverage Expansion Execution & Evidence Capture

Parent:
- R4.48 integrated 52/52 PASS
- R4.48 final seal 27/27 SEALED
- frozen expansion plan SHA256:
  `3a6e1d5b7d454f7c4ecd79c357bc6a2e8cd6e6514c61db07a5d06267834766e5`

R4.49 is the large scientific expansion run.

It executes only:
- 191 missing J14 branches;
- 63 missing J18 branches;
- all four frozen seeds for each branch.

It does **not** rerun:
- J14 M000_C00;
- J18 M000_C00;
- J21.

## Resumable evidence capture

R4.48 froze 32 deterministic shards:
- J14: 24
- J18: 8

R4.49 writes each shard independently:

- `METRIC_RECORDS.jsonl.gz`
- `SHARD_SUMMARY.json`

The gzip evidence file is deterministic (`mtime=0`), and its SHA256 is bound
into the shard summary.

A completed shard is reused on a later invocation only when all of these still
match:
- R4.48 plan SHA;
- shard ID;
- exact frozen branch list;
- stream counts;
- evidence-file SHA256;
- shard PASS state.

An invalid or interrupted shard directory is preserved under
`failed_or_partial_shards/` and the **same frozen shard** is executed again.
No branch selection changes during resume.

## Operational parallelism

The PowerShell runner accepts:

```powershell
-ParallelJobs N
```

Default:

`2`

Parallelism is operational only. It does not change shard membership, seeds,
metric definitions, or evidence identity.

## Expected new evidence

32 shards / 254 branches / 1,016 streams:

- 334,512 metric records
- 223,008 exact-integrity
- 111,504 scientific-descriptive

## Expected full Geonomics evidence after merging SEALED evidence

After adding:
- existing J14 M000_C00 evidence;
- existing J18 M000_C00 evidence;
- existing full J21 evidence;

the complete Geonomics evidence corpus should contain:

- 346,968 metric records
- 229,548 integrity
- 117,420 descriptive

Coverage should become:
- J14: 192/192
- J18: 64/64
- J21: 1/1

## Scientific semantics

R4.49 captures full-coverage evidence but does not yet perform final full-job
scientific adjudication.

Every expansion stream still requires:
- exact canonical coordinate/cell replay;
- finite nearest-neighbor descriptive evidence;
- zero numeric acceptance thresholds;
- zero automatic scientific PASS/FAIL;
- zero autonomous movement/demography/ageing;
- no canonical rewrite.

R4.50 performs the full evidence review and final Geonomics closure.

## Run

Recommended initial invocation:

```powershell
.\run_v0_6D1_R4_49.ps1 -ParallelJobs 2
```

The same command may safely be invoked again after interruption. Valid completed
shards will be reused.

If local memory/headroom is comfortable, operational parallelism may be
increased without changing scientific authority, for example:

```powershell
.\run_v0_6D1_R4_49.ps1 -ParallelJobs 4
```

Next if SEALED:

`BUILD_R450_GEONOMICS_FULL_JOB_REVALIDATION_EVIDENCE_REVIEW_AND_FINAL_GEONOMICS_CLOSURE`
