# INT-0B provider preflight and execution proposal

Date: 2026-10-13
Repository: `ARCANA_WORLD_R6_BW0`
Branch: `r6/si1-bandwidth-f2av`
Preflight source HEAD: `dde79ebe4d26ab7b21eff08245fc83330239c0bc`

## Decision

`INT0B_PROVIDER_INPUTS_VERIFIED__EXECUTION_PENDING_AUTHORIZATION`

The provider-backed input audit for the existing continental engineering case 5:11 passed on this checkout. This report does **not** record a 1,000-year trajectory execution. That run remains blocked until the user explicitly authorizes the exact command, destination, environment, and resource/stop contract below.

## Governing scope and unchanged gates

This is the existing T-F2B engineering experiment at T0 = 210 Ma, with two exact admitted continental cells and a frozen instantaneous Euler driver for 1,000 engineering years. It is separate from the B6 rift pair 1:3. No physical rift event, geological validity interval, ShellSet execution, MPI, Solver, DGBSV, canonical history write, or WORLD_HISTORY access is authorized.

Preserved gates:

- `BLOCKED_F2AV_QUALIFICATION`
- `OPERATOR_CLASS_UNVERIFIED`
- `THRESHOLD_UNJUSTIFIED`
- `RESOURCE_2GB_SCOPE_UNRESOLVED`
- `F2B_SOLVER_EXECUTION_AUTHORIZED=false`
- `ARCANA_SI1_MECHANICS_QUALIFIED=false`
- `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`

## Input inventory and observed identities

The provider audit was run read-only using the repository API `audit_pair_5_11(Path.cwd(), expected_branch="r6/si1-bandwidth-f2av")`, with `ARCANA_EXTERNAL_ROOT=F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES`. The existing loaders checked governed manifests, payload hashes, source lineage, support membership, and profile bindings. The hashes below identify the actual bytes inspected in this preflight; they do not authenticate an unobserved future filesystem state.

| Input / authority | Located path | SHA256 / identity | Observed structure and result |
|---|---|---|---|
| Initial physical geography provider payload | `_ARCANA_EXTERNAL_SOURCES/r6/initial_world/r6run_85af40f36fcb86c23a3571744817780a28e22740f6eaa04ae432bfe7d21f7f65/R6_INITIAL_PHYSICAL_GEOGRAPHY.npz` | `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c`; 1,169,900 bytes | 14 arrays on 180×360 support. Required by the admitted T0 initializer; byte hash matches its governed source record. |
| T0 vector plate partition | `_ARCANA_EXTERNAL_SOURCES/r6/tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz` | `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab`; 5,681,184 bytes | 64,800 parent faces, five vertex coordinates per face, and 1,983 boundary records. Hash matches the tracked vector manifest. |
| B6N8-N T0 field package | `R6_T0_B_PANGAEA_LIKE_V2_FIELD_PACKAGE.npz` (repository root) | `39934c2c0c36aa168d850b02d88ca8a853febdb99915af9b7bb18fed6539a52e` | Hash matches the package identity in the admitted-support binding index; consumed by the existing provider audit. |
| B6N8-N admitted-support binding index | `docs/arcana/research/B6N8N_ADMITTED_SUPPORT_BINDING_INDEX.json` | `aaa571eb64b854656e70fdbb559377a76eb44afdb723080eb5471fd4b1663e00` | Provider audit verified admitted counts: 63,620 total, 14,258 continental. Pair 5:11 admitted cells are bound by exact support ID. |
| Property tuple binding registry | `docs/arcana/research/B6N8N_PROPERTY_TUPLE_BINDING_REGISTRY.json` | Read and semantically checked by the provider audit; it binds material/thermal classes. No separate digest is asserted in this report. | The two selected profiles share material-role ordering; each profile has 73 finite temperature/depth nodes. |
| B4/B5 source set, boundary and kinematic evidence | Tracked source documents plus existing `outputs/r6_b4_plate_kinematics_qualification/` artifacts, read through `load_b5_sources` | Source-set identity `2ffc49375f9e59c7f7abf9140ba7041c64ad0deb0a182df9242184a55ce76109`; kinematics semantic identity `50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`; kinematics artifact `0f598c86b397a293b5983ace21cef18540fc47ad56fd5dc58d483220789bc6d2` | Existing source/manifest lineage and B4 qualification checks passed. The report does not repeat every B4 manifest member or claim an external signature. |
| Pair-event eligibility census | `R6_T0_EVENT_ELIGIBILITY_CENSUS_V3.json` | `e1f5d77443e7f0898b6100a84d36ce2961e94b580df139896e73804b85968f7e` | Pair 5:11 is `ELIGIBLE_QUIESCENT`; this is not activation authority. |
| Exact parent-cell/plate mapping | Derived by the provider audit from the vector partition and admitted support | Mapping identity `b8d57495bc6e196a0b9fe7afd466079bebd97d0f63baafe232f215e45897a09f` | Exact unique-complete 64,800-cell join. No interpolation or support resampling. |

Provider-backed result details:

- Checkout identity checked by the API: branch `r6/si1-bandwidth-f2av`, HEAD `dde79ebe4d26ab7b21eff08245fc83330239c0bc`.
- Selected boundary: `R6BND-T0-3eb57747e6f0a3f3305f`, parent edge row 91, column 28, axis EAST.
- Ordered pair: 5:11. Support IDs: `R6G1D-R091-C029` (plate 5) and `R6G1D-R091-C028` (plate 11); both are admitted continental `CONTINENTAL_HOT_EXTENDED` support.
- The pair census has 15 boundary rows, 8 eligible sections, and status `ELIGIBLE_QUIESCENT`.
- Existing Euler adapter result: signed engineering extension `0.11467052868814648 m/year`. It remains a frozen instantaneous engineering input, not a physical rift law.
- Initial profiles: 73 nodes per side; finite and material-role consistent under the provider checks.
- No canonical state was accessed or changed by the preflight.

## Intermediate trajectory sampling

The existing endpoint/checkpoint artifacts were insufficient by themselves for the INT-1 retention comparison. The bounded correction in this worktree adds an optional observer to the existing reduced kernel and records the initial state plus every completed numerical substep for the middle resolution factor (`0.0005`). It does not alter the kernel equations, forcing, duration, parameters, or the other resolution runs.

The new `DIAGNOSTIC_NUMERICAL_SAMPLES.json` is intended as a temporary comparison reference, not as persistent or canonical history. It contains support IDs, units, time, width, crust and lithosphere thickness, beta, accumulated strain, material coordinates, physical depth coordinates and temperature. No interpolation is used. The runner checks strictly increasing sample time and endpoint equality with all final state fields and derived depths.

Bounds and output accounting:

- At most 10,001 records per support, including the initial state.
- At most 73 profile nodes per support; the runner rejects a provider profile exceeding that limit before evolution.
- At most 20,002 total records and 226 binary64-valued entries per record (7 scalars plus 3×73-vector fields), or 4,520,452 numeric entries.
- A serialization sizing calculation using the fixed artifact schema, full record cardinality, and maximum-length finite binary64 decimal values produced 333,657,599 bytes for the sampled JSON. A 350,000,000-byte ceiling is proposed for that artifact; it is a run-output budget, not a scientific threshold. Other runner artifacts are small relative to this sample artifact. This is a conservative format-derived estimate, not an observed run size or RSS measurement.
- The Python sample object graph and JSON encoding peak memory are not measured. A 2 GiB process working-set ceiling is proposed as an operator-monitored stop threshold for this one local run, not an OS-enforced limit, not an RSS prediction, and not a resolution of `RESOURCE_2GB_SCOPE_UNRESOLVED` in the ShellSet workstream.

Focused offline verification after the sampling change: 59 passed, 0 failed, 0 skipped across INT0A pipeline, functional-development, spatial-support and T0 initializer tests. Python 3.12.10, NumPy 2.3.5, pytest 8.4.2. Provider-backed audit was separately executed twice and passed. `py_compile` and `git diff --check` passed. No trajectory integration was executed.

## Proposed finite execution contract — authorization required

| Item | Proposed setting |
|---|---|
| Environment | Local Windows CPU; Python 3.12.10, NumPy 2.3.5; repository root; explicit governed `ARCANA_EXTERNAL_ROOT` below. |
| Process/CPU | One Python process; 12 logical processors were visible, but this run is single-process and does not request parallel workers. |
| Wall time | 15 minutes operator-monitored maximum. This is a stop budget, not a measured runtime. Provider audit took about 22 seconds; the focused suite took 32.60 seconds, neither is a candidate-run benchmark. |
| Memory | Stop if process working set reaches 2 GiB, polled by the operator. No OS-enforced process memory limit is currently configured/attested. At preflight, Windows reported 34,284,072,960 total and 7,662,350,336 available physical bytes (77% load); these are a point-in-time host reading, not process budget or run measurement. |
| Output | New path `outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01`; confirmed absent at preflight. Stop if directory output exceeds 512 MiB. The sample artifact format-derived ceiling is 350,000,000 bytes. |
| Stop conditions | Any provider/hash/branch mismatch; wrong support or nonfinite state; more than 10,001 samples/support or more than 73 nodes; kernel invariant/replay failure; process working set ≥2 GiB; wall time ≥15 minutes; output >512 MiB; or any attempted canonical publication. Preserve any partial new directory as failed/non-authoritative; never overwrite or clean it. |
| Forbidden | Fair, MPI, ShellSet, Solver, DGBSV, factorization, WORLD_HISTORY access/write, canonical event/T1/T2, post-rift evolution, parameter/scenario substitution. |

Exact proposed PowerShell command sequence, from the repository root:

```powershell
$env:ARCANA_EXTERNAL_ROOT = 'F:\corsiiiuu\Magistrale\Arcana\ArcanaWorld\_ARCANA_EXTERNAL_SOURCES'
$env:PYTHONPATH = 'C:\Users\jose_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\Lib\site-packages;src'
python --version
python -c "import numpy; print(numpy.__version__)"
python scripts/r6_functional_development_t_f2b.py --repository-root . --expected-branch r6/si1-bandwidth-f2av --output-relative outputs/r6_functional_development/INT0B_TF2B_5_11_dde79ebe_20261013_01
```

The execution must be performed only after the bounded correction commit is present locally, its branch/HEAD and provider hashes are rechecked, the output path remains absent, and the user explicitly authorizes this exact scope. The simple runner command does not itself enforce an OS memory/time quota; those proposed stop limits require active operator monitoring. If active monitoring cannot be provided, do not run.

## Provenance and limits

This preflight establishes that the existing provider audit can resolve and validate its governed inputs in this Windows environment at the stated checkout. It does not prove those external files will remain unchanged later; the runner must repeat its validation at execution time. It does not produce a candidate trajectory, output manifest, execution duration, or process peak memory. The material/scenario profile is an existing reference engineering scenario, not a world-authorized rheology selection. The 1,000-year frozen-driver computation is engineering-model behavior only and cannot establish real planetary evolution or geological activity.

Next action: obtain explicit authorization for the exact bounded noncanonical run above. Until then, `INT0B_PROVIDER_INPUTS_VERIFIED__EXECUTION_PENDING_AUTHORIZATION` remains the current outcome.
