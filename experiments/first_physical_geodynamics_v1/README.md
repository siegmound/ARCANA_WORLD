# First physical geodynamics — regional input recovery

`FIRST_PHYSICAL_GEODYNAMICS=BLOCKED_REGIONAL_MECHANICAL_INPUTS`.

This namespace contains a stdlib read-only evidence/input audit, not a new solver or a runnable physical case. Selected mechanical candidate: existing ShellSet/SHELLS, with existing PRE thermomechanical source consumers and R6 history structures. ASPECT remains an alternative, not an additional prerequisite.

`audit.py` recovers historical specialist results, checks exact file SHA identities, records source anchors and produces a precise incomplete regional input template. It never imports or executes a provider, solver or forward kernel. The command exits0 when the documentary audit completes; RESULT.json contains the BLOCKED physical verdict. Old benchmarks and numerical tests are not repeated. Missing regional inputs are null rather than synthetic defaults.

Reproduce into a NEW, nonexistent directory:

```bash
PYTHONDONTWRITEBYTECODE=1 python \
  experiments/first_physical_geodynamics_v1/audit.py \
  --repo /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_GEOMETRY_R1_WORK \
  --output /tmp/arcana_first_physical_geodynamics_new_output
```

Requires the exact original paths recorded in INPUT_IDENTITIES; no network, external packages or engine installation. The output writer refuses an existing output directory.

Useful results in the delivered evidence audit03:

- CAPABILITIES.json: TESTED_UPSTREAM / R6_ADAPTER_TESTED / R6_PHYSICAL_RUN_TESTED / GLOBAL_PHYSICS_READY, each with a finite evidence scope.
- INPUT_READINESS.json: known T0 mesh/frame, PRE records, materials,12Euler vectors and the already-authored conditional first-segment rule; four missing regional physical closures.
- REGIONAL_INPUT_TEMPLATE.json: concrete packet fields still missing. Not a launch contract or complete model.
- HISTORICAL_HASH_COMPARISONS.json:22comparisons over21distinct historical files, all matching. No new measurement of engine performance.
- SOURCE_ANCHORS.json: exact paths, SHA and lines showing the actual ShellSet/INT10K responsibilities.
- THERMAL_FALLBACK.json: already-executed10year conduction/radiogenesis archive kept distinct from a mechanical T1.

The first two audit invocations stopped on incorrect text-search needles in the source-anchor collector (Xe, then width_m). Their sources/logs are preserved; the final collector uses the actual source key. No mathematical acceptance criterion, physical parameter, original source or previous result changed. Only audit03 is the completed recovery. No new benchmark, thermal trajectory or mechanical solve was executed.
