# B6N4-R1 — Second timestep readjudication

## Decision

**`BLOCKED_B6N4R1_RELEVANT_AUTHORITY_UNRESOLVED`** for the complete requested
output family `RESTRICTED_POST_EVENT_PLATE_LOCAL_RIGID_GEOMETRY_AND_KINEMATICS`.
The evidence establishes a finite model-use *upper bound* of 8,214.051909111062
years, but does not establish a positive guaranteed interval before the
unbounded topology/interface/support and rift-process dependencies. The bound
is not an event-free claim and is not the actual nearest limiter. No scoped
continuation is authorized because dependency isolation is not proven.

This readjudication uses source baseline `d3128fca0f6bd812298544768dbac0ef74dcca75`
and final B6N4-A policy evidence from source `5430d09dfd6f3cc5f1ad5d6db36b8fece6b30ab3`.
The deterministic runner emits the machine-readable closure to a caller-selected
output path. The retained qualification copy is in external evidence bundle
`B6N4R1/d3128fca0f6bd812298544768dbac0ef74dcca75`; its
`EVIDENCE_CONTENT_SHA256.txt` SHA256 is
`5e74841664afac30eb0402b84503ad2225917e39ece1a5576ca7ce5d1abe4d86`.

## Dependency closure

| Candidate | Relation to requested output | Time/impact and isolation finding | Result |
|---|---|---|---|
| `GENERIC_TOPOLOGY_EVENT_COVERAGE` | Required: plate geometry/topology identities are part of the requested candidate | B6N4-A impact bound UNKNOWN; dependency isolation NOT_PROVEN; earlier invalidation time UNKNOWN | Global blocking dependency |
| `JUNCTION_CONSISTENCY` | Relevant but non-limiting for this output: preserve set-valued junction identity/incidence; do not claim positional accommodation | Physical compatibility remains UNKNOWN. B6N4-A explicitly says the restricted rigid-kinematic output alone is not thereby invalidated | Does not independently limit this request |
| `MECHANICS_REQUIREMENT` | Not applicable: stress, strain, fault accommodation, and rheology are not requested | B6N2 limits this output to rigid geometry/kinematics | Does not block |
| `NEXT_RIFT_PROCESS_EVOLUTION` | Required to establish continued validity of the active rift-context model | Activation authority is zero-duration only; no next predicate, threshold, opening law, time bound, or process/output isolation is governed | Authority blocker |
| `PLATE_INTERFACE_EVENT_PREDICATES` | Required: interface identity/connectivity is frozen in the requested output | No post-event detector or impact bound; dependency isolation NOT_PROVEN; earlier invalidation time UNKNOWN | Global blocking dependency |
| `SOURCE_TEMPORAL_VALIDITY` | Source-provenance limit, distinct from successor-model authority | T0 Euler source remains instant-only and UNKNOWN beyond 210 Ma. B6N2 separately authorizes a restricted successor model without extending that provenance | Does not independently block successor-model use |
| `SUPPORT_MEMBERSHIP_VALIDITY` | Required: preserve the POST_EVENT support and plate-local representations | Validity is tied to ungoverned topology/interface events; no impact bound, positive interval, or isolation proof | Global blocking dependency |
| `SUCCESSOR_MODEL_SCOPE_REVALIDATION` | Applicable authorized finite cap | B6N3-A requires model revalidation by 8,214.051909111062 years; it does not bound earlier UNKNOWN events | Upper-bound candidate only |
| Asynchronous domains | Not applicable to the tectonic kinematic output | They are preserved and not consumed by this output | Does not block |
| Rigid-rotation numerical stability | No separate governed numerical limiter for the exact rigid-rotation operation | B6F identifies no intrinsic ODE stability bound or angular-accuracy threshold | Does not block |

The UNKNOWN event occurrence is not treated as proof that an event occurs
before the model cap. The blockers are the missing impact/time bounds and
unproven causal isolation for dependencies required by the requested output,
plus the missing authority for continued rift-process evolution. Under the
qualified B6N4-A policy, `NOT_PROVEN` dependency isolation cannot be converted
into a scoped positive continuation.

## Source and model authority

The original 210 Ma Euler source remains `INSTANT_ONLY`; its provenance is not
extended. The B6N2 contract is an independent, restricted successor-model
authority beginning at the POST_EVENT state. B6N3-A adds a finite revalidation
cap. Together they govern the model candidate, but the cap itself does not
resolve the earlier topology, interface, support, or rift-process boundaries.

The six junction relations remain set-valued, with no unique owner or physical
accommodation law. This readjudication preserves those UNKNOWN semantics and
does not invent a junction velocity, opening law, event calendar, or event-free
interval.

## Timestep contract and gates

`R6_SECOND_DT_AUTHORIZATION_AFTER_RIFT_V1.json` remains unchanged. No V2 is
needed because this result changes no timestep permission: V1's fail-closed
rule still applies to the relevant unresolved prerequisites. The nearest
limiter is not established; the 8,214.051909111062-year candidate is retained
only as the model-scope upper bound. Therefore `dt2` is not authorized or
selected, `target_age_ma` is null, and B6O is not authorized.

Canonical WORLD_HISTORY was inspected read-only. A content digest over all 46
files in the canonical store was `82e6ba7e384cf75f4e1627f68ac13762a936cc4266a90718bd40cc696768385f`
both before and after the R6 regression run; the store contained 1,275,143
logical bytes. The physical age keys remain
210.0 Ma and 209.97287659484368 Ma; PRE_EVENT and POST_EVENT retain their
identities and shared payload SHA256
`9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a`. The
canonical store tree digest before the regression run is recorded in the JSON
evidence and must match after qualification.

```text
SECOND_DT_SELECTED = false
target_age_ma = null
T2_CREATED = false
canonical physical epochs = 2
mechanics_executed = false
forward_propagation_executed = false
topology_transition_executed = false
```

No WORLD_HISTORY record was opened through a mutating store lifecycle; the
qualification reads the canonical store files and committed view directly.

## Validation

The focused B6N4-R1 tests passed (**9 passed**); the targeted B6N1/B6F/B6H/
B6I/B6J/B6K/B6N4-A/B0-B/B0-C/B0-E regression set passed (**103 passed**);
the complete active R6 suite passed (**494 passed**). `py_compile`, JSON
validation, and `git diff --check` also passed. These checks qualify the
readjudication procedure and preserve the blocked scientific outcome; they do
not authorize propagation.
