# ARCANA WorldSim v0.6D1-R4.9

## Additional Matched-Control Replicate Expansion & Causal Direction Resolution

R4.9 is the fixed evidence-expansion stage authorized by the SEALED R4.8 result `MATCHED_CONTROL_EFFECT_UNCERTAIN`.

It does **not** alter R3.11, any canonical parameter, the R4.7 repaired evidence, or the R4.8 matched-control evidence. It adds one pre-result-frozen set of 16 new paired CDMetaPOP J09 executions, bringing the paired evidence set from 4 to 20.

### Frozen design

- Parent pairs: 4, preserved and not rerun.
- Additional pairs: exactly 16.
- Final paired sample: exactly 20.
- Each new pair uses the same seed in the dynamic and neutral arm.
- Dynamic arm reuses the R4.7 CDMetaPOP forcing-parity semantics and J09 dynamic end-support ratio.
- Neutral arm reuses the R4.8 matched-control semantics with end-support ratio exactly 1.0.
- Start state, N0 policy, K start, migration/gene-flow settings, runtime and engine version remain matched.
- ARCANA comparison targets are never injected into CDMetaPOP.

### Adjudication

R4.9 reuses the R4.4 ratio neutral factor (1.05) and the R4.8 q10-q90 robustness rule. No adaptive stopping is allowed. If the fixed 20-pair evidence remains uncertain, R4.9 does not automatically request another arbitrary replicate increase; it routes to a separate precision/alternate-evidence closure stage.

### Forbidden actions

- canonical replay;
- canonical parameter change;
- Deep biological coupling;
- majority vote;
- result-selected seeds, sample size, thresholds or stopping;
- rewriting R4.7/R4.8 parent evidence.
