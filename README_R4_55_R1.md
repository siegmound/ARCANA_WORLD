# ARCANA WorldSim v0.6D1-R4.55-R1

Narrow repair for the first R4.55 preexecution block.

No scientific engine was executed in the blocked run.

Root causes:
1. R4.55 incorrectly treated list ordering of the four R4.52 seeds as scientific authority.
   The exact scientific authority is the four unique `job × seed` identities; historical
   contracts retain their own replicate ordering.
2. The R4.3 ENGINE_CONFIG parser hard-coded `seed_1..seed_4`, while the historical
   configs use four indexed seed entries including `seed_0`.

Repair:
- exact four unique seed membership, order-insensitive;
- scan exactly four `seed_<integer>` config keys and sort only for deterministic parsing;
- same exact membership check for raw evidence;
- no seed value, contract, adapter, metric, threshold, target, or canonical state changes.

Prepatch module SHA256:
`cca9ac0297cd574531651a62e814c0d9cebbcd1d3b8b6c274976943eedcfa353`

Postpatch module SHA256:
`870001cabd0708ca1c2ccb8c1fc23987af6daf7635fe2fb590901ed63df57a20`

Run:
```powershell
.\run_v0_6D1_R4_55_R1_seed_ledger_repair_and_reseal.ps1
```
