# ARCANA WorldSim — R6 World History

ARCANA is building a causal, queryable `WORLD_HISTORY`: a compact record of
world state, events, forcing, provenance and replay sufficient to answer
historical queries and support selective high-resolution refinement.

**Current development entrypoint:** [PROJECT_LEDGER/README.md](PROJECT_LEDGER/README.md).
For every new conversation start from [PROJECT_LEDGER/NEW_CHAT.md](PROJECT_LEDGER/NEW_CHAT.md)
and consult the ledger's STATUS, NEXT_ACTION, ROADMAP and PROCEDURE.
Historical [session bootstrap](docs/arcana/ARCANA_BOOTSTRAP.md),
[architecture](docs/arcana/WORLD_HISTORY_ARCHITECTURE.md),
[authority map](docs/arcana/DATA_AUTHORITY_MAP.md) and
[provider registry](docs/arcana/PROVIDER_REGISTRY.md) remain supporting technical references, not current progress ledgers.

## Current boundary

R6 has an authorially ratified T0 realization and a materialized 64,442-node
ShellSet FEG/runtime package. The FAIR qualification reported successful
loading of that ARCANA runtime package. This is a bounded loading result: it
does not authorize ShellSet mechanics, T1 creation or forward evolution.
ARCANA retains scientific authority; external engines are bounded providers,
references or candidates only under explicit contracts.

## Development and validation

R6 source is under `src/arcana_worldsim/r6/`, command-line builders and
diagnostics are under `scripts/r6_*.py`, and focused tests are under
`tests/test_r6_*.py`. See the bootstrap and cleanup policy for the narrow
startup/test workflow. Historical R3/R4/R5 material is mapped in
[the legacy archive map](docs/arcana/LEGACY_ARCHIVE_MAP.md); it is not the
current project entrypoint.
