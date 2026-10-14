# INT-2C-B — Technical checkpoint attestation and runtime preflight

Date: 2026-10-14. Entry branch `r6/si1-bandwidth-f2av`, HEAD
`f49de047ff560f707428b395b7373d46301fdee9`, parent
`6a719da728baa11c4a972195d357fde7c32d21b3`; tracked worktree initially clean.

**Decision: `INT2CB_BLOCKED_FAIR_RUNTIME_IDENTITY_MISMATCH`.** Technical
engineering input closure was attested locally; the complete B0 runtime/store
preflight and real numerical replay remain pending. This is not
`INT2C_B0_REPLAY_PREFLIGHT_PASS__REAL_NUMERICAL_EXECUTION_PENDING`.

## Authenticated inputs and technical issuance

The existing `prepare_r4()` loader reverified the exact nine-file R4 membership,
externally pinned manifest SHA256
`191ee97af186705fe75bacc627013158c69b97041a43f4633e95dd2abbd8e236`, member sizes
and hashes, provider/source provenance, original typed records, both complete
73-node starting states, forcing, configuration and original final-state oracle.
All nine original files also retained identical byte hashes before/after issuance.
No new provider-backed evolution was performed.

- Original execution commit: `91fc83d50ec15d8bb9b826926ac2f2dc859281e8`.
- Historical/current normalized kernel SHA256:
  `bddedfd7439b328951389012b2af371d106d042018ac4be928325a6395666542`.
- Historical source composite:
  `b3aff732b22d8a4ecc8426c5b54bfaca5490cb59a37679cff4d1dd78f713f8ca`.
- Pair 5:11, boundary `R6BND-T0-3eb57747e6f0a3f3305f`, supports
  `R6G1D-R091-C029` / `R6G1D-R091-C028`; 73 nodes per support.
- Frozen forcing: 0.11467052868814648 m/year; duration 31,557,600,000 seconds
  (1,000 engineering years); reference fraction 0.0005.
- Original initial checkpoint:
  `r6checkpoint_7aa9a77c40f44803580e9ff342c92d25b94f960ca727f2356c529e93af01a70e`.
- Original recipe:
  `r6recipe_ab1ae762b061a097275426ee91efd11cafab37b7e9a9bb6f8e307c3da058abc0`.

New `scripts/r6_int2c_checkpoint_attest.py` accepts repository/bundle paths,
not caller-supplied records or hash labels. It invokes the authenticated existing
preparation and unchanged exact `_verify_runtime()`, validates each record with
HistoryStore's existing typed transaction parser, checks unique identities and
the initial-state/forcing/provenance dependency closure, then issues new records.
It does not alter B0, the adapter, historical checkpoint status, forcing, kernel,
equations, numerical settings or expected output. A runtime mismatch rejects
issuance. The nine-record inventory includes the historical records; historical
candidate recipes are preserved as history, not made executable.

The new checkpoint has status `VALIDATED` **only** within
`TECHNICAL_ENGINEERING_INPUT_CLOSURE_ONLY`. Its identity binds the issuer source
digest, inventory digest, checked runtime versions and explicit limitations.
Its parent is the INT-2C-A derived candidate. The matching recipe changes only
its base checkpoint identity. There are eleven records for eventual registration:
the nine prepared records plus the new technical checkpoint and recipe.
This is an input-closure status, not validation of predicted numerical results,
historical interpreter binaries, physical authority or canonical publication.

Final derived records (local runtime Python 3.12.10 / NumPy 2.3.5):

| Item | Identity / SHA256 |
| --- | --- |
| New checkpoint | `r6checkpoint_45ccc437cbe2d5d8d40febbbbc3d7d6d5b5a1a42e7060ca40027048524b71158` |
| New recipe | `r6recipe_46e4b555cd4f996cd58020b840819c6ff468cb4640254fb3bb4efb6e887a4c92` |
| Closed configuration | `856a1e7b3662e64bd60e8d364b708163e356aac5fdc995cdb683ecd6fc6ef075` |
| Checkpoint file | `9fb815fe94542eb041fcbd6a0f9f6092880de0d9a6013d0a3715b8778a105650` |
| Recipe file | `e4803ac6f98a0f13ae7b6c015428fee1f4c955f8efb620c480fd4348e4d4f1fb` |
| Attestation file | `a1f3253899ce36e94e9bb3eecfa5df0b3139be153b6b80fde237313375fb3c9e` |
| Three-member manifest | `8b172002968c9fcd7620d78b456054ac7ca0e7a9afa49f2f9e91ca81e9b1731d` |

Final local output:
`outputs/r6_functional_development/INT2CB_TECHNICAL_ATTESTATION_20261014_02/`.
The `_01` preparation output is preserved as provisional and is not the final
issuer-bound attestation. Neither directory is staged in the code commit.

## Existing Fair runtime: direct read-only observation

The pre-existing SSH configuration for `10.20.80.104`, user `jlpfritas`, was
used with BatchMode, strict existing host-key checking and a connection timeout.
No credentials, new authentication mechanism, job, build or environment change
was requested. Hostname returned `fair`; the ledger's known worktree existed.
One initial metadata script returned a shell syntax error after those checks;
the corrected LF byte stream exited 0. Only known Miniforge base/env prefixes
and `$HOME/.conda/envs/*` were enumerated, without a broad filesystem search.
Each existing Python was queried for `sys.executable`, version and NumPy version
with `PYTHONDONTWRITEBYTECODE=1` and `PYTHONNOUSERSITE=1`.

| Runtime path | Python | NumPy | Compatibility |
| --- | --- | --- | --- |
| `/home/jlpfritas/miniforge3/bin/python` | 3.14.7 | unavailable | incompatible |
| `/home/jlpfritas/miniforge3/envs/arcana-r6-linux/bin/python` | 3.12.14 | 2.5.3 | incompatible |
| Required R4 binding | 3.12.10 | 2.3.5 | not found in inspected prefixes |

These are direct session observations, not hashes of historical runtime binaries
or proof that no suitable environment exists anywhere on Fair. No exact runtime
was established on the supported Fair filesystem. Local Windows tests used the
existing Python 3.12.10 plus installed workspace NumPy 2.3.5 through PYTHONPATH;
no package was installed. Version equality alone does not establish bitwise
cross-platform or historical binary equivalence.

## B0 integration and execution boundary

`validate_replay_inputs()` accepted the genuinely authenticated R4 initial,
forcing, provenance and new technical records through the existing test reader
fixture. The expected final state remains a separate oracle. The kernel was
guarded against execution in the new issuance/closure test. Existing adapter
regressions demonstrate runner input binding with mock kernels only.

No real HistoryStore was instantiated or published in restricted Windows.
No reopened-store/atomic-publication PASS is claimed. On a supported filesystem
and separately qualified runtime, the remaining preflight must register the
eleven records transactionally, reopen the store, compare every record's identity
and content, and invoke current `validate_replay_inputs()` before any execution.
The later real call must use current `execute_replay()` with
`DeterministicKernelAdapter(attestation.prepared)` and independently recompute
both states; no mock kernel or expected-state return is acceptable.

Acceptance remains the full expected state identity
`r6state_d36b8094e89671d0d25894bcd4d798efdb426c65fcd6eb5d6652531f92c51d6a`
and each original per-support pretty-JSON/LF payload digest
`2b4836954e688d7aac6d9e26ccb61aa02fa94e9e40550c395922b30fa1b45d7b`.
Compact B0 identity hashes and historical pretty-JSON hashes are distinct.
Discrepancies must be preserved; no normalization or relaxed threshold is allowed.

No executable numerical command is certified by this task: runtime and real
store preflight prerequisites are incomplete, and no numerical execution is
authorized. A fresh candidate store/evidence root and active time/memory/output
supervision must be checked absent and approved before an eventual bounded run.

## Smallest explicit runtime decision

Two alternatives require a separate decision: authorize provision of the exact
historical version pair, or review a separately identified candidate binding for
the existing Fair Python 3.12.14 / NumPy 2.5.3 runtime. The latter must record
interpreter/library identities and its own configuration/checkpoint/recipe IDs,
retain the original runtime-bound records, pass offline contract tests, and
evaluate both numerical outputs against the unchanged R4 oracle in a separately
authorized replay. It cannot be implemented by relaxing `_verify_runtime()` or
assuming equivalence. No alternate binding has been issued here.

## Verification and remaining authority

Focused INT-2C-B/A, INT-1A, INT-2A and INT-2B suites: 63 passed, 0 failed,
0 skipped, 1 deselected (actual Windows store-publication test). New tests cover
deterministic technical issuance, typed B0 closure, preservation of candidate
records, Python/NumPy mismatch, malformed dependency identity, absent bundle and
canonical path rejection. Existing tests cover incomplete provenance, altered
forcing/material/configuration/source and separation of prediction from oracle.
Early development runs exposed two incorrect field-name references in the new
attestor; both were corrected before the passing suite. One test invocation had
an incorrect test filename and collected no tests; the corrected suite above
was executed. These were implementation/test-command errors, not replay runs.

Final py_compile, UTF-8/LF, whitespace, manifest membership/hash checks, unchanged
historical adapter/kernel/report checks and staged diff checks are required for
consolidation. No historical artifacts were rewritten. No canonical store was
read or mutated. Historical interpreter binary identity, Fair numerical
equivalence, actual B0 registration/readback and execution resource authority
remain unverified.

Preserved: `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`,
`THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`,
`F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`,
`WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
