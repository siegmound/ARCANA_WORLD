# B6N8-C — Reduced rift prototype comparison design

## Decision

Design source baseline: `b7d4c50b9f10021757ba45f984107c3e9447f03f` on the
currently checked out branch `r6/b6n8b-targeted-rift-model-research`. No
B6N8-C branch was specified in the request, so this design does not create or
switch branches. B6N8-B remains research evidence only.

**Recommendation: `PROTOTYPE_TRACK_A`.** Compare a Buck-style reduced
force/thermal/mode model against the requirements, but do not yet implement
it as ARCANA production code. Track A is the only direction with a located
published state-dependent mode criterion that plausibly adds process
information beyond B6N2 kinematics. It needs limited, explicitly governed
lithospheric thermal/material state and contains reduced force-balance
mechanics. Its criterion can request regime/interface/topology/support
reevaluation; it cannot determine topology or support outcomes.

Track B is `INSUFFICIENTLY_DEFINED` as a Tier-2 process model. Forward fault
growth studies found in the screen derive segment growth/linkage from
stress/fracture or discrete-element mechanics, while slip-to-length models
need slip supplied. Neither gives a defensible source for activating or
deactivating ARCANA's 71 segments from the current pair-level kinematics alone.
Do not construct a comparison implementation for Track B by assigning
arbitrary segment activation.

This is a **design**, not a model selection, prototype run, parameter choice,
or propagation authority. The machine-readable protocol is
[`B6N8C_PROTOTYPE_COMPARISON_DESIGN.json`](B6N8C_PROTOTYPE_COMPARISON_DESIGN.json).

## Controlled comparison question

Can a state-bearing, physically traceable model add process/regime
information that is not a re-expression of B6N2 motion, and expose that
information as conservative B6N6 requests for reevaluation?

The intended outputs are limited to:

- evolved model-defined process state;
- model-authorized process and interface diagnostics;
- model-scoped regime/validity predicates;
- conservative topology-reevaluation and support-reevaluation requests.

The model may not perform or claim plate splitting, plate creation, boundary
creation, junction rewiring, support reassignment, crust production, or final
breakup geometry. Predicate, event candidate and transition application
remain distinct. A model can ask ARCANA to stop/refine/re-evaluate; separate
authority must define any resulting graph or membership change.

## Track A — equation-level Buck dependencies

Buck's paper defines lithospheric force per horizontal position from
depth-integrated yield strength plus gravitational/buoyancy contributions.
The strength envelope takes the lesser of brittle-failure stress and
temperature-/strain-rate-dependent ductile flow stress. An applied finite
strain changes thermal structure, crustal thickness, strength and buoyancy.
The lower crust is allowed to flow under pressure gradients associated with
crustal-thickness variation. The paper then computes the net change in force
required for continued local extension. Increasing required force is assumed
to widen the extension zone; decreasing force is taken to favor continued
localization. Core-complex behavior additionally depends on lower-crustal
flow. This is a reduced force-balance/thermal mode model, not a nonmechanical
phenomenological scalar.

### FULL_DEPENDENCY_SET

1. **Geometry and initial condition:** lateral model width; lithosphere and
   crust thickness profiles; initial narrow extension zone and its width;
   initial crustal-thickness gradients; crust/mantle layer geometry.
2. **Thermal state/evolution:** initial temperature profile or an authorized
   way to construct it; surface and basal thermal boundary conditions;
   thermal conductivity/diffusivity; vertical advection from extension;
   radiogenic heat production and its vertical distribution; thermal
   expansion for buoyancy.
3. **Strength/rheology:** brittle failure/yield law and effective pressure
   assumptions; crust and mantle ductile flow laws and composition; strain
   rate; temperature and depth dependencies; strength envelope and its depth
   integral.
4. **Force/buoyancy bookkeeping:** crust/mantle density contrast, thermal
   density anomaly, gravity, crust-thickness anomaly, integrated lithospheric
   strength, thermal buoyancy force and crustal buoyancy force. The mode
   criterion depends on their combined force change, not one thickness or
   heat-flow scalar alone.
5. **Lower-crust flow:** Moho pressure gradient from spatial crustal-thickness
   variation; effective lower-crust viscosity/flow law; rheological
   temperature dependence; flow diffusivity or the spatial flow solution;
   advection/thinning of the crustal-thickness field. This contribution is
   causal to the paper's core-complex versus wide-rift distinction.
6. **Applied forcing and experiment:** prescribed extension velocity or
   strain-rate history, spatial deformation pattern, finite strain/time
   increment, initial zone geometry, and the assumed widening/localization
   response rule.
7. **Numerical scope:** thermal and thickness discretization, boundary
   conditions, stability/error behavior, force integration and criteria for
   comparing initial/final force.

These are dependencies of the published formulation, not a request to adopt
its Earth-specific tabulated values. Its original example includes particular
compositions, constants, strain rate, widths and strain increments. Those
are study setup choices and are excluded from ARCANA authority absent a
separate adjudication.

### MINIMUM_CAUSALLY_REQUIRED_SET

To preserve the published **force-change mode criterion**, a candidate must
carry enough state to recompute, after each forcing increment:

- the temperature/depth structure relevant to ductile strength and thermal
  buoyancy;
- the crust/lithosphere thickness structure relevant to thinning,
  buoyancy and the Moho pressure gradient;
- the applied extension/strain-rate state and spatial zone geometry;
- composition/constitutive parameters sufficient to calculate brittle and
  ductile strength and lower-crust flow;
- the derived components of force and the combined signed change in required
  extension force.

At minimum these inputs must be initialized before Track A can run: model
domain and initial thickness profiles; initial thermal profile and thermal
boundary/material configuration; lithosphere/crust composition and strength
law identity; gravity/density/thermal-expansion configuration; a defined
extension forcing mapped to the model domain; and the flow closure needed for
the targeted mode classes. Values may remain unknown until governed; no
default Earth values fill gaps.

### POSSIBLY_REDUCIBLE_SET

- A full temperature field might be replaced by a reduced thermal basis or
  sufficient profile coefficients only after showing it preserves ductile
  strength, thermal buoyancy and force-change signs over the intended scope.
- The lower-crust flow PDE might be replaced by the paper's effective
  diffusivity closure only for its justified rheological domain. Removing the
  effect entirely changes core-complex predictions and is not equivalent.
- Depth-integrated force components can be stored as diagnostics and
  recomputed from physical state, rather than persisted as independent state.
- A local 2-D strip could be compared before a larger model if its boundary
  conditions and dependency buffer are explicit. It cannot claim junction or
  along-strike fault behavior that it does not resolve.
- Composition may be represented by material-family IDs plus governed
  property bundles, but those IDs are discrete and cannot be numerically
  averaged.

### UNSAFE_TO_REMOVE_SET

For the full Buck mode criterion, it is unsafe to remove temperature/thermal
evolution, thickness geometry, constitutive strength dependence, applied
strain-rate/amount, density/buoyancy terms, or lower-crust flow while still
claiming the same widening/localization/core-complex modes. Omitting lower
crust flow specifically suppresses the published core-complex mechanism.
Collapsing all causes into a fitted scalar without causal-preservation tests
would be a different model. The original paper itself identifies incomplete
coupling between flow and thermal calculations as a limitation; that argues
for a model-form uncertainty term, not for treating the simplified closure as
exact.

## Track B — reduced fault/segment process

The best-developed forward examples found for evolving rift fault networks
use local heterogeneities and resulting stresses in brittle/ductile or
discrete-element crust to nucleate, propagate, interact and link faults.
They are physically informative but mechanics-bearing and generally evolve
network geometry beyond a fixed set of 71 line segments. Fault displacement-
length/fracture models can explain how growth scales with displacement, but
they require slip or stress/loading as the driving process. The screened
sources do not provide a validated, generally transferable low-order law that
takes ARCANA pair-relative kinematics and determines segment activation,
deactivation, interaction and localization without additional physical state.

Therefore Track B's source-supported classification is
`INSUFFICIENTLY_DEFINED`. The following cannot be filled by a proxy in this
design:

- **Activation:** needs a source-supported initiation state/criterion such as
  a mechanical instability, fault nucleation/weakness plus driving stress, or
  an explicitly authored initial active fault. Existing pair process
  activation is not per-segment fault activation.
- **Deactivation:** needs a law for exhaustion, stress redistribution,
  healing, switching or abandonment; no such law is selected.
- **Interaction:** needs stress/traction transfer or another validated
  interaction closure with geometry and material dependence.
- **Linkage candidacy:** needs fault-tip/segment geometry plus an interaction
  or fracture criterion; graph proximity alone is not physical linkage.
- **Localization:** needs evolving spatial deformation/activity and a
  criterion that distinguishes concentration from numerical concentration.
- **Regime reevaluation:** needs a model-defined state and signed/uncertain
  margin or discrete transition status with detector coverage.

No segment may be made active just because its ID belongs to the pair
interface, because its endpoints show B6N8-A geometric mismatch, or because
the model needs a nontrivial output. Track B may return only `UNKNOWN` for
these outputs until a scientifically defensible reduced law and its inputs
are identified.

## Authorial synthetic-input policy

Classification is about authority, not data availability alone. A governed
field can be a model input only where its semantics, spatial support and
validity match the model. The input ledger below is not a selection of
quantities or values.

| Candidate input | Classification now | Support/units | May later be authored as a synthetic primitive? | WorldSim dependency / uncertainty |
| --- | --- | --- | --- | --- |
| POST_EVENT process identity, pair 1:3, geometry payload, 71 interface segment IDs, 72 unique interface nodes and governed junction incidence | `EXISTING_CANONICAL_STATE` | Exact existing IDs/support; geometry payload is the governed input | No need to invent; preserve identity | Read-only initial/checkpoint binding; no boundary/fault type follows from these identities |
| B6N2 plate-local Euler vectors and validity contract | `EXISTING_CANONICAL_STATE` / conditional forcing authority | rad/year; plate-local, pair-scoped through the contract | No new value here | The B6N2 contract still requires horizon/interval adjudication; no positive interval is authorized by this design |
| Relative plate-side motion from Euler vectors and initial geometry | `DETERMINISTIC_DERIVATION` | Sphere coordinate displacement/velocity diagnostics; 71-segment/72-node mapped only under declared frame rules | Not a primitive | Kinematic/numerical uncertainty; not physical extension, stress or accommodation |
| Unoriented local tangent/normal and relative velocity components | `DETERMINISTIC_DERIVATION` only after explicit geometric construction; signed physical normal/polarity remains `UNKNOWN` until convention is authorized | Segment support; tangent dimensionless, speed m/year if time authority applies | A frame/sign convention is an authorial model decision, not a physical value | Geometry discretization and frame uncertainty; do not call normal velocity physical rift opening |
| Current governed crustal thickness and continental reference heat-flow/lithosphere fields | `EXISTING_CANONICAL_STATE` on their current T0 source support, where present | Cell/class support and existing field units | Do not duplicate as new primitives | Must bind/reproject to interface/model scope under a separate deterministic support rule; T0 surface heat flow does not itself define a full geotherm |
| Full initial temperature profile, basal thermal state or layer-specific thermal state | `UNKNOWN / NOT_CURRENTLY_GOVERNED` for this rift interface/model initialization unless a matching current authority artifact is explicitly bound | K; vertical profile and lateral model support | Potentially yes, as a synthetic planet's initial physical state | Could later be produced by a governed thermal/geology domain; uncertainty as profile/range/ensemble with source resolution |
| Crust/lithosphere thickness profile, material composition and spatial weakness/heterogeneity | Existing T0 fields may constrain parts; model-ready profile/weakness scope is `UNKNOWN / NOT_CURRENTLY_GOVERNED` | m and discrete material/support IDs; no invented width | Yes, if required by a selected law and included in world-generation authority | Likely geology/material domain; preserve discrete material IDs and spatial uncertainty; no Earth fault locations |
| Heat capacity, conductivity, density, expansion, heat production and gravity | `LITERATURE_CALIBRATED_PARAMETER` or `AUTHORIAL_SYNTHETIC_PRIMITIVE` depending on planetary authority; not selected | SI units, by material and support | May be authored as planet composition/structure when world-generation authority defines them | Could be generated by material/thermal domains; represent parameter and model-form uncertainty separately |
| Brittle friction/cohesion/effective pressure, ductile flow-law family and constants, strain weakening, fracture energy | `LITERATURE_CALIBRATED_PARAMETER` only after a model/domain justification; currently `UNKNOWN / NOT_CURRENTLY_GOVERNED` for B6 | Law-specific units and material support | Some constitutive choices are authorial model decisions, but numeric values need evidence | Requires laboratory/literature support and applicability argument; ranges/distributions/model alternatives, no paper table copied as canon |
| Initial fault activity/damage, segment activation, segment slip, tip state | `MODEL_INTERNAL_STATE` only after a selected law and authorized initialization; otherwise `UNKNOWN / NOT_CURRENTLY_GOVERNED` | Per model segment/fault support | Only through an explicit physical initialization rule, never arbitrary per-segment assignment | Could derive from prior tectonic history later; uncertainty and provenance per segment |
| Buck integrated strength, buoyancy components, effective flow diffusivity and ΔF | `DETERMINISTIC_DERIVATION` from a complete initialized Buck state/law | force per unit length; flow diffusivity m²/s in the published reduced closure | No; derived outputs, not independent canon | Propagate all input/model/numerical uncertainties into signed ΔF and predicate status |
| Track B stress, traction, damage or energy-release driving field | `UNKNOWN / NOT_CURRENTLY_GOVERNED` | Model-specific spatial/fault support | Could be authored only under a physical initial-state model; stress usually must be produced by an authorized mechanical model | Missing producer, constitutive law and scope; preserve UNKNOWN |
| Active-zone width, widening, fault linkage and topology/support outcome | `MODEL_INTERNAL_STATE` or predicate candidate only after model definition; actual topology/support outcome remains separate authority | Explicit model support, m or discrete graph identity | Not a primitive for this stage | Output may request reevaluation only; uncertainty on location/width and detector coverage |

An `AUTHORIAL_SYNTHETIC_PRIMITIVE` needs a declared reason the synthetic
planet requires the quantity, physical units, support/resolution, authority
source, dependency owner and uncertainty. Some initial fields may be authored
in the synthetic-world initializer; others should be generated by a governed
material, thermal or geological WorldSim domain. This design does not decide
which domain owns them or populate values.

### PRE-ACTIVATION HISTORY AND T1 INITIALIZATION AUTHORITY

The rift activation age is **209.97287659484368 Ma**. A candidate model may
require physical state at T1, but that requirement alone does not authorize
creating an initial value at activation. For every required quantity, later
B6N8-D/B6N8-E work must distinguish the **initial value required by the
model** from the **authority to create that value at T1**, and classify its
temporal origin as one of:

- `STATIC_PLANETARY_PARAMETER`;
- `PREEXISTING_EVOLVED_STATE`;
- `ACTIVATION_INITIALIZED_STATE`;
- `POST_ACTIVATION_DERIVED_STATE`;
- `UNKNOWN`.

Thermal structure, crustal thickness, lithospheric thickness, strength or
rheological structure, density/material structure, inherited weaknesses and
lower-crustal state are candidate prehistory-sensitive quantities if the
selected equations depend on them. This list assigns no values and does not
assert that every quantity belongs in the final model. No present-Earth or
published reference value is imported into ARCANA.

B6N8-D may find that a required process state cannot be initialized solely at
rift activation. If a quantity should have evolved before T1, subsequent work
must establish whether it is already represented by ARCANA state, derivable
from existing history, reconstructible under qualified authority, or requires
a new upstream historical state/domain. It must not be silently backcast, and
an authorial constant cannot substitute for historical evolution without
separate authorization. Until that adjudication, its temporal origin and
initialization authority remain `UNKNOWN`.

## Common ARCANA comparison interface (conceptual only)

Both model tracks use the same B6N6-facing shell and return typed, scoped
results. No production API is introduced.

| Operation | Conceptual contract |
| --- | --- |
| `initialize_process_state` | Bind model/version, authority, POST_EVENT checkpoint, pair/interface/junction support, model-specific initialized state, parameter authority, uncertainty and replay identity; fail closed on a missing required field. |
| `consume_B6N2_kinematic_forcing` | Accept only B6N2 vectors and an separately authorized temporal scope. Produce model-frame kinematic input only after frame/support mapping; never relabel the geometric mismatch as opening. |
| `advance_process_state(INTERNAL_DT)` | Return an isolated candidate state plus rates/error/stability and model validity. `INTERNAL_DT` remains temporary numerical time and is not `dt2` or a persistent interval. |
| `report_process_observables` | Emit named value, units, kind (`EVOLVED_STATE`, `DERIVED_DIAGNOSTIC`, `INVARIANT`, `UNAVAILABLE`, `UNKNOWN`), authority, support, time validity and input identities. |
| `evaluate_regime_predicates` | Emit per-predicate TRUE/FALSE/UNKNOWN, signed margin if defined, uncertainty, validity, detector coverage and bracketability. A crossing is only a candidate. |
| `evaluate_interface_reevaluation_predicates` | Return the exact covered interface IDs or declared aggregate support, uncovered IDs, status and uncertainty. No uniform assignment to all 71 segments. |
| `evaluate_topology_reevaluation_predicates` | Emit conservative `REEVALUATE / NO_REQUEST / UNKNOWN` request and event-class coverage. Never emit or apply new connectivity. |
| `evaluate_support_reevaluation_predicates` | Report current membership `VALID / INVALID / UNKNOWN`, affected support and dependency buffer; no reassignment. |
| `report_uncertainty` | Preserve separate parameter, forcing, model-form, spatial-localization, criterion, event-time, numerical and dependency uncertainty; no unsupported single confidence scalar. |
| `report_authority_bounds` | Identify exact source/model/temporal/spatial scope, validity limit, unsupported outputs and stop conditions; unknown applicable bound stops/isolate scope. |
| `report_adaptive_dt_indicators` | Report integration error/stability, state rate, predicate margin/rate, uncertainty growth, validity bounds and event bracket width. B6N6 chooses no step without separate authorization. |

Replay binds model equation/version, initial state, all authored/calibrated
inputs, support mapping, B6N2 forcing identity, uncertainty settings, solver
and accepted/rejected step decisions, predicate definitions, random seed if
any, scope/buffer proof, and output identities. Track A may be deterministic
conditional on fully bound inputs and numerical policy. Track B would need
reproducible nucleation/tie-breaking or explicit stochastic seed lineage.

## Common synthetic test case

Use the exact governed POST_EVENT plate-pair 1:3 input as a **read-only
support fixture**: its 71 interface segments, 72 unique node identities and
the governed incident junction identities remain unchanged. Both tracks must
receive the same input checkpoint, geometry/support hashes, B6N2 vector
identity, forcing samples, declared experiment window, and replay protocol.
The model may use an explicitly authored synthetic material/thermal profile
only after the input ledger and authority have been closed. Track B cannot
start with fault-active labels unless a future law initializes them.

B6N8-A's reported `pair_side_geometric_mismatch` remains a derived diagnostic
and is not input as opening, extension, slip or damage. B6N8-A's
2053.512977-year shadow window is **not** reused as a physical experiment
duration; it was a diagnostic fraction of a model-scope bound, not a physical
validity interval. A future experiment window and temporal discretization
must be separately specified for the isolated experiment, with no canonical
WORLD_HISTORY publication and no implication of `dt2`/T2 authorization.

Common controls:

1. **Baseline B6N2-only control:** derive only existing kinematic diagnostics
   and record no process state/predicate unless the new law creates it.
2. **Track A:** calculate model-defined state/force terms and its source
   criterion from the same synthetic material/thermal initial state and
   forcing. Return only reevaluation requests, not a topology result.
3. **Track B:** run only if a primary source and defensible reduced equations
   for activity/interactions, initialization and driving state are found. If
   not, record `INSUFFICIENTLY_DEFINED`/UNKNOWN; do not synthesize the missing
   equations.
4. Repeat each eligible case with identical support and forcing under the
   declared numerical refinement protocol; compare physical/process
   observables separately from integration error. No acceptance tolerance is
   invented here.
5. Vary only authoritatively bounded inputs/uncertainties in a later approved
   experiment; keep scenario sensitivity distinct from numerical refinement.

Because B6N2 currently has no selected positive-duration successor window,
this design itself does not initiate a geological-time advance. A future
noncanonical prototype must first name its own research scope and time
coordinate and demonstrate that it is not claiming canonical temporal
authority.

## Comparison outputs and no-arbitrary-score rule

Record per track, using evidence or explicit `UNKNOWN`:

- process-state components, units, evolution law and whether they add
  information not derivable from B6N2;
- predicate definitions, input dependencies, margin/status, uncertainty,
  validity, detector coverage and bracketability;
- segment/interface support coverage, uncovered identities and junction
  scope;
- topology event classes that can trigger reevaluation and classes not
  covered; support-validity evidence and dependency closure;
- number/types of required initial fields and parameters, each with source,
  support, units and uncertainty; missing-input count/list, not an arbitrary
  burden score;
- uncertainty dimensions represented versus left UNKNOWN;
- local domain/buffer required and evidence for isolating it;
- variable-step support, solver stability/error estimator and event-refinement
  behavior, demonstrated or untested;
- deterministic replay identity or stochastic seed policy;
- wall time, memory and equations/solve counts from later runs, compared on
  the same hardware/configuration; no arbitrary latency cutoff;
- model-form complexity, mechanical equations/fields required, software
  dependencies/version/license and synthetic-world transfer limits.

Keep B6N7 requirement coverage and all four B6N4-R1 blockers as independent
rows. A model can score `DIRECTLY_ADDRESSED` for process evolution and still
be `NOT_ADDRESSED` for support validity. Do not collapse them to a weighted
score or declare an overall pass by averaging.

## Prototype go/no-go criteria

A track merits implementation only if the research design can show all of:

1. at least one initialized process-state component has a source-supported
   evolution law and is not just a B6N2 coordinate/displacement duplicate;
2. at least one dynamic regime/validity predicate follows from the cited
   equations or qualified model authority, including its physical scope and
   signed margin/uncertainty where defined;
3. every required input is either bound to current authority, explicitly
   proposed as an authorial synthetic primitive, or transparently blocks
   execution; no unknown is filled with an Earth default;
4. interface mapping declares covered/uncovered segments and junctions;
5. topology/support outputs are requests only and stop conservatively when
   coverage or validity is unknown;
6. variable-`INTERNAL_DT` behavior, detector coverage and replay can be tested
   without publishing WORLD_HISTORY;
7. the model's mechanics dependency and computational domain are explicit.

No arbitrary numerical threshold for state change, accuracy, runtime,
uncertainty or acceptance is introduced. For Buck, a source-defined sign
change in the model's net force response is a candidate mode criterion; its
use as an ARCANA *reevaluation request* requires explicit approval and
uncertainty treatment. It is not the criterion for plate splitting or
breakup. For Track B, absent source-derived activation/interactions means
no-go until research supplies that law.

## B6N4-R1/B6N7 coverage expectation

| Blocker / requirement | Track A expected capability if faithfully initialized | Track B current research status | Separate authority that remains |
| --- | --- | --- | --- |
| Next rift-process evolution | Potentially direct within Buck's limited state/validity | `UNKNOWN` until reduced network law identified | Model validity and inputs |
| Interface event predicates | Regional mode signal only; per-segment mapping not established | Could be segment-native, but currently no defensible reduced law | Segment/junction response mapping |
| Generic topology event coverage | At most request reevaluation when the model criterion signals a mode boundary | No coverage established | Split/merge/boundary/junction transition classes and application |
| Support membership validity | Not supplied by force criterion | Not supplied | Support dependency closure/remap authority |
| B6N7 state semantics/units | Model state can be explicit; profile/force units traceable | Not yet definable from a source-backed reduced model | Initial state authority and units/support |
| Forcing/initialization/replay | Requires same B6N2 forcing plus physical profile/material state; conditional | Requires driving stress/slip/history or new law | Synthetic input authority, validity and replay closure |
| Uncertainty/adaptive stepping | Possible to expose, but Buck's published analysis does not by itself provide an ARCANA event-error controller | Undetermined | Parameter/model-form uncertainty, solver bounds and detector coverage |

## Mechanics escalation and remaining decisions

**Result: `TIER2_PLUS_LIMITED_PHYSICAL_STATE_REQUIRED`.** Track A is a
reduced model with finite physical thermal/strength/thickness/flow state and
an integrated force response. Its force criterion is mechanically derived;
it is not mechanics-free merely because it avoids a full regional Stokes or
finite-element solve. Full mechanics is not proven necessary for the
reevaluation-only prototype. If the desired output expands to segment slip,
stress redistribution, fault linkage, accommodation or physical breakup
geometry, current evidence may force escalation toward Tier 4, but that
decision is not made here.

Track B remains `UNRESOLVED` and may require Tier 4 to get source-supported
activation and interaction. Do not relabel stress, fracture or mechanical
accommodation as a scalar heuristic to preserve a Tier-2 label.

Before any prototype coding, the decision owner still needs to adjudicate:

- whether candidate lithospheric/thermal/material primitives may be authored
  for this synthetic planet and which WorldSim domain owns each;
- whether the Track A criterion is acceptable solely as a process/regime and
  reevaluation request, with no width/topology update;
- which model support maps to the pair interface and what remains uncovered;
- how a positive-duration noncanonical experiment window is authorized,
  given the B6N2 validity gate;
- parameter authority/uncertainty and permissible physical claims.

## Preserved gates

```text
physical_rift_model_selected = false
physical_rift_model_qualified = false
prototype_implemented = false
physical_parameters_selected = false
SECOND_DT_SELECTED = false
dt2_years = null
T2_CREATED = false
B6O_authorized = false
mechanics_executed = false
canonical_forward_propagation_executed = false
topology_transition_executed = false
support_remapping_executed = false
WORLD_HISTORY_changed = false
```

No prototype was implemented or run. No coefficient, physical value, time
step, event time, topology result or support reassignment was selected. The
design creates no production contract and authorizes no propagation.

## Next scientific investigation

The next supported investigation is **B6N8-D — BUCK EQUATION-LEVEL RECOVERY
AND MINIMAL-STATE REDUCTION AUDIT**. It must recover the published governing
equations and complete causal dependency graph; identify evolved and
algebraic variables, parameters, forcing, boundary and initial conditions,
thermal, strength/force and applicable lower-crustal-flow dependencies; trace
the widening/localization criterion and its provenance; and assess the
minimum causally faithful state, unsafe-to-remove dependencies, candidate
reductions, initialization and prehistory requirements, uncertainty sources,
validity limits, and B6N2-to-model forcing requirements.

B6N8-D is an equation-level scientific audit only. It does not authorize
prototype implementation, physical-model selection, numerical coefficient
selection, `dt2`, T2, B6O, canonical propagation, mechanics execution, topology
mutation or support remapping. B6N8-C authorizes only
`PROCEED_TO_B6N8D_EQUATION_LEVEL_AUDIT`.

## Scientific provenance

- **PRIMARY, model equations and assumptions:** Buck, W. R. (1991), “Modes of
  continental lithospheric extension,” *JGR* 96(B12), 20161–20178,
  [doi:10.1029/91JB01485](https://doi.org/10.1029/91JB01485). Equation-level
  source reviewed via the article text at
  [AGU/Wiley](https://agupubs.onlinelibrary.wiley.com/doi/abs/10.1029/91jb01485)
  and the accessible paper copy at
  [ResearchGate](https://www.researchgate.net/publication/241588292_Modes_of_Continental_Lithospheric_Extension).
  Key dependencies: thin-sheet integrated yield/buoyancy force; finite
  imposed strain; 1-D thermal advection/diffusion at the extension-zone
  center; brittle/ductile yield envelope; lower-crust flow/thickness evolution;
  model-assumed widening/localization from force change. Its stated important
  limitation is incomplete coupling between flow and thermal calculations.
- **PRIMARY, forward fault-network mechanics:** Finch, E. & Gawthorpe, R.
  (2017), “Growth and Interaction of Normal Faults and Fault Network Evolution
  in Rifts: Insights from Three Dimensional Discrete Element Modelling,”
  *Geological Society, London, Special Publications*,
  [doi:10.1144/SP439.23](https://doi.org/10.1144/SP439.23). The peer-reviewed
  abstract states nucleation, propagation and interaction respond to local
  heterogeneities and resulting stresses; used to assess Track B's driving
  state/mechanics requirements.
- **PRIMARY, fault growth via slip:** Cowie, P. A. & Scholz, C. H. (1992),
  “Growth of faults by accumulation of seismic slip,” *JGR* 97(B7),
  11085–11095, [doi:10.1029/92JB00586](https://doi.org/10.1029/92JB00586).
  Used to distinguish slip-driven fault growth from a model that predicts
  activation from B6N2 kinematics.
- **PRIMARY, fault interaction / rift linkage:** Wolf et al. (2022),
  “Evolution of Rift Architecture and Fault Linkage During Continental
  Rifting,” *JGR: Solid Earth*,
  [doi:10.1029/2022JB024687](https://doi.org/10.1029/2022JB024687). The study
  identifies crustal strength, inherited structures and surface-process
  efficiency as controls; used as evidence against arbitrary segment-only
  activation.
- **PRIMARY, fault evolution caveat:** Pan et al. (2022), “Evolution of
  normal fault displacement and length as continental lithosphere stretches,”
  *Basin Research*, [doi:10.1111/bre.12613](https://doi.org/10.1111/bre.12613).
  The paper reviews that many fault growth models are based on final geometry
  and lack kinematic constraints; used as an adversarial screen, not as ARCANA
  authority.
- **ARCANA authority:** `contracts/R6_MINIMUM_EVOLVABLE_RIFT_MODEL_REQUIREMENTS_V1.json`,
  `contracts/R6_MINIMUM_RIFT_MODEL_B6N4R1_BLOCKER_MATRIX_V1.json`,
  `contracts/R6_POST_EVENT_KINEMATIC_AUTHORITY_V1.json`,
  `contracts/R6_ADAPTIVE_PROPAGATION_CANDIDATE_TRAJECTORY_V1.json`, and the
  B6N8-A contract/attestation. These bound the synthetic support, conditional
  forcing, separate predicates and non-actions; they do not supply missing
  constitutive authority.
