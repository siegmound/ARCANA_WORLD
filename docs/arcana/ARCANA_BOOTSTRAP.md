> **SUPERSEDED FOR CURRENT DEVELOPMENT CONTINUATION (2026-10-10).** This document describes the historical PRE-B0 status, not the current R6 development stage. The single operational starting point is [PROJECT_LEDGER/README.md](../../PROJECT_LEDGER/README.md), then [STATUS.md](../../PROJECT_LEDGER/STATUS.md) and [NEXT_ACTION.md](../../PROJECT_LEDGER/NEXT_ACTION.md). Scientific contracts and historical evidence remain valid only within their original stated scope.

# ARCANA WorldSim — Session Bootstrap

Read this file, then [current state](ARCANA_CURRENT_STATE.md),
[architecture](WORLD_HISTORY_ARCHITECTURE.md),
[authority map](DATA_AUTHORITY_MAP.md), [provider registry](PROVIDER_REGISTRY.md)
and [cleanup policy](CLEANUP_POLICY.md). Avoid broad historical scans unless a
specific authority or replay dependency requires one.

## Repository entrypoints

- R6 source: `src/arcana_worldsim/r6/`
- Builders/diagnostics: `scripts/r6_*.py`
- Default pytest surface: current `tests/test_r6_*.py` regression modules.
  R1–R5 stage suites remain available for explicit stage-specific runs; source
  snapshots under `outputs/`, `repairs/` and run-evidence trees are evidence,
  not default test roots. See `pytest.ini`.
- R6 focused regression: `tests/test_r6_*.py`
- Current authority, contracts and manifests: root `R6_*` files
- ShellSet integration: `external/ShellSet-v1.1.0/` and
  `src/arcana_worldsim/r6/shellset_mesh/`

## Working rules

- ARCANA owns canonical scientific state and provenance.
- Treat manifests/contracts as authority boundaries; diagnostic outputs do
  not promote themselves to authority.
- Do not infer permission for mechanics or forward evolution from a successful
  package load.
- Preserve deterministic builders and hard-anchor inputs when consolidating.
- Begin with `git status --short`, branch and HEAD. Keep work scoped to the
  requested R6 stage.

## R6 runtime authorization boundary

- `runtime_authorized`: true only for
  `LOAD_AND_CONSUME_GOVERNED_ARCANA_T0_RUNTIME_PACKAGE`.
- `mechanics_authorized=false`
- `forward_evolution_authorized=false`
- `dt_selected=false`
- `t1_created=false`
- `canonical_state_changed=false`

This bounded package authorization does not qualify full ShellSet mechanics or
forward evolution. Preserve historical pre-execution records as written; they
may record the earlier `runtime_authorized=false` status and are not rewritten
by this current operating boundary.

For repository cleanup decisions, read
[C0-E ledger](C0_E_CLEANUP_LEDGER.md) and
[legacy archive map](LEGACY_ARCHIVE_MAP.md).

PRE-B0 C0 cleanup has completed through F4 health closure. C0-F2 removed only
verified high-confidence data copies and pytest scratch; C0-F3 retained the
remaining payload surface conservatively. The execution reference index is a
generated navigation aid, not scientific authority. Duplicated historical
payloads remain intentionally retained until a governed provenance/content
identity layer can preserve distinct records while sharing payload bytes.
