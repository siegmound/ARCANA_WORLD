# ARCANA WorldSim v0.6D1-R4.40
## Geonomics Domain-Specific Carrier Dynamics Authority & Execution Queue Preflight

Parent authority:
- R4.39 integrated: 44/44 PASS
- R4.39 final seal: 32/32 SEALED
- R4.39-R5 reseal verification: 16/16 PASS

R4.40 closes the carrier-dynamics authority gap without authorizing Geonomics
to invent biological dynamics for ARCANA's nonliteral carriers.

## J14 and J18

A carrier is one representation of an active canonical deme support, not one
census individual.

The only authorized carrier evolution is:

1. bind the next ordinal Geonomics timestep to the next canonical age;
2. replace the nonliteral carrier state exactly with the canonical anchor state;
3. rebuild Geonomics-derived spatial caches;
4. permit only static connectivity/readout operations.

Between anchors:

- autonomous movement: forbidden
- autonomous births/deaths: forbidden
- autonomous ageing as physical time: forbidden
- coordinate interpolation: forbidden
- population_proxy -> Individual count: forbidden

R4.40 validates the complete canonical replay source surfaces:

- J14: 192 branches × 140 transitions = 26,880 exact carrier-state targets
- J18: 64 branches × 14 transitions = 896 exact carrier-state targets

Coordinates remain exactly:

- `x = grid_col`
- `y = grid_row`

## J21

J21 is layer-only:

- 147 native dynamic layers
- 4 canonical sidecars outside Geonomics Layer.rast
- 8 ordinal transitions
- 1,176 exact future layer targets

No autonomous carrier dynamics are applicable or authorized.

## Why the default Geonomics queue remains forbidden

R4.40 source-audits the live Geonomics 1.4.9 `Model._make_fn_queue`.
The default queue can include movement and population dynamics. Those operations
have no ARCANA authority for nonliteral carriers.

Therefore R4.40 compiles an ARCANA domain-specific queue contract instead of
authorizing `Model.walk()`.

## Important nonclaim

R4.40 closes **authority**, not execution.

It still sets:

- `single_transition_dry_run_validated = false`
- `production_execution_queue_authorized = false`
- `geonomics_execution_ready = false`
- model runs = 0
- scientific execution = false

The next stage must execute one disposable transition and prove state invariants
before any production queue can be authorized.

Run:

```powershell
.\run_v0_6D1_R4_40.ps1
```

Next if SEALED:

`BUILD_R441_GEONOMICS_DOMAIN_SPECIFIC_EXECUTION_QUEUE_SINGLE_TRANSITION_DRY_RUN_AND_STATE_INVARIANT_VALIDATION`
