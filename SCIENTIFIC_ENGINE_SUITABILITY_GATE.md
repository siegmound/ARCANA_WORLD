# ARCANA WorldSim — Scientific Engine Suitability Gate

## Authority and purpose

```yaml
PROJECT: ARCANA WorldSim
DOCUMENT_ROLE: PERSISTENT_SCIENTIFIC_PROVIDER_AND_TOOL_SELECTION_POLICY
APPLIES_FROM: post-v0.6D1-R5.16
APPLIES_TO: R5.17 and later scientific/implementation stages
PARENT_GOVERNANCE:
  - v0.6D1-R5.16 SEALED
  - ARCANA_WORLD_POST_R5_16_MACROHISTORY_OBJECTIVE.md
STATUS: ACTIVE_GOVERNANCE_POLICY
CANONICAL_WRITER: ARCANA_WORLD_ORCHESTRATOR_ONLY
```

This file exists so future stages and new conversations do not have to reconstruct the scientific-tool policy from chat history.

The governing principle is:

> **Use the most scientifically appropriate existing authority or specialist engine for each research question. Do not default to custom ARCANA code when a validated domain-specific tool can answer the question more defensibly.**

No external engine replaces ARCANA WorldSim. Engines, libraries and providers produce governed evidence. ARCANA retains orchestration, provenance, adjudication and canonical authority.

---

## 1. Mandatory decision order

Before implementing a new scientific computation, apply this gate in order:

```text
SCIENTIFIC QUESTION
        |
        v
1. EXISTING ARCANA AUTHORITY SUFFICIENT?
        | yes -> reuse exact governed payload/state
        | no
        v
2. EXISTING VALIDATED SPECIALIST ENGINE SUITABLE?
        | yes -> reuse through governed adapter/run
        | no
        v
3. NEW SPECIALIST TOOL CLEARLY JUSTIFIED?
        | yes -> audit, pin, validate, then use as provider
        | no
        v
4. MINIMUM CUSTOM ARCANA IMPLEMENTATION
```

The preferred outcome is the earliest scientifically sufficient branch in this sequence, not the branch with the least implementation effort.

A stage must not introduce a new engine merely because it exists, and must not implement a bespoke approximation merely because writing Python locally is easier.

---

## 2. Mandatory pre-compute questions

Every new scientific subproblem must answer all of the following before implementation:

1. **What exact scientific quantity or process is unresolved?**
2. **Does a SEALED/CANDIDATE governed ARCANA payload already contain it or a defensible derivation basis?**
3. **Are the semantics, units, spatial support and temporal support sufficient for the requested use?**
4. **Which already validated specialist engines are scientifically applicable?**
5. **Would a new external specialist tool materially improve physical/biological validity, numerical robustness or reproducibility?**
6. **What is the minimum computation necessary?**
7. **What output will be evidence only, and what later adjudication is required before canonical use?**

If semantic sufficiency cannot be demonstrated, the computation is blocked from promotion even if code can technically produce a number.

---

## 3. Standard gate record

Each stage that requires a material provider/tool decision should record an equivalent of:

```yaml
SCIENTIFIC_QUESTION:

EXISTING_ARCANA_AUTHORITY:
  candidates: []
  exact_identity_verified: false
  semantics_sufficient: false
  decision:

EXISTING_VALIDATED_ENGINES:
  candidates: []
  selected:
  decision:

NEW_SPECIALIST_TOOLS:
  candidates: []
  audit_required: true
  selected:

SELECTED_PROVIDER:
  name:
  role:
  version:
  runtime_identity:
  justification:

REJECTED_ALTERNATIVES:
  - provider:
    reason:

CUSTOM_IMPLEMENTATION_REQUIRED: false
MINIMUM_CUSTOM_SCOPE:

CANONICAL_ROLE: EVIDENCE_PROVIDER_ONLY
ADJUDICATION_REQUIRED: true
```

Allowed decision classes are:

```text
REUSE_CANONICAL_ARCANA
REUSE_VALIDATED_PROVIDER
INTRODUCE_SPECIALIST_PROVIDER
MINIMUM_CUSTOM_IMPLEMENTATION
BLOCKED_INSUFFICIENT_SEMANTICS
```

---

## 4. Suitability criteria

Provider selection must be based on the scientific problem rather than habit or availability. At minimum evaluate:

- semantic match to the target quantity/process;
- physical/biological assumptions;
- state representation and units;
- temporal scale and timestep behavior;
- spatial scale, grid/topology and boundary behavior;
- stochasticity and ensemble support;
- calibration requirements;
- compatibility with changing ARCANA paleogeography/environment;
- ability to preserve lineage/species/state identity where relevant;
- numerical stability and known limitations;
- computational cost on available local hardware;
- deterministic/reproducible execution where expected;
- version/runtime pinning and provenance;
- adapter/integration burden;
- output inspectability and validation;
- licensing/redistribution constraints when relevant.

A familiar engine is not automatically suitable. A scientifically mismatched engine must be rejected even if already installed.

---

## 5. Existing ARCANA specialist-engine baseline

This is a routing baseline, not an instruction to run every engine.

### NEMO

Primary use class:
- forward-time individual-based quantitative genetics;
- QTL/quantitative-trait experiments;
- selection, dispersal and demography where NEMO semantics fit.

Repository history pins NEMO 2.4.2 for the earlier quantitative-genetics oracle role. A later stage must still verify the runtime identity it actually executes.

### Geonomics

Primary use class:
- landscape genomics;
- spatially explicit genotype-environment dynamics;
- regional individual/genomic experiments.

Use when joint spatial/environment/genomic structure is central to the question.

### SLiM

Primary use class:
- forward-time population genetics;
- selection, mutation, introgression/admixture and demographic histories;
- genetically explicit lineage experiments.

Prefer SLiM when the question is fundamentally population-genetic rather than ecological or macrohistorical.

### tskit / msprime / pyslim ecosystem

Primary use class:
- tree-sequence handling;
- ancestry/genealogy representation;
- efficient ancestry simulation or post-processing where appropriate;
- SLiM-compatible genealogical workflows.

Stage-local versions and exact runtime bindings must be verified before production use; their presence never authorizes an ancestry interpretation automatically.

### CDMetaPOP

Primary use class:
- spatial demogenetics;
- metapopulation structure;
- multispecies/population connectivity and gene-flow robustness.

Prefer isolated, version-pinned execution when its runtime requirements differ from the main ARCANA environment.

### RangeShiftR / RangeShifter

Primary use class:
- dispersal;
- range expansion/colonization;
- landscape connectivity;
- persistence under spatially explicit movement assumptions.

Use as a specialist range-dynamics provider, not as a replacement for ARCANA species/history authority.

### Madingley / MadingleyR

Primary use class:
- ecosystem/trophic opportunity;
- macroecological sensitivity or provider evidence where its abstractions fit.

This remains a candidate/provider class unless the active stage explicitly pins and validates the exact runtime/package used. It must remain separate from ARCANA species authority.

---

## 6. Domain routing baseline

Use this table as the default starting point, then apply the suitability criteria above.

| Scientific problem | First provider classes to evaluate |
| --- | --- |
| quantitative genetics | NEMO; SLiM where appropriate |
| forward population genetics / selection / introgression | SLiM; tskit/pyslim for tree-sequence handling |
| ancestry / genealogy | tskit; msprime; pyslim/SLiM as appropriate |
| landscape genomics | Geonomics; SLiM for targeted genetic experiments |
| metapopulation / spatial gene flow | CDMetaPOP; Geonomics; RangeShiftR depending on question |
| dispersal / colonization / range expansion | RangeShiftR / RangeShifter |
| ecosystem / trophic opportunity | existing ARCANA ecology first; Madingley-class provider if justified |
| climate / paleoclimate | exact ARCANA bound climate/paleoclimate authority first; specialist climate provider only if a real gap remains |
| hydrology / freshwater | exact ARCANA hydrology authority first; specialist hydrology/GIS provider only after source audit |
| terrain / drainage topology | existing ARCANA channel/topography products first; specialist GIS/drainage library if needed |
| human demography / settlement | ARCANA weighted-population/settlement layer, with specialist providers only for bounded subproblems |
| trade / network connectivity | ARCANA macrohistorical layer plus validated graph/network methods for bounded computations |
| polity / war / collapse | ARCANA macrohistorical model; external tools may provide bounded evidence but cannot write history/canon |

---

## 7. Hydrology-specific rule

Hydrology is a concrete example of why this gate is mandatory.

Before adding or writing any freshwater model, inspect exact governed ARCANA hydrological inputs and the code that generated them. In particular, R5.17-B6 must inspect the exact R3.14-bound channel-hydrology source/payload before deciding that a new hydrology engine is required.

The current source path referenced by R3.14 includes a `channel_hydrology_state_I.npz` input class and hydrological quantities used by the paleoclimate code. Those semantics must be adjudicated before replacement or duplication.

Decision order for R5.17-B6 and analogous work:

```text
A. governed ARCANA hydrology already sufficient
   -> REUSE_CANONICAL_ARCANA

B. governed topology/drainage sufficient but bounded derivation missing
   -> reuse authority + minimum specialist derivation

C. physical water balance/reliability genuinely missing
   -> evaluate a dedicated hydrology provider

D. no suitable provider can preserve ARCANA semantics
   -> minimum custom ARCANA hydrology implementation
```

Potential future hydrology/GIS tools may be investigated only as **candidates** until explicitly audited, version-pinned and validated. Examples such as drainage-routing libraries or distributed hydrological models are not automatically authorized by being listed here or in a stage discussion.

Relative precipitation, hazard indices, wetland forage, aridity, ocean-circulation freshwater forcing or a generic habitat-water score must not be silently relabelled as physical terrestrial freshwater supply.

---

## 8. External provider governance

Every external scientific engine/provider remains subordinate to ARCANA governance.

Mandatory rules:

- no provider is an implicit canonical writer;
- no majority vote between engines defines ARCANA history;
- an engine result is evidence until explicitly adjudicated;
- input authority and exact source identity must be recorded where material;
- executable/package/runtime version must be pinned for production evidence;
- seeds and ensemble design must be recorded for stochastic runs;
- configuration and adapters must be repository-tracked when they affect interpretation;
- output manifests/hashes and validation summaries must be retained where appropriate;
- provider outputs must not silently mutate SEALED parent authority;
- disagreements between providers are scientific evidence to adjudicate, not errors to hide.

A new external provider requires an explicit suitability decision before its first production use. Reusing an already validated provider still requires a stage-local statement that its assumptions match the current question.

---

## 9. Custom-code rule

Custom ARCANA computation is valid when ARCANA-specific coupling or governance makes it necessary, but its scope should be minimal.

Custom code is preferred when, for example:

- no specialist engine represents the required process;
- available tools cannot preserve ARCANA's changing geography/state semantics;
- the missing operation is a transparent transformation/adapter rather than a full scientific model;
- integration of a large external engine would add assumptions greater than the scientific value it provides.

Custom code must not reimplement mature domain science merely to avoid evaluating the appropriate specialist tool.

---

## 10. Long-run and local-runtime rule

Scientifically useful long executions are allowed on local hardware.

When a provider run is material to a stage, repository-track as applicable:

```text
configuration
runner/adapter
runtime identity and versions
input authority/hashes
seeds and ensemble design
validation checks
logs or compact summaries
output manifest/hashes
adjudication result
```

Interactive-session cost is not a reason to omit scientifically valuable provider evidence.

---

## 11. Stage and seal rule

This policy does **not** itself:

- authorize a new scientific stage;
- authorize a new provider run;
- promote any CANDIDATE to SEALED;
- complete R5.17-B6;
- materialize freshwater support or `K(x,t)`;
- permit canonical mutation.

It is a persistent selection gate that every applicable stage must consult before choosing its computation path.

When an applicable stage intentionally departs from this policy, the stage artifact must state why the departure is scientifically justified.

---

## 12. Bootstrap rule for future conversations

When continuing ARCANA WorldSim:

1. read `ARCANA_WORLD_CURRENT_STATE.md`;
2. inspect `SIMULATION_RESULTS/MANIFEST.json` / `SEMANTIC_CATALOG.md` for existing results;
3. apply this `SCIENTIFIC_ENGINE_SUITABILITY_GATE.md` before designing new scientific computation;
4. retrieve historical artifacts only when targeted provenance or semantics require them.

This gate is the standing reminder that **the scientific question chooses the tool; the tool does not choose the scientific question**.

---

Formalized: 2026-09-11 (Europe/Rome project date).
