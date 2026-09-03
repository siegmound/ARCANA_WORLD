# R3.9 Diagnostic Smoke Audit

The diagnostic path loads the **sealed R3.8 150 Ma checkpoint by hash** and advances one ordinary 125 kyr cadence to 149.875 Ma.

Result: PASS.

- R3.8 checkpoint JSON/NPZ authority: valid
- CHA-1 exact-event pulse authority: valid
- biology steps: 1
- Deep biological coupling: OFF
- CHA-1 applied: NO

This smoke validates restart input and ordinary continuation mechanics only. It does not authorize the 66.0 Ma PRE_CHA1 checkpoint; that requires the full governed 672-step local run.
