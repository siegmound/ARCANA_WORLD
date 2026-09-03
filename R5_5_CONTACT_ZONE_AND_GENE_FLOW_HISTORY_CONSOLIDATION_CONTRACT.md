# ARCANA WorldSim v0.6D1-R5.5 — Contact-zone and gene-flow history consolidation

## Scientific question
Given the twelve robust R5.1 cradle families, the J14 spatial trajectories, R5.3 CDMetaPOP demographic persistence evidence and R5.4 NEMO FLOW-vs-no-flow evidence, where and when do the two hominin candidate lineages have **spatial contact opportunities**, and what demographic/genetic context accompanies those opportunities?

R5.5 is a **scientific candidate stage**, not a sealing stage.

## Engine utility adjudication
No new external engine is useful for the R5.5 question. RangeShiftR, CDMetaPOP and NEMO have already supplied the connectivity, demography and genetic-robustness evidence needed for this consolidation. Re-running them would add cost and risk circularity without adding a new scientific axis. SLiM is deferred to R5.6 because ancestry/admixture simulation only becomes well-posed after R5.5 has produced explicit contact-opportunity windows.

## Spatial authority
Contact windows are computed ARCANA-native from matched J14 ensemble states, restricted to the same family network reconstruction used in R5.3: R5.1 q99 core plus downstream J14 occupancy, fixed maximum 32 cells. R5.2 RangeShiftR geometry, R5.3 CDMetaPOP values and R5.4 NEMO values do not create, move or delete a contact window.

## Contact semantics
For each of the 7 robust `RPT_010_D02` families × 5 robust `RPT_009_D02` families = 35 cross-lineage pairs, R5.5 evaluates matched J14 ensemble members at every age where both families already exist.

Two spatial diagnostics are retained:
- exact cell overlap;
- one-grid-cell Chebyshev proximity, including exact overlap.

The latter is a **contact opportunity**, not realized mating, not realized gene flow and not admixture.

Fixed descriptive support thresholds are 0+, 25%, 50%, 75% and 100% of matched ensemble members. They form a nested reporting family and are not a majority vote or truth-selection mechanism.

## Cross-engine context
For every contact pair × the three fixed demographic stress profiles, R5.5 carries side-by-side:
- R5.3 CDMetaPOP extinction, minimum-population, He and allele-retention diagnostics;
- R5.4 NEMO FLOW-minus-matched-no-flow diagnostics.

No agreement score, forced metric equality, weighted score, single history winner or automatic scientific PASS/FAIL is authorized.

## Outputs
R5.5 produces:
- a pairwise contact-zone history registry;
- an NPZ temporal atlas of exact and one-cell contact support fractions;
- a 35×3 cross-engine contextual registry;
- immutable candidate-parent hash binding;
- integrated audit and output manifest.

## Closure policy
R5.5 remains CANDIDATE. R5.3–R5.6 are intended to close as one larger demographic/genetic-history milestone rather than as micro-seals.
