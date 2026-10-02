# ARCANA WORLD — PRE-B0 C0-B Authority and Dependency Audit

**Audit date:** 2026-10-01
**Scope:** static, read-only repository audit at `2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`.
**Purpose:** inform a controlled consolidation before B0; this report authorizes no deletion or scientific change.

## Baseline and evidence limits

- Observed branch: `r6/t0-authorial-realization-materialization`; observed HEAD: `2aa6a8e4d8edbd7796c5c2dea4c8d0d90f042264`; worktree was clean.
- Inventory baseline from C0-A: 50,140 tracked files, approximately 2.92 GiB logical size, 1,576 tracked root files.
- The requested `git fetch origin` could not write `FETCH_HEAD` in this managed worktree. The locally cached origin ref matched the supplied commit, but a fresh remote check was not possible. Creation of `r6/pre-b0-repository-consolidation` was also denied by `.git` write permissions. No branch or repository file was changed during those attempts.
- This is a targeted static graph, not proof that every dynamic path, external workflow, historical replay, or user script has been found. “No consumer found” means no in-scope static R6 consumer was found, not that a family is safe to delete.

## A. Repository dependency graph

```text
initial_world generators / canonical inputs
  -> R6 state and T0 materialization
  -> history store, checkpoints, events, provenance
  -> query / consumer / refinement interfaces

canonical R6 physical and boundary authority
  -> physical-domain and boundary adapters
  -> heat-flow / thermal / FEG materializers
  -> R6 FEG + runtime package + manifests
  -> vendored ShellSet ARCANA runtime loader

scripts (builders, validators, qualification harnesses)
  -> source modules + governed input artifacts
  -> generated evidence, payloads and reports

tests
  -> core contracts, deterministic materialization, parser/source contracts,
     geometry/topology and ShellSet integration boundaries
```

| Component | Consumers | Builders / producers | Tests / manifests | WH0 contribution |
|---|---|---|---|---|
| `r6/initial_world/` | T0 materialization and history-facing code | `scripts/r6_materialize_initial_world.py` and related validation/materialization runners | `test_r6_initial_world.py`, initial-world artifacts/manifests | Initial state, deterministic regeneration, refinement starting point |
| History core (`store`, `state`, `temporal`, `checkpoint`, `query`, `provenance`, `registry`, `consumer`, `bootstrap`) | R6 callers and tests; the test suite imports these APIs directly | bootstrap/materialization runners create envelopes and records | `test_r6_bootstrap_core_wave1.py`, `test_r6_world_history_core.py`, `test_r6_wave2_binding_artifacts.py` | Direct B0 foundation: immutable history records, events, provenance, query and branch/refinement structures |
| Physical / boundary R6 (`physical/`, `physical_domain_t0.py`, `physical_boundary_accommodation.py`, `planning.py`) | T0 binders, geometry and boundary diagnostics | `scripts/r6_bind_*`, `r6_adjudicate_*`, junction and geometry builders | corresponding physical-domain, boundary, junction and planning tests; canonical manifests | Supplies physical state and causal input contracts to later history checkpoints |
| T0 specialist materialization | authorial T0 artifacts and specialist runtime inputs | `scripts/r6_t0_authorial_materialization.py`, `scripts/r6_materialize_initial_world.py` and related builders | T0 manifests/reports and materialization tests | T0 state and provenance; preserve source authority and deterministic builders |
| PRE_ORBDATA + `shellset_mesh/` | FEG/runtime package materialization and ARCANA ShellSet source integration | `r6_pre_orbdata_materialize_*`, mesh adapter and qualification scripts | PRE_ORBDATA/S1A/S1B contracts, tests, FEG/package manifests | Potential geological-state provider/input to WH0; currently specialist integration and bounded qualification, not general history engine |
| Vendored `external/ShellSet-v1.1.0/` | ShellSet executable build and configured FAIR runs; ARCANA-specific path reads FEG/runtime package and runtime marker | upstream source plus governed ARCANA successor patch | source-contract tests, patches/provenance and FAIR evidence | Reusable specialist mechanics/provider candidate; this checkout's current qualification proves the runtime-loading boundary only |
| pyGPlates feasibility/mapping/topology | explicit diagnostic runners/tests | `scripts/r6_pygplates_*` | mapping/topology contracts and reports | Geometry/topology provider candidate; not yet bound as canonical dynamic authority |

### ShellSet qualification boundary

At this HEAD, the C0-B handoff reports `PASS_R6_S1B_PRODUCTION_RUNTIME_LOAD` for 64,442 expected nodes: FEG and runtime package validated/loaded, `ArcanaRuntimeIsLoaded=true`, `ArcanaShellsModeActive=true`, and failure latch false. This is evidence for the bounded runtime-load boundary. It does **not** qualify full ShellSet mechanics, authorize mechanics, T1, or forward evolution. Preserve that distinction in future documentation and artifact classification.

The FEG and runtime `.dat` are generated current inputs with matching manifests/hashes, not disposable build debris. The vendored source, governed patch and source/qualification provenance are required to understand or reproduce the integration; they are not independent canonical scientific state.

## B. Active R6 architecture

| Component | Runtime status | Authority | WH0 relevance | Decision |
|---|---|---|---|---|
| `store.py`, `state.py`, `temporal.py`, `checkpoint.py` | Core APIs exercised by R6 tests | ARCANA record/contract authority | History, events, checkpoint and branch substrate | `KEEP_RUNTIME`, `KEEP_REUSABLE` |
| `query.py`, `consumer.py`, `provenance.py`, `registry.py`, `bootstrap.py` | Core APIs exercised by tests and bootstrap flows | ARCANA identity/provenance/consumer contracts | Query, lineage, provider registry, bootstrap | `KEEP_RUNTIME`, `KEEP_REUSABLE` |
| `initial_world/` | Generator, validator, materializer and refinement paths have R6 tests/runners | Governed synthetic initial-world inputs and deterministic producer contracts | Initial checkpoint and selective refinement source | `KEEP_RUNTIME`, `KEEP_AUTHORITY`, `KEEP_REUSABLE` |
| `physical/`, `physical_domain_t0.py`, boundary modules | Active builders/tests and current R6 artifacts reference them | R6 physical contracts and source authority | Physical state, geometry, topology and future event input | `KEEP_AUTHORITY`, `KEEP_REUSABLE` |
| `t0_materialization/` | Specialist materialization and tests | T0 authorial configuration/provenance | State materialization and reproducible checkpoint source | `KEEP_RUNTIME`, `KEEP_AUTHORITY` |
| PRE_ORBDATA and `shellset_mesh/` | Materializers, validators and source integration are active | Current FEG/runtime contracts and governed package; qualification evidence is provenance | Geological provider candidate and future checkpoint input | `KEEP_AUTHORITY`, `KEEP_REUSABLE`, `KEEP_REFERENCE` |
| `pygplates_*` | Diagnostic runners/tests exist; engine registry says candidate/not bound | Diagnostic only | Possible future geometry/topology provider | `KEEP_REUSABLE`, `KEEP_REFERENCE`; no canonical promotion |
| `planning.py` engine registry | Imported by R6 planning tests | ARCANA retains scientific authority | Declares bounded interfaces and engine status | `KEEP_RUNTIME`, `KEEP_AUTHORITY` |

## C. Legacy adjudication

| Engine/family | Historical role | Current R6 role found | Future WH0 possibility | Classification and risk |
|---|---|---|---|---|
| NEMO | R3/R5 benchmark/reference engine, runners, evidence and tests remain | `NOT_BOUND` in the R6 engine registry; R6 planning names it as an external bounded calculation only | Possible independent climate/ocean comparison or refinement provider if inputs, temporal semantics and provenance are governed | `ARCHIVE_PROVENANCE`, `KEEP_REFERENCE`; deleting could break historical replay, benchmark tests or evidence reconstruction |
| Geonomics | Legacy ecological engine in R3/R4 multi-engine work and evidence | No R6 registry binding found; older orchestrator/tests and scripts still contain references | Possible population/ecology adapter, not an authority source by itself | `REVIEW_UNKNOWN`, retain history until older workflow dependencies are adjudicated |
| CDMetaPOP | Legacy population/demographic engine and bridge evidence | `NOT_BOUND` in R6 registry | Possible population provider after explicit state/forcing contracts | `ARCHIVE_PROVENANCE`, `KEEP_REFERENCE`; do not remove bridge/test provenance |
| SLiM | Legacy population-genetics runs and comparisons | `NOT_BOUND` in R6 registry | Possible bounded genetics/population provider | `ARCHIVE_PROVENANCE`, `KEEP_REFERENCE`; historical inputs and result evidence may be hard anchors |
| RangeShiftR | Legacy range-shift/biodiversity calculation | `NOT_BOUND` in R6 registry | Possible distribution/refinement provider under a future adapter contract | `ARCHIVE_PROVENANCE`, `KEEP_REFERENCE`; no R6 runtime binding was found |
| Madingley | Legacy ecosystem-model/reconciliation material | No R6 registry binding found; historical scripts/tests mention it | Potential ecosystem comparison only; no present provider contract | `REVIEW_UNKNOWN`, preserve until exact artifact and consumer links are mapped |
| BIOME4 | Legacy vegetation/productivity model | R6 registry explicitly retains a bounded role but says input gaps exist and production is unauthorized | Plausible WH0 vegetation/productivity provider after input closure | `KEEP_REFERENCE`, `KEEP_REUSABLE`; do not delete the integration/design material |

The engine registry enforces `scientific_authority="ARCANA"` for its entries. A listed engine role is an interface/status record, not evidence that the engine is currently bound, authorized, or executed by R6.

## D. Generated artifact analysis

| Family | Duplicate / reproducibility evidence | Authority and use | Adjudication |
|---|---|---|---|
| `outputs/` | Contains historical run output; at least one R3_36 NPZ exactly matches its consolidated copy by SHA256. Reproducibility varies by producer and external engine. | Historical results can be replay inputs, baselines, validation evidence or hard anchors; generated status alone does not negate those uses. | `REVIEW_UNKNOWN` by artifact family; inventory builder, input and consumer links before any deletion. |
| `local_runs/` | Run-local artifacts; some have scripts/manifests, while exact regeneration and current consumers vary. | May contain logs, intermediate data, external-engine outputs and provenance necessary to interpret results. | `ARCHIVE_PROVENANCE` or `DELETE_GENERATED` only after per-family reproducibility and consumer checks; no bulk delete. |
| `SIMULATION_RESULTS/` | README states files are copies from `outputs/` and `local_runs/`, originally SHA256-checked; manifest records original/consolidated paths. A sampled R3_36 replay copy still matches exactly (`67A21D79…AE3953C5`). | Consolidated catalogue is a discoverability layer; copied files are not automatically authority, but some are historical reference inputs/evidence. | Duplicate subset is a `DELETE_DUPLICATE` candidate only after confirming all current consumers and preserving manifest/provenance. Keep the catalogue/index until then. |
| Large R6 JSON, FEG, runtime package and diagnostics | Many have named builders and tests; some payloads are generated deterministically, but some reports also serve as governed evidence. | Current R6 contracts/manifests explicitly refer to key payloads and identities. | Keep current governed inputs/evidence and their builders. Do not apply blanket `DELETE_GENERATED`. |

The initial `SIMULATION_RESULTS/README.md` reports 863 copied files and a 100% SHA256 check at consolidation time. Current tracked count is larger than that snapshot, so the old count is not a complete current duplicate inventory.

## E. Protected list — DO NOT DELETE during consolidation

- `src/arcana_worldsim/r6/` and the R6 tests that define its contracts.
- Current R6 canonical inputs, authority artifacts, manifests, lineage/provenance and named builder scripts.
- PRE_ORBDATA contracts and scientific adjudications, the 64,442-node FEG/runtime package and manifests, plus their materializers and tests.
- `external/ShellSet-v1.1.0/src/`, the governed patch, input/configuration dependencies, license and qualification evidence. Keep stock reference inputs distinct from ARCANA authority; their presence does not make them ARCANA data.
- R6 initial-world and physical-domain payloads, plus source artifacts needed to regenerate them deterministically.
- Legacy tests, bridge scripts, model inputs and evidence that serve as regression anchors or reproduce a governed historical result, until that relationship is resolved.
- `SIMULATION_RESULTS` manifests and provenance links while any copied result remains in the catalogue.

## F. Cleanup proposal

1. **Wave 1 — safe metadata repair:** refresh the bootstrap/current-state/README and execution index at an explicitly chosen authoritative HEAD. Preserve existing scientific content and label historical stages clearly. Regenerate indexes from their checked-in builders, then validate record counts and hashes.
2. **Wave 2 — duplicate review:** reconcile `SIMULATION_RESULTS` manifests against `outputs/` and `local_runs/` using hashes and repository-wide consumer searches. Report exact duplicate groups; do not remove originals or copies in this audit wave.
3. **Wave 3 — archive:** group superseded R3/R4/R5 reports, handoffs, logs and benchmark evidence into provenance families only after linking each to its runner, test, hard anchor and authority references. Preserve path mapping and commit history.
4. **Wave 4 — generated-file removal:** remove only individually proven regenerable artifacts that have a maintained builder, complete source inputs, no active consumers and no authority/evidence role. Exclude current R6 payloads and qualification artifacts unless a successor is verified.
5. **Wave 5 — obsolete/deletion decisions:** decide per family after the previous waves and a clean full consumer audit. “No R6 import found” is insufficient proof of obsolescence.

## G. C0-B decision summary

- R6 World History core and its current tests/builders are direct B0 dependencies: retain.
- R6 physical/T0 and PRE_ORBDATA/ShellSet materialization are current upstream authority/provider surfaces: retain, while recording the bounded runtime qualification limit.
- pyGPlates and legacy engines remain candidates/references unless their R6 contracts explicitly bind them; none acquires ARCANA scientific authority.
- Large output volume is not itself the cleanup target. The main risk is losing provenance, historical replay anchors and discoverability while trying to reduce context load.
- C0-B establishes a staged cleanup plan; it does not establish that generated/duplicate files have been exhaustively enumerated or authorize their removal.

## H. Uncertainties

- Fresh remote state and requested consolidation branch could not be checked/created because `.git` metadata writes were denied in this managed worktree.
- Static search does not fully resolve dynamic paths, external scripts/users, or every historical replay dependency across 50,140 tracked files.
- Per-artifact reproducibility is not proven for whole `outputs/` or `local_runs/` families; engine execution may be version-, platform- or schedule-dependent.
- The exact duplicate subset in `SIMULATION_RESULTS/` needs manifest-wide hash reconciliation; the sampled matching pair is not a family-wide proof.
- Geonomics and Madingley need targeted legacy artifact-to-consumer adjudication before archive/delete decisions.

**C0-B outcome:** authority/dependency audit complete for the scoped R6 and engine families; cleanup implementation is not authorized by this report. The next safe stage is C0-C documentation/bootstrap design after review of this report and restoration of the requested branch workflow.
