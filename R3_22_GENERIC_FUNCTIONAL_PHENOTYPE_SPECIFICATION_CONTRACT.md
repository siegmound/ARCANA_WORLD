# v0.6D1-R3.22 — Generic Functional Phenotype State-Space Specification, Trade-Off Governance & Replay Interface

## Status

`CANDIDATE — SPECIFICATION ONLY / NO PHENOTYPE VALUES / NO BIOLOGY REPLAY`

## Parent authority

R3.22 may run only above the SEALED R3.21 final audit:

`PASS_R321_H0_PRESENT_LINEAGE_REGISTRY_HISTORICAL_CLOSURE_AND_FUNCTIONAL_PHENOTYPE_FORK_READINESS_SEALED`

Required parent closure:

- 43/43 R3.21 final seal checks PASS;
- R3.19 JSON SHA-256 `658e5da006f1a5c1d499090cc2a07ff0c1058f6f253b5c90d639eabbbd68fc71`;
- R3.19 NPZ SHA-256 `f5aa7f0828baeee2d5fd6221797229c0a4e25b787d157095e7652d3b81c56406`;
- 134 present species;
- 295 present components;
- Deep biological coupling OFF.

R3.22 does not reopen R3.19, R3.20 or R3.21.

## Scientific objective

R3.22 defines a **generic, multivariate functional phenotype state space** that can later be calibrated and replayed for every biological lineage without selecting a human lineage, sapience target, civilization target or author-desired endpoint.

The stage answers only:

> What biologically generic state variables, applicability gates, covariance structure, costs and derived-capability dependencies must exist before a functional-phenotype evolution replay is scientifically admissible?

It does **not** answer:

- which lineage is human-like;
- which lineage is most intelligent;
- which lineage will use tools;
- which lineage is a candidate for H1;
- what numerical phenotype any of the 134 species has.

## State granularity

Primary functional state is **component-level**.

The 295 components are the authoritative future state units. Species-level values are downstream population-weighted summaries over applicable components only.

This preserves:

- within-species geographic differentiation;
- local adaptation;
- future gene flow and admixture effects;
- divergence among demes/components before speciation.

A single scalar phenotype per species is forbidden as the primary runtime representation.

## Reserved domains from R3.21

R3.22 formalizes exactly the ten generic domains reserved by R3.21:

1. manipulative capability;
2. locomotor flexibility;
3. cognitive capacity;
4. learning/plasticity;
5. sociality;
6. dietary flexibility;
7. life-history;
8. ecological generalism;
9. tool-use potential;
10. environmental problem-solving capability.

The first eight domains are represented by primary evolvable vectors. The final two are **derived contextual capabilities**, not direct genetic state variables.

## Primitive functional trait space

R3.22 defines 31 primary traits:

### Manipulative capability

- M1 effector independence;
- M2 force precision span;
- M3 workspace control;
- M4 sensorimotor feedback resolution.

### Locomotor flexibility

- L1 locomotor mode breadth;
- L2 substrate breadth;
- L3 transition control;
- L4 effector-locomotor decoupling.

### Cognitive capacity

- C1 working-memory integration;
- C2 inhibitory control;
- C3 relational integration;
- C4 causal model depth.

No single `intelligence` scalar is introduced.

### Learning/plasticity

- P1 acquisition efficiency;
- P2 retention stability;
- P3 cross-context transfer;
- P4 developmental behavioral plasticity.

### Sociality

- S1 social tolerance;
- S2 coordination capacity;
- S3 social-learning fidelity;
- S4 communication repertoire bandwidth.

### Dietary flexibility

- D1 trophic resource breadth;
- D2 digestive processing breadth;
- D3 resource switching flexibility.

### Life-history

- H1 maturation duration;
- H2 reproductive output rate;
- H3 parental investment;
- H4 adult survival horizon.

### Ecological generalism

- G1 habitat breadth;
- G2 climatic tolerance breadth;
- G3 disturbance resilience;
- G4 colonization breadth.

## Applicability governance

Not every trait is biologically meaningful for every lineage.

R3.22 therefore separates **trait applicability** from **trait magnitude**.

Future applicability states:

- `ACTIVE`;
- `STRUCTURAL_ZERO`;
- `NOT_APPLICABLE`;
- `UNKNOWN`.

A `NOT_APPLICABLE` trait may not become active merely by continuous Gaussian drift. Activation requires a separately governed morphological or functional innovation event in the future replay.

This prevents the functional layer from manufacturing unsupported anatomical innovations by continuously increasing an abstract score.

R3.22 assigns no applicability states yet.

## Latent coordinate semantics

Primary trait coordinates are future empirical latent variables on the real line.

Higher values mean only **more of the named function**, not higher global fitness, intelligence, evolutionary progress or human similarity.

Fitness effects are environment-dependent.

Empirical observables remain separate from latent coordinates and require comparative calibration before any state is materialized.

## Future quantitative-genetic state

R3.22 reserves the following future component-level state:

- `functional_applicability_code[component, trait]`;
- `functional_mean_z[component, trait]`;
- `functional_va[component, trait]`;
- `functional_gcov[component, trait, trait]`;
- `functional_plasticity_beta[component, trait, environment_driver]`.

The active-trait submatrix of `functional_gcov` must be:

- finite;
- symmetric;
- positive semidefinite.

No numerical G-matrix is created in R3.22.

The existing R3.19/R3.21 reduced three-trait ecological genetic state is preserved separately and is **not repurposed** as the new functional phenotype state. Cross-covariances with those ecological traits are undefined until independently calibrated.

## Expression and evolution form

R3.22 reserves only the model family:

`z_expressed = z_genetic_mean + B_plasticity @ E_centered + developmental_residual`

and the future multivariate quantitative-genetic update family:

`delta_z = G_functional @ beta_selection + gene_flow + drift + mutation_input`

No coefficients, selection gradients, mutation inputs, covariance strengths or plasticity slopes are assigned in this stage.

## Derived capabilities

### Tool-use potential

`T_tool_use_potential` is a contextual derived capability depending on manipulation, sensorimotor control, cognitive integration, learning and local object affordances.

It is not a direct heritable trait and cannot be selected as an author target.

### Environmental problem-solving

`Q_environmental_problem_solving` is a contextual derived capability depending on cognition, learning/plasticity, sensorimotor exploration and ecological novelty/opportunity.

It is not a direct heritable trait and cannot be selected as an author target.

The numerical aggregation functions remain undefined until empirical calibration.

## Trade-off governance

R3.22 defines mechanistic classes that must later be calibrated, including:

- neural/behavioral energetic allocation;
- offspring-number vs per-offspring investment;
- shared-effector morphological constraints;
- dietary generalist/specialist frontiers;
- ecological generalist/specialist frontiers;
- costs and benefits of sociality;
- developmental-time/learning-window coupling.

R3.22 does **not** author-assign numerical correlation coefficients or trade-off strengths.

## Empirical calibration gate

No functional value or replay is authorized until a later calibration stage addresses:

- comparative multi-taxon evidence;
- phylogenetic non-independence;
- allometric effects where relevant;
- measurement and proxy uncertainty;
- observable-to-latent mappings;
- heritability / additive variance evidence;
- covariance calibration;
- metabolic/ecological cost calibration;
- held-out validation where data permit.

Humans may eventually appear as one taxon in comparative evidence, but may not define the scale or target.

Deep/noetic exposure is excluded from this calibration and replay branch.

## Forbidden in R3.22

- materializing values for any lineage/component;
- selecting a human candidate;
- human-likeness ranking;
- sapience score;
- civilization potential score;
- assigning tool use directly as a gene/trait;
- assigning problem-solving directly as a gene/trait;
- author-set heritability or covariance numerics;
- repurposing the existing three R3.19 ecological reduced traits;
- enabling Deep biological coupling;
- advancing biological time;
- mutating H0 or CHA-2.

## Candidate outputs

A successful local run writes:

- `R3_22_FUNCTIONAL_PHENOTYPE_SPECIFICATION.json`
- `R3_22_PRIMITIVE_TRAIT_CATALOG.json`
- `R3_22_DERIVED_CAPABILITY_GRAPH.json`
- `R3_22_CONSTRAINT_AND_TRADEOFF_GOVERNANCE.json`
- `R3_22_REPLAY_STATE_INTERFACE.json`
- `R3_22_EMPIRICAL_CALIBRATION_REQUIREMENTS.json`
- `R3_22_AUDIT_SUMMARY.json`
- `R3_22_AUDIT.md`
- `R3_22_OUTPUT_MANIFEST.json`

## Natural successor

R3.22 does not authorize immediate human-readiness scoring.

The next scientific task after R3.22 closure is a comparative calibration / ancestral-state stage that estimates the new functional variables without using a human endpoint, followed by a governed evolutionary replay of those traits.
