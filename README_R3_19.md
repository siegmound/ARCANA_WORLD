# R3.19

Stage: **v0.6D1-R3.19 — Recent H0 Phase-Aware Transport Coupling & 125 ka -> 0 Biology Macrostep Closure**

Run after R3.18 is SEALED.

```powershell
.\verify_v0_6D1_R3_19_patch.ps1
.\run_v0_6D1_R3_19_checks.ps1
.\run_v0_6D1_R3_19_phase_aware_transport_closure.ps1
```

The canonical run executes one 125 kyr biology step and exactly two 62.5 kyr transport updates. A constant-forcing bit-exact R3.8 equivalence gate is executed before the variable-forcing canonical branch.

If exact 0 ka support consistency fails, the runner fails closed and writes a diagnostic rather than a canonical checkpoint.


## R3.19-R2 endpoint-support repair

The phase-aware transport forcing remains time-integrated over two 62.5 kyr phases. Discrete `accessible` topology is now bound to the exact 0 ka provider endpoint. After phase 2, any population on cells that are accessible in the phase-average forcing but inaccessible at exactly 0 ka is conservatively reconciled with the existing SEALED `remap_to_land` operator. This is an operator-order/topology binding repair, not a parameter or cadence change. The constant-forcing case with identical endpoint support remains bit-exact to SEALED R3.8.
