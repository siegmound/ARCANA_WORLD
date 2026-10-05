# B6N4-A — Event impact and state significance

## Decision and scope

The general policy is `R6_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY_V1`.
It formalizes **event is not state**: an event ledger entry does not itself
require a new WORLD_STATE. Significance is evaluated against an identified
spatial/temporal resolution, represented domains, requested outputs, and
dependency scope. No global scalar threshold or unguided physical law is
introduced.

This is a policy qualification, not timestep authorization. The seven
adjudications are retained in the development evidence bundle
`B6N4A/4ab6655bf04c7497207e6cf937adf66bd905815f/B6N4A_SEVEN_UNKNOWN_ADJUDICATION.json`
under `ARCANA_WORLD_QUALIFICATION_EVIDENCE`; this is not the final B6N4-A
attestation. Unbounded impacts remain UNKNOWN. No row asserts event absence. A missing or
unknown source/model authority is checked before impact significance and
cannot be bypassed by a subresolution assessment.

## Record and uncertainty semantics

Existing WORLD_HISTORY event, state, checkpoint, and refinement records are
sufficient; no parallel store or schema is needed. Event records and state
boundaries remain distinct. A canonical state may contain explicit
`SupportClass.UNKNOWN` with a null value and uncertainty/provenance; canonical
means governed best reconstruction at declared scope/resolution, not certainty.
Refinement re-evaluates significance at its own resolution.

Actual event subjects use occurrence `OCCURRED` or `UNKNOWN`. Non-event
authority/scope horizons use null occurrence rather than being coerced to
`UNKNOWN` physical occurrence. Local/regional impact permits consideration of
unaffected scopes only when dependency isolation is proven. If dependency
extent is unproven, the affected model/domain family fails closed at global
scope; this does not authorize unrelated domains.

The evaluator is deterministic and classification-only. It does not predict
events, infer their absence, publish state/checkpoints, select `dt`, or
authorize propagation.

## Seven B6N4 horizon adjudications

| Horizon | Occurrence / authority interpretation | Significance | Blocked scope and remaining gap |
|---|---|---|---|
| `GENERIC_TOPOLOGY_EVENT_COVERAGE` | Event occurrence UNKNOWN; support/topology uncertainty | `INSUFFICIENT_IMPACT_BOUND` | Tectonic/topology-dependent family; no complete event coverage, impact envelope, or proven dependency closure |
| `JUNCTION_CONSISTENCY` | Not an event occurrence; six junction identities do not govern response/tolerance | `INSUFFICIENT_IMPACT_BOUND` | Junction/topology-dependent outputs; response, tolerance, accommodation and causal isolation unresolved. Current restricted rigid kinematics alone is not thereby invalidated |
| `MECHANICS_REQUIREMENT` | Non-event scope horizon; mechanics is not requested by restricted geometry-only kinematics | `NOT_APPLICABLE` for this request | If mechanics outputs are later requested, their authority/trigger remains unresolved |
| `NEXT_RIFT_PROCESS_EVOLUTION` | Event occurrence UNKNOWN; model authority absent for further rift evolution | `AUTHORITY_BLOCKED` | Rift/topology-dependent family; no governed predicate, threshold, opening law, time constant or dependency closure |
| `PLATE_INTERFACE_EVENT_PREDICATES` | Event occurrence UNKNOWN; interface/topology uncertainty | `INSUFFICIENT_IMPACT_BOUND` | Interface/topology-dependent family; no post-event detector, impact envelope, or positive interval bound |
| `SOURCE_TEMPORAL_VALIDITY` | Non-event source-authority limit; source interval remains UNKNOWN | `AUTHORITY_BLOCKED` for claims extending source validity | Source-provenance claim scope. B6N2/B6N3A separately govern only their restricted successor-model use and do not extend source provenance |
| `SUPPORT_MEMBERSHIP_VALIDITY` | Non-event support-validity horizon; no independent support-change predicate | `INSUFFICIENT_IMPACT_BOUND` | Support/topology-dependent family; no independent predicate or dependency closure |

The machine-readable adjudication includes the source statuses/reasons, each
authority class, resolution context, dimension evidence, classification,
scope, and deterministic result digest. UNKNOWN remains UNKNOWN; no threshold,
event frequency, boundary type, or geological behavior was invented.

## Qualification and preserved gates

The qualification source commit is `4ab6655bf04c7497207e6cf937adf66bd905815f`;
the policy/evaluator/test additions are in the working tree and are not
committed. Focused policy tests: **11 passed**. Complete active R6 regression:
**485 passed**. These tests include preservation of explicit UNKNOWN through a
temporary WORLD_HISTORY write/query/replay path and ensure non-event horizons
do not acquire physical event-occurrence values.

No frozen B6N1/B6N2/B6N3-A/B6N4 V1 contract was edited. No canonical history
write, mechanics, ShellSet, OrbData mechanics, forward propagation, or topology
transition was performed. Canonical physical epochs remain 2.

```text
SECOND_DT_SELECTED = false
target_age_ma = null
T2_CREATED = false
canonical physical epochs unchanged = true
mechanics_executed = false
forward_propagation_executed = false
topology_transition_executed = false
```

**Verdict:** `PASS_B6N4A_EVENT_IMPACT_AND_STATE_SIGNIFICANCE_POLICY`.
This does not revise frozen B6N4 V1 or authorize `dt2`. Any B6N4-R1
readjudication requires a separate stage and authorization.
