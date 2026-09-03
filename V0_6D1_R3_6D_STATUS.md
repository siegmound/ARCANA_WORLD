# v0.6D1-R3.6D status

**Implementation status:** EXECUTABLE BINDING CANDIDATE PASS.

**External scientific evidence status in ChatGPT build environment:** NEMO EXECUTION PENDING.

Reason: the build/container environment does not contain `nemo2.4.2` or conda. R3.6D therefore does not fabricate engine output. The runpack includes the pinned WSL installation/preflight and complete local execution/evidence pipeline.

Closed in this candidate:

- upstream-source-bound NEMO 2.4.2 INI renderer;
- exact QTL effect/frequency mapping;
- controlled Wright-Fisher `breed_disperse` lifecycle;
- cadence-normalized symmetric migration binding;
- common-random-number FLOW/no-flow paired experiment;
- population-size sensitivity scaffold;
- qfreq quantitative evidence parser;
- ScientificEvidenceBundle emission;
- automated NEMO-vs-ARCANA admixture-only comparison;
- WSL setup, parallel execution and collection runners;
- governance locks preserving ARCANA authority.

Still pending before any R3.5 parameter decision:

- actual NEMO 2.4.2 pilot/ensemble execution on the user's WSL environment;
- review of finite-N sensitivity;
- scientific inference from the three-way evidence.

No changes to `mu`, `b`, `q*=0.045`, production ceiling, paleogeography, fission/coalescence, speciation, RI or canonical World 1 state are authorized here.

## R2 executable-evidence repair
- Real-engine smoke: 10/10 jobs rc=0; 0 qfreq under original `generations-1` schedule.
- Root cause: NEMO 2.4.2 qfreq extractor persists on a final-generation callback.
- Repair: final-only `quanti_freq_logtime = generations`; invalid custom schedules fail closed.
- Scientific state/parameters: unchanged.
