# ARCANA WorldSim v0.6D1-R4.55

Actual scientific execution stage for the 20 remaining non-Geonomics R4.2 jobs.

Frozen scope:
- 20 jobs
- 4 R4.52 seeds/job
- 80 scientific streams
- 2 R4.53 metrics/stream
- 160 metric records

Dispatch:
- Madingley / RangeShifter: exact hash-bound R4.3 historical adapters.
- NEMO / SLiM / CDMetaPOP: exact R4.21 adapters authorized and executed under R4.22.
- CDMetaPOP additionally requires each R4.7 REPAIR_PROFILE.json with no comparison-target leakage.

R4.55 preserves RAW_ENGINE_EVIDENCE.json separately from SCIENTIFIC_READOUT_EVIDENCE.json.
It performs no numeric value adjudication, no majority vote, no target selection and no canonical write.

The runner is resumable:
- valid JOB_COMPLETE => skip;
- partial => archive and restart the same frozen job;
- completed but hash-invalid => fail closed.

Run:
  .\run_v0_6D1_R4_55.ps1

Next on SEALED:
BUILD_R456_MULTI_ENGINE_23_JOB_FULL_EVIDENCE_REVIEW_AND_FINAL_REVALIDATION_CLOSURE
