# ARCANA WorldSim — v0.6D1-R5.11
## R5.10 ↔ sealed R3.30 census-calibration / weighted-group-ABM reconciliation

### Purpose
R5.11 reconciles the R5.10 two-lineage 0 ka community-precondition handoff with the already SEALED R3.30 census-equivalent calibration, weighted residential-group ABM and late-Pleistocene community-history layer.

R5.11 is a **reconciliation/audit stage**. It does not rerun R3.30, does not execute an external engine, and does not create a new demographic or cultural history.

### Parent authority
- R5.10 must be an eligible candidate with 33/33 checks and the exact two-lineage cohort `RPT_010_D02 + RPT_009_D02`.
- R3.30 must remain byte-identical to its historical SEALED authority.
- R3.29 and R3.28 replay artifacts used by R3.30 must remain byte-identical to the already reconciled parent chain.

### Census-equivalent semantics
R3.30 materializes an absolute **census-equivalent calibration ensemble**, not an observed archaeological headcount and not canonical numeric population truth.

R5.11 independently revalidates that:
1. the 32×2 `Ne/N_total` draws are exactly regenerated from the frozen triangular calibration prior and seed;
2. the 200 ka census-equivalent anchor is exactly `R3.28 population_proxy / (Ne/N_total)`;
3. the 50→0 ka census-equivalent trajectory preserves only the sealed R3.28 relative population trajectory;
4. group sizes/counts and active/regional-network equivalents are exactly reconstructed from the sealed R3.29 community-precondition state and frozen R3.30 formulas.

The frozen numeric prior and group-size/network references are classified as **legacy evidence-calibrated diagnostic hyperparameters**, not observations and not canon.

### Weighted-group-ABM semantics
A stored R3.30 agent is a mesoscopic weighted representative of residential-group equivalents. It is not a person, literal camp, archaeological site or village.

R5.11 validates census/group conservation at all eleven anchors and preserves these interpretations:
- represented people → census-equivalent weight;
- represented camps → residential-group-equivalent weight;
- fission/fusion counts → reorganization equivalents, not observed events;
- CHA-2 disruption equivalents → diagnostic pressure, not destroyed camps;
- inter-lineage exchange → opportunity diagnostic, not realized gene flow or ancestry.

### Governance
- Both retained lineages remain in the handoff.
- The 25 R3.30 sensitivity variants remain diagnostic and cannot select a lineage or identity.
- No unique human identity, named culture, language, religion, agriculture, city/state or ethnicity is materialized.
- No literal absolute census, literal residential-group count, or literal fission/fusion event history is promoted.
- Deep biological coupling remains OFF.
- No canonical state is changed.
- R3.31 is **not auto-authorized**; it requires a separate reconciliation because it materializes abstract technological-ecology stocks.

### Output interpretation
R5.11 answers only whether the sealed R3.30 census/group layer can be safely reused as a governed diagnostic layer downstream of R5.10.
