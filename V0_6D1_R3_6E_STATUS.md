# ARCANA WorldSim v0.6D1-R3.6E Status

Status: **CAUSAL INFERENCE GATE PASS — STRUCTURAL ADMIXTURE OPERATOR MISMATCH SUPPORTED; CALIBRATION NOT AUTHORIZED**

Evidence authority:
- real NEMO 2.4.2 pilot: 40/40 executed, 40/40 qfreq parsed;
- N=500 and 2000;
- 2 replicates;
- B0, B1 and C3;
- matched FLOW / NO-FLOW controls;
- 64-QTL analytic polygenic reference.

Primary finding:
ARCANA whole-trait moment mixing injects ~114–127x more admixture VA than the analytic polygenic reference, while NEMO remains within the same order of magnitude as that analytic reference. The current operator is therefore promoting population-structure / ancestry covariance into durable within-deme additive variance.

No production calibration is authorized yet because N sensitivity and replicate depth remain limited and the replacement operator has not been designed/validated.
