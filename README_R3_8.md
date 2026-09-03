# R3.8 — Canonical 150 Ma Continuation Checkpoint

R3.8 is SEALED. It materializes the first exact restartable World-1 H0 boundary after the R3.7I segregation-aware production promotion.

The canonical checkpoint is the JSON+NPZ pair under `local_runs/v0_6D1_R3_8/`. Both files are hash-bound in the sealed audit and contain all explicit state needed for continuation, including reduced genetics and lifecycle persistence registries.

Validation established:
1. exact exposed-state equivalence to the sealed R3.7I/R3.7H K_CENTER 150 Ma reference;
2. exact save/reload identity at 150 Ma;
3. exact full-state identity between direct and reloaded 150→149 Ma continuation.

Use `run_v0_6D1_R3_8_checks.ps1` to validate the sealed package. Do not regenerate the 150 Ma checkpoint for normal continuation; load the sealed one. Historical 210→150 replay is now an audit path, not a routine prerequisite.
