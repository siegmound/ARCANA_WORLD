# v0.6D1-R3.17 — Seal Gate

This gate seals the completed exact 120 ka environmental restart while preserving the SEALED R3.16 biology state at 125 ka.

Canonical received artifacts:
- restart envelope SHA-256: `5b800279324afdd19279fa0c395ace822b4104155690191f81c6be884d2aeca8`
- pending exposure accumulator SHA-256: `b191faae44b4db8bc0afaaba942b0f04087758fa554c480375eb0f753ab309cc`

The sealed audit:
1. requires the R3.16 `193/193` SEALED parent authority;
2. verifies the exact canonical R3.17 artifact hashes and semantics;
3. independently rebuilds the 125→120 ka C2 exposure from the SEALED provider/clock;
4. requires array-exact equality between the recomputed and stored pending exposure accumulator;
5. requires exact R3.16 biology-state identity before/after the replay;
6. requires zero population mass on cells becoming inaccessible at 120 ka;
7. preserves the 125 kyr biology cadence, 62.5 kyr transport cadence, gene-flow cadence, H0 Deep OFF, and all scientific parameters.

Run:

```powershell
.\verify_v0_6D1_R3_17_seal_gate_patch.ps1
.\run_v0_6D1_R3_17_sealed_checks.ps1
```

The expected sealed verdict is:

`PASS_R317_EXACT_120KA_ENVIRONMENTAL_RESTART__125KA_BIOLOGY_STATE_AND_5KYR_PENDING_EXPOSURE_SEALED`
