# INT3-ENG10K-E — FAIR synthetic supervisor evidence closure

Date: 2026-10-24
Repository: `siegmound/ARCANA_WORLD`
Branch: `r6/si1-bandwidth-f2av`
FAIR-qualified commit: `cb9bd8373eeb028b83c8bc1abb376624e3553adb`

## Decision

`INT3_E_FAIR_SUPERVISOR_SYNTHETIC_RUNTIME_PASS`

The operator reports that the focused Linux suite on the exact commit above
collected 43 tests and passed all 43 (0 failed, 0 skipped), exiting 0 in 2.83 s.
The execution was synthetic supervisor testing only; the INT3 provider preflight
also passed as `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`. No ENG10K
numerical evolution was run.

## Evidence and authority

| Item | Reported value | Authority / local verification |
|---|---|---|
| Tested source | `cb9bd8373eeb028b83c8bc1abb376624e3553adb` | Operator-reported exact test commit; local branch HEAD matches at consolidation. |
| Runtime | Python 3.12.10, NumPy 2.3.5, pytest 9.1.1 | Operator-reported FAIR environment. |
| Preflight | `INT3_ENG10K_PREFLIGHT_PASS_NO_NUMERICAL_EVOLUTION`, exit 0 | Reported by FAIR procedure. |
| Linux tests | 43 collected, 43 passed, 0 failed, 0 skipped; 2.83 s; exit 0 | Operator-reported; original files were not transferred to Windows. |
| Evidence directory | `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/INT3_ENG10K_E_FINAL_ASSERTION_RETESTS/cb9bd837_20261015_01` | FAIR path reported by operator. |
| `pytest.log` | SHA256 `a6513d0baf2d382f4338d38e250e6c3c1e186881f966f6395e92f2191f29ade1` | Operator-reported; not rehashed locally. |
| Checksums | OK for `source_commit.txt`, `runtime.txt`, `preflight.log`, `preflight.exitcode`, `pytest.log`, `pytest.exitcode` | Procedure-reported checksum checks; artifacts not imported or independently checked on Windows. |

The report therefore records FAIR operator evidence, not a Windows re-verification
of the original logs or checksum sidecars.

## Synthetic supervisor coverage

All three Linux end-to-end process tests passed on the reported run:

- natural exit of the synthetic child;
- timeout and termination of a synthetic process group;
- leader exit while a live descendant remains, including completion before
  natural-exit classification.

This qualifies those tested supervisor paths in the reported Linux runtime. It
does not establish hard operating-system resource quotas. Any RSS/output limits
exercised by the supervisor are sampled monitoring behavior; OS-enforced memory
or time isolation is not claimed.

## Historical failures retained

Earlier outcomes remain separate and unchanged: INT3-C had 30 passed / 1 failed;
INT3-D had 40 passed / 1 failed; the first INT3-E attempt failed during
collection (exit 2); an earlier INT3-E run had 41 passed / 1 failed (reported log
SHA256 `f33b3c9d49b230c782018941b198e0bda4e951623c7f13aa316a6356f3194b1f`); the
fixture hotfix retest had 42 collected, 41 passed / 1 failed on a child-source
`NameError`; and the next retest had 43 collected, 42 passed / 1 failed on the
stale stdout assertion (reported log SHA256
`fbf2f8e05e086a380975e81eb1ef9c948ba3954daa6c239b0cd84e3e57d2e861`). Original
failures and collection errors retain their identities and evidence. The
subsequent 43/43 PASS does not rewrite or retroactively promote any of them.

## Scope limits and next decision

This result does not qualify the ENG10K scientific kernel, geophysical model,
F2B/Solver, physical validity, or canonical `WORLD_HISTORY`. It does not authorize
an ENG10K run. All existing gates remain unchanged:

`BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`;
`RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`;
`ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`;
`INT3_ENG10K_EXECUTION_AUTHORIZED=false`.

The next decision is a separate review of whether the engineering preconditions
justify proposing one bounded, noncanonical ENG10K authorization. This synthetic
PASS is not that authorization. The R4 checkpoint, manifest, and all historical
outputs remain unchanged.
