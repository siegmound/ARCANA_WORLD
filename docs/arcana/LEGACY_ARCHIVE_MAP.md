# Legacy Archive Map

Historical R3/R4/R5 files are recoverable from Git history. This map records
family-level disposition; a retained current dependency remains at its
current path. Archive decisions do not demote referenced scientific authority.

| Family | Historical contribution | Current disposition |
|---|---|---|
| `README_R3_*`, `README_R4_*`, `README_R5_*` | Stage entrypoints and handoffs for historical simulation/engine work | Remove only when no current R6 contract, test, builder or authority map names the file; prior bytes recoverable from Git history. |
| `NEXT_STAGE_HANDOFF_*` | Human continuation prompts between completed stages | Historical-only when not referenced by current R6; remove from current surface after dependency checks. |
| `run_v0_6D1_R3_*`, `run_v0_6D1_R4_*`, `run_v0_6D1_R5_*` and stage launch/verification helpers | Reproducibility and stage-specific validation workflows | Keep if an active test/source path consumes them; otherwise historical-only one-shot runner, recoverable from Git history. |
| R3/R4/R5 authority, contracts and reuse maps | Scientific provenance, reusable algorithms and explicit R6 parent references | Retain exact files still referenced by current R6; do not delete merely by prefix. |
| `outputs/`, `local_runs/`, `SIMULATION_RESULTS/` | Historical runs, evidence, copies and replay inputs | Outside this cleanup wave; preserve pending hash/consumer/data audit. |

The C0-E ledger lists exact removed counts and retained exceptions for this
cleanup. The Git commit history is the recovery path for removed historical
documentation and one-shot scripts.

## PRE-B0 consolidation status

C0 root cleanup and C0-F2 high-confidence data cleanup are complete. C0-F3
and F4 retained remaining historical payloads conservatively because semantic
record identity and full reproducibility are not established for every copy.
The default pytest configuration selects active `test_r6_*.py` modules;
historical R1–R5 stage tests remain available for explicit invocation, while
run/evidence snapshots are not default test roots. The execution reference
index is regenerated navigation metadata, not authority.
