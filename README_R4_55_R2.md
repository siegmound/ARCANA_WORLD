# ARCANA WorldSim v0.6D1-R4.55-R2

R4.55-R1 closed preexecution authority 21/21 PASS with zero binding errors.
The next failure was a PowerShell parser error before the first scientific engine.

Observed:
`}throw "unsupported path ..."` inside the minified bridge.

R2 rewrites the same bridge in readable PowerShell with explicit token boundaries.
It preserves adapter dispatch, `$CondaBasePython` / `$BasePyQ` NEMO architecture,
timeouts, WSL ownership, resume behavior and raw-evidence failure handling.

Prepatch SHA256:
`40314e492426c55043a68ea147444933c83076b420957591bf1c22db1f079799`

Postpatch SHA256:
`e3e607a5a9a9d1154d507797ce93f70f12680f1041ba6d7672e771cddc2d7111`

No scientific engine executed before this parser failure.

Run:
```powershell
.\run_v0_6D1_R4_55_R2_powershell_bridge_repair_and_reseal.ps1
```
