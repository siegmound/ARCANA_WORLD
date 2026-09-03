# v0.6D1-R5.6 — Targeted Ancestry and Admixture Challenges

## Scientific question
Given the ARCANA-native cross-lineage contact-opportunity histories produced by R5.5, what ancestry persistence and tract structure can emerge under fixed neutral gene-flow challenges?

R5.6 does **not** infer a unique realized admixture history and does not promote a SLiM output into canon.

## Engine utility review
SLiM 5.2 is useful at this stage because R5.5 now supplies temporal contact availability while SLiM supplies forward-time recombination and tree-sequence ancestry. `tskit==1.0.3` is used to recover true local ancestry from remembered founder roots. `msprime` and `pyslim` are not required by R5.6 and are not used merely because they exist in the historical runtime environment.

No additional RangeShiftR, CDMetaPOP, NEMO, Geonomics, or Madingley execution is useful for this objective.

## Authority separation
- R5.5 determines only whether a pair has one-cell contact opportunity at each of the 141 J14 age states.
- Any positive matched-ensemble support activates the binary contact state. The support fraction is **not** converted into a migration rate.
- Identical binary schedules may be deduplicated computationally; all 35 pair identities remain mapped to the schedule and none is ranked or dropped.
- One R5.5 age state maps to one standardized SLiM reproductive transition solely as computational indexing; this is not a literal hominid generation clock.

## Fixed challenge family
For every unique contact schedule and seed `{560601,560602}`:
- `NO_FLOW`: 0.0
- `LOW_BIDIRECTIONAL`: 0.005
- `HIGH_BIDIRECTIONAL`: 0.02

The high rate preserves the previously governed R4.1 SLiM two-population challenge magnitude; the low rate is a predeclared lower sensitivity challenge. Neither is fitted to R5.3, R5.4, R5.5, or to resulting ancestry.

The model is neutral: two populations of 200 diploid individuals, 1 Mb sequence, recombination rate `1e-8/bp`, mutation rate 0, tree-sequence recording enabled. Founders are permanently remembered so local ancestry can be traced to source population roots.

## Authorized readout
For each direction (`p2→p1`, `p1→p2`):
- mean donor ancestry fraction;
- haplotype ancestry min/max;
- fraction of final haplotypes with any donor ancestry;
- donor ancestry tract count;
- mean and maximum donor tract length;
- tree-sequence integrity metadata.

`NO_FLOW` cross-ancestry must be exactly zero as a model-integrity control. LOW/HIGH values never cause automatic scientific PASS/FAIL and are not required to be monotonic.

## Governance
No majority vote, weighted score, result-selected tuning, pair winner, ancestry-history winner, canonical rewrite, or Deep biological coupling. R5.6 remains a candidate. If R5.6 completes, the natural next step is one integrated R5.3–R5.6 scientific block audit/seal rather than another micro-seal.
