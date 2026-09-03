# v0.6D1-R4.3-R1 — NEMO Host-Control Runtime Repair

Status: implementation repair candidate.

Observed first full R4.3 execution: J10/J13/J17 (all and only NEMO jobs) returned bridge code 127 while R4.0 fresh evidence still confirmed NEMO 2.4.2 READY and the other 20 jobs produced terminal evidence. The blocked completeness audit reported 17 SCIENTIFIC_RESULT, 3 SEMANTIC_NONCOMPARABILITY and 3 ADAPTER_FAILURE.

Root cause class: host-control invocation defect, not scientific disagreement. The original R4.3 bridge invoked `python` inside the `arcana-nemo242` engine environment. The R4.1 SEALED NEMO microbenchmark instead invoked NEMO from a shell in that environment; Python was never part of the engine-runtime contract.

Repair: use the Miniforge/base control Python only for adapter orchestration. The actual engine invocation remains `conda run -n <pinned NEMO env> nemo2.4.2 R43.ini`.

Frozen scientific content unchanged: 23 job IDs, seven windows, 92 seeds, per-job semantic/unit mappings, NEMO 2.4.2 pin, representative 120-generation response runtime, migration/initial-frequency drivers, canonical state, Deep=OFF, no majority vote, no adjudication.

Repair execution mode `-RepairNemo` reruns exactly the three frozen NEMO jobs and preserves the earlier blocked evidence before recollecting all 23 bundles.
