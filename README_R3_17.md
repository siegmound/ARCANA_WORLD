# v0.6D1-R3.17 — Exact 120 ka Environmental Restart

R3.17 consumes the final ten 500-y C2 environmental intervals 125→120 ka **without executing a 5-kyr biology step**.

Outputs:
- `R3_17_120KA_DUAL_CLOCK_RESTART_ENVELOPE.json`
- `R3_17_PENDING_125_TO_120KA_EXPOSURE_ACCUMULATOR.npz`
- `R3_17_EXACT_120KA_ENVIRONMENTAL_RESTART_SUMMARY.json`

The R3.16 125 ka checkpoint remains the biological state authority. The new envelope records physical age 120 ka, biology age 125 ka, 5 kyr pending exposure, 57.5 kyr to the next transport boundary and 120 kyr to the next biology boundary.

Candidate validation:
- R3.17 tests: 9/9 PASS;
- inherited R3.16 tests: 11/11 PASS;
- inherited R3.15 tests: 12/12 PASS;
- inherited R3.14 + portability tests: 13/13 PASS;
- immediate regression: 45/45 PASS;
- formal candidate audit: 161/161 PASS.

Local sequence:

```powershell
.\verify_v0_6D1_R3_17_patch.ps1
.\run_v0_6D1_R3_17_checks.ps1
.\run_v0_6D1_R3_17_recent_restart_sync.ps1
```

R3.18 must combine the pending 5 kyr exposure with 120→0 recent exposure before one full 125-kyr biology update.
