# ARCANA WorldSim v0.6D1-R4.42
## Geonomics Multi-Transition Bounded Replay & Production Execution Queue Authorization Preflight

Parent:
- R4.41 integrated 28/28 PASS
- R4.41 final seal 21/21 SEALED

R4.42 extends the validated single-transition mechanics across complete
canonical sequences while keeping the scope bounded.

## Bounded replay scope

### J14
- deterministic first frozen branch only
- 141 canonical states
- all 140 transitions
- 4 frozen seeds
- 560 transition validations

### J18
- deterministic first frozen branch only
- 15 canonical states
- all 14 transitions
- 4 frozen seeds
- 56 transition validations

### J21
- complete 20 ka -> 0 ka canonical layer sequence
- 9 states / 8 transitions
- all 147 native layers
- 4 frozen seeds
- 32 transition validations

Total required: **648 transition validations**.

Every transition preserves the R4.41 rules:

- no `Model.walk()`
- no movement
- no births/deaths
- no autonomous ageing
- no coordinate interpolation
- no population_proxy -> carrier-count conversion
- exact ordinal clock
- exact next canonical state
- frozen RNG state
- required reset baseline invariants

## Production queue authorization

If all 648 bounded transition validations pass, R4.42 authorizes only:

`ARCANA_EXACT_CANONICAL_ANCHOR_REPLAY_QUEUE`

It does **not** authorize the default Geonomics execution queue.

Authorization means the execution mechanics are production-eligible. It does
not yet authorize scientific execution.

R4.42 intentionally remains:

- scientific readout authority closed: false
- scientific execution authorized: false
- Geonomics execution ready: false
- scientific execution performed: false

The reason is that the exact Geonomics metrics/readouts and ARCANA
adjudication schema have not yet been frozen.

Run:

```powershell
.\run_v0_6D1_R4_42.ps1
```

Next if SEALED:

`BUILD_R443_GEONOMICS_SCIENTIFIC_READOUT_AUTHORITY_METRIC_EXTRACTION_AND_ADJUDICATION_SCHEMA_PREFLIGHT`


## R4.42-R1 multi-step clock validation repair

The first live R4.42 run produced exactly four passing transitions per job:
one first transition for each of the four frozen seeds.

This pattern is caused by reusing the R4.41 helper
`_advance_authorized_clock_once()`, whose PASS contract is intentionally
single-step and hard-coded to require `-1 -> 0`.

R4.42 is multi-transition. After the first transition the legitimate clocks
are `0 -> 1`, `1 -> 2`, etc. The clocks themselves were not shown to be wrong;
the validator was.

R4.42-R1 introduces a local multi-step helper that requires, at transition
index `ti`:

- before: `model/community/species t == ti-1`
- after:  `model/community/species t == ti`

It calls exactly the same three R4.40-authorized primitives:

- `Model._set_t()`
- `Model._set_comm_t()`
- `Model._set_spp_t()`

No R4.41 source or evidence is modified.
No autonomous dynamics are introduced.
