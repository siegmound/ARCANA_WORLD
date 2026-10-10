# Indice minimo delle evidenze (identità e scope)
Questa pagina NON è un manifest sostitutivo. Le identità precise dei payload sono nei manifest originali. Verificare disponibilità, hash e scope prima di dichiarare PASS.

| Evidenza | Identità / percorso | Conclusione consentita |
|---|---|---|
| ShellSet Fair upstream parallel capacity | `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` | 9/9 modelli ListEx1 in parallelo, capacity patch, LAPACK smokes; NON ARCANA mechanics |
| Fair OrbData/ARCANA loading | `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json` | qualified runtime integration, NON full physical solve |
| R6 B6N5 structural gap | `docs/arcana/B6N5_POST_RIFT_STRUCTURAL_TRANSITION_AUTHORITY.md` | `BLOCKED_B6N5_INSUFFICIENT_STRUCTURAL_TRANSITION_AUTHORITY` |
| R6 B6N6 model | `docs/arcana/B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE.md` e 2 contracts R6 | architecture only |
| BW1 F1 | `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F1/3b8ab7a588d3b658255e41bd5a92e5a31b78604a-memory-cap32-20261008T185921Z` (Fair) | bounded assembly-only |
| F2-A original | Source commit `e1694e18ddf1843c6709dd7e78f5de7bd6a281b4`; manifest SHA `605559ef61a652ae565d7240da33a089b5cda08cb1159052cb77fc2d58f4a1cd` | original `BLOCKED` preserved |
| F2-A recovery | `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2A_RECOVERY/dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z`; manifest SHA `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936` | recovery reconstructed, review required |
| F2A-V compile-only | Fair `BW1_F2AV_COMPILE_ONLY/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T125317Z` | compile only PASS |
| F2A-V full assembly-only | Fair `BW1_F2AV_RUN/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`; source `df670c8...`; MPI rc75 | `BLOCKED_F2AV_QUALIFICATION` (invalid saturation indicator) |
| F2A-V original transferred archive | GitHub evidence branch `evidence/r6-bw1-f2av-20261010` commit `f318a217dfee2f99d51e834948bcf765d5d45c6b`; LFS SHA256 archive `0a67103b04959e4f4c0c211a29800f31262f4950ebe34bee60ffa14166041c64` | same original evidence, no scientific promotion |

**F2A-V recovery parziale (2026-10-10, report Codex locale non ancora committato/verificato indipendentemente):** Windows `outputs/r6_si1_bandwidth_f2av_offline_recovery/df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z/F2AV_RECOVERY_RESULT.json`; derived-manifest SHA256 dichiarato `e2c945442ab49397bc94164c41498b38fc3f091d65db60481c19ca8ec7612ec4`; decisione `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE`. 79 file originali e 8 staged inputs riportati integri; CSV normalizzato e diagnostica intrabundle riconciliata. Nessuna promozione.

**F2-A sealed reference ora presente e verificato nel worktree Windows** (aggiornamento 2026-10-10): percorso Fair `BW1_F2A_RECOVERY/dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z`, richiesti `F2A_RECOVERY_RESULT.json`, `F2A_RECOVERY_ARTIFACT_MANIFEST.json` e manifest SHA256 `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`. Non dichiarare F2A-V recovered prima di comparazione incrociata effettiva.

**External evidence boundary:** Fair file paths and copied Windows paths are locators, **not** proof that current session has mounted/read those files. GitHub LFS pointer alone is not the binary; `git lfs pull`, archive SHA and inner manifest must be checked.

## Nuovo trasporto F2-A sealed (2026-10-10)
- GitHub evidence branch `evidence/r6-bw1-f2av-20261010`, nuovo commit **`72df050f1dc6616426fd25b33fd7de0cc15d83ac`**, che aggiunge `evidence/F2A_RECOVERY_dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z.tar.gz` (Git LFS) e `.sha256`.
- Fair SHA256 del **manifest interno** verificato prima del push secondo il log: `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`. Non inventare il SHA256 del tar: leggerlo dal file `.sha256` al download.
- Windows archive download, SHA verification e unpack: **PASS** (report di esecuzione utente 2026-10-10). Result F2-A verificato presente. Nuova F2A-V recovery con `--f2a-recovery-root`: exit 0; decision `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`.

## F2A-V complete offline recovery — 2026-10-10
- Windows output (non committato): `outputs/r6_si1_bandwidth_f2av_offline_recovery/F2AV_WITH_F2A_REFERENCE_V1/F2AV_RECOVERY_RESULT.json`, companion CSV/report/manifest in quella directory.
- Recovery evidence manifest SHA256 dichiarato da runner: **`3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`**. Verifica indipendente del contenuto e codice rimane fase successiva.
- Decisione esatta: `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`, exit code `0`; cross-reference F2-A accettato dal runner.
- Contrasto rigoroso: **originale** `BLOCKED_F2AV_QUALIFICATION`; **precedente recovery parziale** `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE`; **nuova recovery completa** senza ancora giudizio sulla matrice/solver. Non sostituire/seal originali.

## F2A-V read-only numerical adjudication report (Windows, 2026-10-10)
- Sorgente: report Codex presentato dall'operatore, **non** file sigillato né repository commit. La review ri-verifica recovery manifest `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f` e 3 artefatti; originale F2A-V 79 membri + manifest e normalized CSV fields6/7; F2-A manifest `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`, result SHA reported `5dde558e…5968fe762` (digest parziale nel report, non inventare caratteri mancanti). 
- Misure riconciliate: n 128884; band kl=ku=727 nKRows 2182; valid 186996964, nonzero 1804327, nonfinite 0; paired 93434040, mismatches 10 (1 zero/nonzero e 9 nonzero mismatch), max rel 1; diagonal dominance strict/near 0, nonstrict 128884; 18.41 decades coeff range. Full CSV/report nel worktree Windows da consultare.
- IEEE inherited `underflow=true`, `inexact=true`, `overflow=false`; phase inexact in `BUILD_F`, `BUILD_K`, `MATRIX_SYMMETRY`, `ROW_COLUMN_STATISTICS`, `OUTPUT_AGGREGATES`; 0 observed new overflow/underflow per phase. Non dedurre causa.
- Code/review tests `139 passed, 2 skipped`, py_compile/JSON/diff check PASS; default pytest temp directory failure workaround `--basetemp`. NVHPC corrected writer / automated sealed E2E fixture / SciPy BW0/BW1 tests outstanding.
- Decisione **`GO_FOR_F2B_PREFLIGHT_DESIGN_ONLY` come classificazione operativa**; non è un seal scientifico e `BLOCKED_F2AV_QUALIFICATION` resta invariato. No Solver, factorization, mechanics.
