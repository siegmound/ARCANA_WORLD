# R3.17 Operator/Cadence Audit

## Question
Can the 5 kyr residual interval 125→120 ka be represented as 4% of a normal R3.8 biology step?

## Result
**No.** R3.8 is not a set of mutually independent continuous ODEs. It is a governed composed operator.

### dt-continuous internals
The following implementations accept `dt` mathematically:
- species demography relaxation;
- trait response;
- non-flow additive-variance ODE;
- intrinsic-RI/isolation-clock accumulation.

### Fixed/per-step internals
The following cannot be fractionally invoked under current authority:
- barrier migration: absolute 62.5 kyr transport cadence;
- segregation-aware gene flow/recombination: one exchange application per 125 kyr biology step;
- speciation/extinction/fission/coalescence: governed cadence/gate evaluation;
- closed-loop reduced genetic state updates are ordered around the same selection/gene-flow/variance sequence.

Applying only the first group over 5 kyr would change operator ordering and therefore constitute new biology. Applying the second group over 5 kyr would explicitly violate sealed cadence.

## Chosen solution
R3.17 is a **deferred-biology dual-clock restart**:
- exact environment reaches 120 ka;
- the biology state remains exact at 125 ka;
- 5 kyr environmental exposure is accumulated for the still-open 125→0 biology macrostep.

This solution changes no biological parameter and is exactly composable into a future 125-kyr update.

## Relevant inherited evidence
- R2.1 established 125 kyr biology / 62.5 kyr transport as internal cadence independent of external chunking.
- R3.7G promotion preserved these cadences.
- R3.16 proved adaptive environmental substeps must not become biology steps.
- R3.10 provides precedent for physical/event time advancing while ordinary lifecycle time is intentionally frozen during a special bridge.
