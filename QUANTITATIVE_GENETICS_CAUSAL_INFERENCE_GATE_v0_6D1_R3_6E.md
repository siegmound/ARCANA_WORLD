# v0.6D1-R3.6E — Quantitative-Genetics Causal Inference Gate

## Scope

R3.6E consumes the completed real NEMO 2.4.2 pilot from R3.6D (40/40 executed, 40/40 parsed) and asks one narrow question:

> Is the persistent R3.5 VA problem primarily caused by cadence/homeostasis, or by the semantics of the current ARCANA admixture moment-mixing operator?

No canonical parameter is changed in this stage.

## Independent evidence

Three references are compared on the same R3.6B/C benchmark states:

1. ARCANA whole-trait `gene_flow_moment_mix` at 1x125 kyr.
2. ARCANA rate-normalized 5x25 kyr moment mixing.
3. NEMO 2.4.2 explicit 64-QTL forward-time reference with matched no-flow controls.
4. An analytic infinite-population polygenic reference derived from the same QTL effects/frequencies and the same cadence-normalized interval transition matrix.

The analytic additive-genetic update is

`VA = 2 * sum_l a_l^2 p_l (1-p_l)`

and after finite interval migration

`p' = D p`.

This reference has no finite-N drift noise.

## Decisive result

For B1, ARCANA's admixture-only increment is ~126.96–127.00 times the polygenic analytic increment. With 64 aligned loci, the theoretical maximum amplification of whole-trait between-mean variance relative to genic variance is approximately `2L = 128`; the observed result is therefore diagnostic rather than accidental.

Across B1 and C3, ARCANA 1x125k is ~114–127x above the analytic polygenic reference. NEMO is only ~0.45–2.68x the analytic reference across N=500/2000 and two replicates, i.e. the same order of magnitude despite finite-N noise.

NEMO FLOW runs also retain strong between-deme structure (`Qst` minimum >0.90), while within-deme `Va` remains small. This shows that the divergent deme means largely remain population structure rather than becoming durable within-deme additive variance.

## Mechanism

The current ARCANA moment mixer uses the variance identity for a mixture of whole trait distributions:

`Vmix = weighted(Vwithin) + m(1-m)(mean1-mean2)^2`.

That identity is correct for the variance of a pooled mixture, but the second term is not generally equal to durable within-deme additive genetic variance after mating/recombination.

For a polygenic additive architecture under linkage equilibrium, the admixture increment in genic variance is instead proportional to

`2 m(1-m) sum_l a_l^2 (Delta p_l)^2`,

whereas the whole-trait term is proportional to

`4 m(1-m) (sum_l a_l Delta p_l)^2`.

The latter includes cross-locus ancestry covariance. With many aligned loci it can be ~`2L` larger. Free recombination in NEMO destroys most of that covariance rather than preserving it as standing within-deme VA.

## Verdict

`STRUCTURAL_ADMIXTURE_OPERATOR_MISMATCH_SUPPORTED__CALIBRATION_NOT_YET_AUTHORIZED`

The evidence supports:

- cadence is a secondary effect, not the principal cause;
- `b` is not yet demonstrated to be underpowered;
- `mu` is not yet demonstrated to be wrong;
- raising the VA ceiling remains unjustified;
- the current whole-trait moment-mixing variance update is the primary repair target.

## Governance

R3.6E does NOT authorize:

- canonical writes;
- automatic calibration;
- changes to `mu` or `b`;
- changes to `q*=0.045`;
- ceiling changes;
- resuming canonical 150 Ma continuation.

## Next stage

The next governed step should design a segregation/recombination-aware moment representation. Preferred direction:

- keep deme trait means as now;
- keep true within-deme additive variance separately;
- represent admixture-generated ancestry/linkage covariance as a transient reservoir rather than immediately promoting all between-mean variance into `VA`;
- decay/convert that reservoir according to recombination/polygenic architecture;
- validate the reduced operator against the NEMO and analytic references before rerunning 210→150 Ma.
