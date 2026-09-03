# R3.19-R1 — Canonical runner q-ceiling authority repair audit

## Failure reproduced

The canonical R3.19 run reached the post-step validation/report path and failed with:

`AttributeError: 'R319Config' object has no attribute 'resource_variance_ceiling'`

The phase-aware transport operator, parent authority validation, and all candidate scientific gates had already passed. The failure was caused by one stale runner-only attribute name.

## Root cause

`R319Config` inherits the governed R3.4/R3.5/R3.8 ceiling as:

`variance_ceiling_normalized = 0.08`

There is no governed config field named `resource_variance_ceiling`.

## Repair

Only the canonical runner validation line is changed:

- old: `q_ceiling=float(cfg.resource_variance_ceiling)`
- new: `q_ceiling=float(cfg.variance_ceiling_normalized)`

No numerical value is changed. The runner now reads the same sealed q ceiling used by the inherited runtime and previous R3 stages.

## Regression hardening

A new regression test requires:

1. `R319Config.variance_ceiling_normalized == 0.08`;
2. `resource_variance_ceiling` is absent;
3. the canonical runner uses the inherited authority name;
4. the stale attribute string is absent from the runner.

The formal candidate audit adds the same runtime-path guard.

## Verification

- R3.19: 11/11 PASS
- R3.18: 10/10 PASS
- R3.17: 9/9 PASS
- R3.16: 11/11 PASS
- R3.15: 12/12 PASS
- R3.14: 13/13 PASS
- Total immediate regression: 66/66 PASS
- R3.19 formal candidate audit: 209/209 PASS

## Governance

- Scientific parameter changes: NONE
- Biology changes: NONE
- Transport operator changes: NONE
- Biology cadence changes: NONE
- Transport cadence changes: NONE
- R3.8 authority modified: NO
- R3.19 phase-aware engine modified: NO
- Deep biological coupling: OFF

This is an operational canonical-runner repair only.
