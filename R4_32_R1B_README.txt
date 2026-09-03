v0.6D1-R4.32-R1B — Native Geonomics Static Validation Introspection

Purpose
-------
R4.32 live root blocked at 28/29 because only 1/3 Geonomics parameter manifests
were static-valid. R4.32-R1 generic diagnostic recognized zero candidates because
it assumed a schema that did not match the native R4.32 serialization.

This overlay is diagnostic-only. It does NOT repair or weaken R4.32.
It introspects the actual project root and:
  * locates the R4.32 implementation source by canonical gate/count tokens;
  * locates native JSON evidence without assuming job_id field names;
  * finds J14/J18/J21 anywhere in nested manifest contexts;
  * reports explicit static_valid=false / false-like mapping fields;
  * preserves source context and JSON snapshots in a detailed report.

Governance
----------
No Geonomics execution.
No target numeric execution.
No readjudication.
No canonical-state change.
No gate weakening.
Failed R4.32 evidence remains preserved.

Run
---
.\run_v0_6D1_R4_32_R1B_native_introspection.ps1

Detailed report
---------------
outputs\v0_6D1_R4_32\R4_32_R1B_NATIVE_GEONOMICS_STATIC_VALIDATION_INTROSPECTION.json
