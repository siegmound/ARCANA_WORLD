# ARCANA WORLD — R6 CANONICAL CLEAN REPLAY OBJECTIVE

**Status:** Strategic objective / future execution contract  
**Project:** ARCANA WorldSim  
**Current development line:** R5.17 / B7 / P7S  
**Reference repository:** `siegmound/ARCANA_WORLD`  
**Current reference world role:** development + scientific oracle  
**Target future line:** `R6_CLEAN_REPLAY`  
**Last baseline referenced when this objective was written:** `main` at `57e9e1885e0d91859409d81dc8dbca92d04c3ab7`

---

## 1. Core objective

ARCANA will **not** continue indefinitely by stacking new world layers on top of the current R5 development simulation.

The intended future transition is:

> **Finish and freeze the remaining foundational physical contracts—especially P7S—then run a new clean simulation from the same initial physical state and the same CHA-1 / CHA-2 events, using the mature toolchain, authority rules, provider bindings, UNKNOWN semantics, provenance, and validation systems developed during R3–R5.**

The current R5 world is therefore not considered wasted or invalid.

Its long-term role is:

```text
R5_REFERENCE_WORLD
=
development world
+
scientific oracle
+
regression reference
+
source of validated contracts and invariants
```

The future R6 world is intended to become:

```text
R6_CLEAN_REPLAY
=
first canonical end-to-end replay
using the mature ARCANA simulation architecture
```

---

## 2. Why a clean replay is desirable

The existing world was produced while the simulation architecture itself was evolving.

The historical workflow often had the form:

```text
simulate
→ discover missing authority
→ recover data
→ add provider
→ repair contract
→ replay partial stage
→ add unknown mask
→ reconcile
→ continue
```

This development process was useful because it exposed real scientific and engineering weaknesses.

However, once the architecture is sufficiently mature, the canonical world should instead be generated through:

```text
validate prerequisites
→ execute stage
→ validate outputs
→ advance
```

from the beginning.

A clean replay will separate:

```text
effects caused by:
initial state + physical rules + CHA events

from

effects caused by:
historical implementation choices,
fallbacks,
partial recoveries,
or pipeline evolution
```

This is scientifically important, not merely repository cleanup.

---

## 3. What must remain identical in R6

R6 must begin from the **same canonical starting state** used by the current ARCANA world wherever that state remains scientifically valid.

The replay must preserve:

```text
same initial physical world state
same canonical physical laws
same sealed canon constraints
same CHA-1 event
same CHA-2 event
same event timing
same event semantics
same intentionally fixed stochastic seeds where applicable
same authoritative external evidence where still current
```

R6 must not silently redesign the world merely because better tools now exist.

The purpose is to rerun the same world-generating experiment through a better, cleaner simulation pipeline.

---

## 4. CHA-1 and CHA-2 requirement

CHA-1 and CHA-2 must become explicit replayable event contracts rather than being represented only through downstream historical artifacts.

Conceptually:

```text
STATE(t_before)
+
CHA_EVENT
↓
EVENT TRANSFORM
↓
STATE(t_after)
```

Each CHA event should eventually have an explicit machine-readable contract covering at least:

```text
event identifier
event time
spatial footprint
physical forcing
energy/material effects
duration
uncertainty
downstream coupling rules
deterministic/stochastic components
provenance
```

R6 must reproduce the same canonical CHA-1 and CHA-2 events.

A future counterfactual system may later permit:

```text
replay with CHA
vs
replay without CHA
```

but that is **not** the purpose of the initial R6 clean replay.

---

## 5. Current position before the R6 transition

At the time this objective was written, ARCANA is still completing the foundational P7S physical-soil/hydraulic architecture.

Current high-level state:

```text
P7Q / HRAB parent-material authority       COMPLETE AS SPARSE TEMPORAL AUTHORITY

P7S endpoint SoilGrids binding             PROVEN
P7S Rosetta hydraulic derivation           PROVEN
BIOME4 dz/whc/Ksat input contract           PROVEN
endpoint physical invariants                PROVEN
material-only transferability               TESTED / INSUFFICIENT
environment-conditioned endpoint diagnostic DONE
BIOME4 hydraulic sensitivity                DONE
historical driver authority audit           DONE
historical climate provider adjudication    DONE
Python/OpenSSL TLS access                    PROVEN
HTTP Range access                            PROVEN

bounded HDF5/NetCDF climate extraction       CURRENT BLOCKER
historical climate binding                   NOT YET PROVEN
historical Ksat proof                        NOT YET COMPLETE
WHC historical treatment                     NOT YET COMPLETE
bounded P7S hydraulic replay                 NOT YET AUTHORIZED
```

The current immediate work must therefore continue.

**Do not start R6 merely because the clean replay objective exists.**

---

## 6. Gate for starting R6

The preferred transition point is:

```text
1. finish P7S historical climate binding
2. finish historical Ksat strategy
3. finish WHC bounded historical strategy
4. establish the final P7S hydraulic replay contract
5. confirm the BIOME4 production input/output contract
6. freeze the foundational architecture
7. start R6_CLEAN_REPLAY
```

It is **not necessary** to continue the current R5 world all the way through civilizations before launching R6.

The intended strategy is to stop extending the old development world once the foundational physical/ecological simulation contracts are mature enough to replay cleanly.

---

## 7. R6 architecture principle

R6 should be orchestrated as a reproducible stage graph, approximately:

```text
BOOTSTRAP / INITIAL STATE
        ↓
GEOLOGY / TOPOGRAPHY
        ↓
CLIMATE
        ↓
CHA-1
        ↓
HYDROLOGY
        ↓
EARLY ECOLOGY / BIOLOGICAL EVOLUTION
        ↓
CHA-2
        ↓
LATE BIOLOGICAL EVOLUTION
        ↓
PARENT MATERIAL / HRAB
        ↓
P7S PHYSICAL SOIL / HYDRAULICS
        ↓
BIOME4 VEGETATION / PHYSICAL NPP
        ↓
TERRESTRIAL ANIMAL RESOURCES / MADINGLEY
        ↓
AQUATIC + MARINE RESOURCES
        ↓
MATERIAL / NATURAL RESOURCES
        ↓
SETTLEMENT GEOGRAPHY / CONNECTIVITY
        ↓
K(x,t)
        ↓
HUMAN / CIVILIZATION LAYER
```

The exact stage names may evolve, but the principle is fixed:

> **Every downstream stage must consume an explicitly validated upstream contract.**

---

## 8. First-class UNKNOWN semantics

R6 must incorporate uncertainty and missing authority from the beginning.

The world state must preserve distinctions such as:

```text
KNOWN
DIRECT_SUPPORTED
DERIVED_SUPPORTED
SPARSE_AUTHORITY
UNKNOWN
OUTSIDE_SCOPE
NOT_APPLICABLE
```

Unknown values must not be silently converted into estimated values merely to achieve full spatial coverage.

The replay philosophy remains:

```text
where authority exists:
    compute

where bounded derivation is justified:
    derive with uncertainty

where authority is insufficient:
    preserve UNKNOWN

where physically inapplicable:
    mark NOT_APPLICABLE / OUTSIDE_SCOPE
```

This is a core ARCANA design requirement.

---

## 9. Provider and scientific authority rules

R6 must reuse the provider-governance lessons learned during R5.

Every external source must have explicit:

```text
provider identity
version
source URL / DOI
variable semantics
spatial support
temporal support
units
native resolution
authority class
uncertainty
retrieval provenance
hashes where appropriate
license/access information
```

A provider must not be promoted beyond its actual authority.

Examples of distinctions that must remain explicit:

```text
direct observation
direct GCM-derived
statistical reconstruction
downscaled model
derived variable
cross-check only
endpoint calibration authority
historical authority
```

No automatic interpolation or backcasting is allowed unless the source semantics explicitly justify it.

---

## 10. Tooling that R6 should inherit from the beginning

R6 should use the mature tools developed during R5 rather than rediscovering them after failures.

Important capabilities include:

```text
provider registry
scientific authority matrices
temporal coverage adjudication
explicit UNKNOWN masks
hash/provenance ledgers
bounded provider acquisition
schema validation
deterministic cohort selection
replay contracts
cross-provider comparison
scientific authority register
runtime/environment validation
path-scoped Git governance
fail-closed execution
deterministic cache reuse
```

The clean replay should prefer automated prerequisite validation before each stage.

---

## 11. Reproducibility requirement

R6 should aim for:

```text
fresh machine
+
repository
+
declared runtime environments
+
provider manifests
+
external data references
+
fixed intentional seeds
+
canonical configuration
=
reproducible world replay
```

Bit-identical output is not required when an external simulator cannot guarantee it.

However, ARCANA must be able to reproduce:

```text
scientific inputs
stage decisions
authority masks
major world structures
statistical outputs
governed invariants
```

within explicitly declared tolerances.

---

## 12. R5 → R6 reconciliation

R6 must not automatically become canonical merely because it is newer.

At major milestones compare R6 against R5.

The comparison should focus on **structural and scientific invariants**, not strict cell-by-cell identity.

Examples:

### Geology / topography

```text
continental structure
major basins
elevation distribution
shoreline topology
```

### Climate

```text
global/regional temperature structure
precipitation belts
seasonality
major climatic domains
```

### Hydrology

```text
major basin topology
river-network structure
freshwater availability
lake/channel regimes
```

### CHA events

```text
affected regions
physical forcing
event consequences
post-event state transitions
```

### Biology

```text
species-count ranges
cradle persistence
lineage/dispersal structure
major ecological regions
```

### HRAB / parent material

```text
material-family geography
known/unknown fractions
temporal support
conflict structure
```

### P7S

```text
hydraulic distributions
WHC/Ksat ranges
unknown-mask extent
BIOME4 input validity
```

---

## 13. Canonical promotion rule

After replay to at least the foundational P7S/BIOME4 boundary:

```text
R5_REFERENCE_WORLD
vs
R6_CLEAN_REPLAY
```

must be reconciled.

Possible outcomes:

```text
R6 ROBUST
→ R6 becomes canonical baseline

R6 DIFFERS BUT EXPLAINABLY
→ adjudicate and document differences

R6 MAJOR UNEXPLAINED DIVERGENCE
→ investigate before canonical promotion
```

R5 must remain available as an oracle/reference until R6 has passed reconciliation.

---

## 14. R6 should not inherit development debris

R6 should not blindly copy:

```text
temporary recovery scripts
obsolete provider attempts
duplicated schemas
historical debug artifacts
superseded intermediate ledgers
one-off manual patches
```

Only the final validated contracts, tools, providers, and canonical inputs should enter the clean replay.

The R5 repository history remains evidence of how those decisions were reached.

---

## 15. No premature R6 start

The existence of this objective must **not** interrupt current P7S work.

Immediate priority remains:

```text
complete bounded historical climate access/binding
→ historical Ksat proof
→ WHC bounded strategy
→ final P7S contract
```

Only after this foundational architecture is sufficiently frozen should R6 begin.

---

## 16. Long-term success criterion

The final goal is not simply “a cleaner repository”.

The clean replay succeeds if we can state:

> Starting from the same canonical initial world and the same CHA-1 / CHA-2 events, the mature ARCANA toolchain independently regenerates a physically, biologically, temporally, and provenance-consistent world whose major structures are explainable from the model rather than from historical implementation patches.

This is the intended transition from:

```text
simulation under development
```

to:

```text
validated world-generation system
```

---

## 17. Immediate continuation instruction

Until the R6 gate is reached:

```text
CONTINUE R5.17 / P7S
```

Current immediate direction:

```text
resolve bounded HDF5/NetCDF climate extraction
without exceeding provider-transfer governance

then

bind historical climate authority

then

prove historical Ksat strategy

then

resolve bounded WHC strategy

then

freeze the P7S contract
```

After that, explicitly adjudicate:

```text
AUTHORIZE_R6_CANONICAL_CLEAN_REPLAY
```

Do not begin R6 implicitly.

---

## 18. One-sentence project memory

> **ARCANA R5 is the development/reference world used to finish and validate the simulator; once P7S and the foundational BIOME4 contract are frozen, ARCANA should launch R6 as a clean end-to-end replay from the same initial state and identical CHA-1/CHA-2 events, using the mature authority/provenance/UNKNOWN-aware toolchain, reconcile R6 against R5, and only then continue canonical downstream worldbuilding.**
