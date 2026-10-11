# R6 INT-0A — first multi-provider integration

**Decision:** `INT0A_INTEGRATION_CODE_READY__NONCANONICAL_RUN_NOT_YET_EVIDENCED`

**Scope:** offline integration code and bounded tests only. No new T-F2B evolution run, Fair job, ShellSet, MPI, Solver, or canonical history write was performed. This report records code readiness, not an executed trajectory or scientific qualification.

## Existing capabilities and evidence

| Component | Numerical role and contract | Support/time and provenance | Scope, limits, tests/evidence |
|---|---|---|---|
| `functional_development.py` | Materializes an admitted continental T0 profile as `T0Profile`; converts it to `ReducedState`; provides the existing `pure_shear_thermal_step` kernel and a separate fixed-geometry thermal profile kernel. | Profile is per exact support ID at T0 = 210 Ma; units and material properties are carried in the typed profile. | The pure-shear kernel is a reduced engineering model. It does not provide lateral thermal coupling or prove geological validity. Existing development tests cover profile and kernel behavior. No equations were copied into the new orchestrator. |
| `functional_spatial_support.py` | `audit_pair_5_11()` checks the exact face/plate join, admitted two-sided continental cells, T0 Euler kinematics, event census, and selects the lower-median eligible non-junction extension edge. It materializes a profile on each selected side. | Two adjacent 1-degree parent-cell supports; ordered plate pair 5:11; T0. Returns source, mapping, vector, field-package, support-index, and event-census identities. | The selected edge is an engineering reference section. `Xe` is parent-cell-center spacing, not Buck physical `Xe`. Provider audit requires external source payloads. |
| `plate_support_adapter.py` | Supplies B5 plate, boundary, node and junction support using exact topology joins; no temporal transition law. | T0 plate identities and shared-support topology; reads the governed B4/B5 inputs and external vector payload. | Reused transitively by the spatial audit. Existing spatial tests cover unique joins, signed velocity and fail-closed unknowns. |
| `pre_orbdata_t0_initializer.py` | Binds material classes/properties and initialization authority for admitted columns; includes a read-only support preflight and a separate synthetic-column evaluator. | Exact admitted support; T0 column profile and property registry/config identities. | It authorizes an initializer contract, not arbitrary history before T0 or a full planetary thermal history. Full provider path depends on external field/vector payloads. |
| `b6k_candidate.py` | Candidate geometry from finite Euler rotation over its own fixed interval. | B6 candidate geometry, pair 1:3 context. | Not the 5:11 continental thermal trajectory; no splice is made. Existing isolated-candidate tests are separate. |
| `b6n8a_shadow.py` | Multi-resolution diagnostic shadow for conditional plate-local motion, querying B0 state through `HistoryQueryService`/`HistoryStore`. | B6 post-event pair 1:3 and its exact supported state. | Diagnostic-only; does not provide physical rift transition authority and is not executed by INT-0A. Its existing attestation remains limited to its own scope. |
| T-F2B runner `scripts/r6_functional_development_t_f2b.py` | Already performs the actual 5:11 spatial audit, consumes both T0 profiles and the selected Euler `Ux` in the reduced thermal kernel, compares three substep fractions, and checks deterministic replay/restart and area conservation. | 1,000-year engineering window with frozen instantaneous forcing; separate candidate output directory. | This was an existing integration experiment, not repeated here. The INT-0A change extracts its output-to-input binding into a tested package API and adds B0-shaped candidate state/checkpoint/replay records and a trajectory artifact. |
| B0 HistoryStore/query/replay/refinement | Typed immutable state, forcing, checkpoint and replay-recipe contracts; append-only transactions, read-view queries, closed-input replay, and isolated refinement/reconstruction. | Identity- and support-bound records; persisted history when explicitly used. | INT-0A serializes typed B0 domain-state/checkpoint/forcing/replay records into a separate candidate bundle. It does **not** append to, query, or mutate canonical `HistoryStore`; the replay recipe is a descriptor and is explicitly not registered as executable HistoryStore closure. Refinement is not used for this two-cell slice. |

T-F2B already integrates providers on 5:11. INT-0A does not rename that experiment or claim the first numerical execution. Its contribution is a reusable, fail-closed binding layer with direct tests showing that changing the upstream forcing changes downstream width and changing an upstream profile changes downstream temperature.

## Implemented integration

Added `src/arcana_worldsim/r6/int0a_pipeline.py` with:

- A strict adapter from the spatial audit's profile mappings to the existing `T0Profile`, without interpolation or resampling.
- A repository-audit entry point fixed to ordered pair 5:11 and a separate fixture-only entry point that requires an explicit `SYNTHETIC_FIXTURE_ONLY` marker.
- Binding checks for exact selected support IDs, two-sided admitted continental material, quiescent pair census (not activation authority), finite positive signed Euler extension, an orthonormal section frame, radius/width, provider SHA syntax, source branch/commit, T0 profile units/cardinality/material roles, and the admitted initializer's configuration lineage on the repository-authority path.
- `advance_pair()`, which sends those exact profiles and forcing to the existing `pure_shear_thermal_step`; it adds no scientific equation.
- A candidate trajectory document with T0/candidate time, exact support IDs, state fields and deltas, provider/source/config identities, engineering forcing frame, event candidates explicitly UNKNOWN, uncertainty, B0 typed state/checkpoint/forcing/replay descriptors, and explicit noncanonical scope.
- A new-directory candidate-bundle writer with deterministic JSON, readback/hash checks and overlap/overwrite refusal for caller-declared protected roots. The runner's established multi-artifact staging directory remains under `outputs/r6_functional_development`; it refuses overwrite and writes its manifest last.

The existing runner now calls the shared orchestration API, defaults `--expected-branch` to `r6/si1-bandwidth-f2av`, and includes `CANDIDATE_TRAJECTORY.json` in the run manifest. `WORLD_HISTORY` is not read or written by the new module. B0 record types are serialized locally only; the candidate bundle is not published to a `HistoryStore`.

## Support and case boundary

The selected integration case is the existing T-F2B continental plate pair **5:11**, with two exact admitted parent-cell supports, thermal profiles at 210 Ma and T-F2B's signed Euler extension in the selected section-normal frame. The extension is frozen for the existing engineering-window configuration. No interpolation is introduced.

The B6 rift pair **1:3** remains distinct. Neither its geometry candidate nor its post-event shadow is combined with 5:11. The T-F2B event census reports quiescence only within that census scope and is not activation or event-transition authority.

## Output contract and staging

The candidate schema is `ARCANA_R6_INT0_NONCANONICAL_CANDIDATE_V1`. T-F2B output is a new directory below `outputs/r6_functional_development` containing its existing audit, section/profile, convergence, replay/restart and run-result artifacts plus `CANDIDATE_TRAJECTORY.json` and `CANDIDATE_MANIFEST.json`. Existing destinations are refused; no output directory was created in INT-0A.

The trajectory stores per-support initial/candidate reduced fields and deltas, exact support/time identifiers, signed forcing/frame, provider identities, source branch/commit, configuration identity, uncertainty and UNKNOWN event status. B0-compatible records have their own deterministic identities. Checkpoints remain `CANDIDATE_NONCANONICAL`; replay is marked `DESCRIPTOR_ONLY_NOT_REGISTERED_IN_HISTORYSTORE`. The manifest hashes the candidate artifacts and is written last. A write/readback check detects ordinary incomplete writes; this is not a claim of durable storage or atomic multi-file publication.

## Validation performed

Bounded command on Windows, using the installed pytest and the bundled NumPy path, with a fresh writable `--basetemp`:

```text
python -m pytest -q --basetemp <fresh-writable-temp> \
  tests/test_r6_int0a_pipeline.py \
  tests/test_r6_functional_spatial_support.py::<five selected offline regressions> \
  tests/test_r6_functional_development.py::<two selected offline regressions>
```

Result: **20 passed, 0 failed, 0 skipped**. INT-0A tests verify binding, downstream sensitivity to changed forcing/profile, restart determinism, rejection of wrong pair/support/provenance/frame/event scope, fixture-only separation, B0 record round-trip, deterministic candidate bytes, protected-root rejection and overwrite refusal.

An earlier broader attempt to execute provider-backed spatial tests could not complete because the required external payload `../_ARCANA_EXTERNAL_SOURCES/r6/initial_world/.../R6_INITIAL_PHYSICAL_GEOGRAPHY.npz` is unavailable in this checkout; that attempt also encountered a Windows pytest temporary-directory permission problem. The temporary-directory issue was avoided with a fresh explicit `--basetemp` for the bounded suite. No claim is made that the real provider audit passed in this environment.

`py_compile` passed for the new module, modified runner and test module. UTF-8/LF and `git diff --check` passed in final local verification. No Fair compiler/runtime evidence is relevant or newly produced.

## Remaining UNKNOWN and limits

- The real T-F2B provider audit and candidate execution were not run because the external payload is unavailable here. The current implementation's repository-audit path remains dependent on that governed input and its hashes.
- The T0 reference profiles and material configuration are admitted engineering inputs; their use does not establish a complete physical history or geological validity through the interval.
- The frozen 5:11 Euler driver is an engineering scenario. No evolving kinematic provider or temporal validity evidence is added.
- Event absence/activation, a physical cross-section, physical `Xe`, sub-cell support, lateral thermal coupling, uncertainty distributions, and B6N8-R real-support roster remain unresolved or outside the model.
- B0 schemas are reused, but no candidate record is persisted to `HistoryStore`, queried, refined, or independently replayed through B0's closed-input service. The emitted replay recipe is a descriptor until its forcing/state/provenance closure is registered and a replay adapter is bound.
- Deterministic byte identity is scoped to same code, input and runtime; cross-runtime bitwise equivalence is not claimed.
- This work does not resolve any F2A-V operator, numerical acceptance, Solver, SI1 resource, mechanics or canonical-history gate.

## INT-0B proposal

The next task is one bounded noncanonical execution of the existing T-F2B 5:11 runner, after a separate authorization is granted. Configuration to review before that authorization:

- Repository branch/commit: `r6/si1-bandwidth-f2av` at the reviewed commit; invoke with `--expected-branch r6/si1-bandwidth-f2av` explicitly.
- Existing provider case: exact lower-median eligible non-junction 5:11 section chosen by `audit_pair_5_11`; two admitted T0 profiles at 210 Ma; no B6 1:3 inputs.
- Scenario: existing 1,000-year frozen Euler engineering driver and resolution fractions `0.001`, `0.0005`, `0.00025`; this is a reproducibility/engineering run, not a scientific history.
- Inputs: restore the required external initial-world payload into its governed location, verify all provider-manifest hashes and source branch/head, and retain a read-only input inventory before execution.
- Output: a fresh, operator-reviewed directory such as `outputs/r6_functional_development/INT0B_TF2B_5_11_<unique-run-id>`; never reuse the legacy T-F2B path or any existing output. Capture exact command, Python/NumPy versions, elapsed time, peak process memory if available, output bytes, exit status, and manifest hashes.
- Stop/acceptance: refuse existing paths, fail on source/input mismatch or nonfinite state/invariant/replay mismatch, preserve any partial output as non-authoritative, and do not write canonical `WORLD_HISTORY`.
- Separate authorization must explicitly cover the noncanonical computation, input access, CPU/time/memory/output budget, destination, and stop conditions. INT-0A itself grants none of these execution permissions.

**Next action:** prepare/review the finite INT-0B execution configuration and request its distinct authorization. No further open-ended architecture-design phase is proposed.

## Preserved gates

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
