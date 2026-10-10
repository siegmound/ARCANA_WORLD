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

**No offline recovery result recorded as of 2026-10-10.** The transferred evidence has been extracted and first CSV records inspected. F2-A recovery companion must be available for fully reconciled recovery; absence blocks full closure.

**External evidence boundary:** Fair file paths and copied Windows paths are locators, **not** proof that current session has mounted/read those files. GitHub LFS pointer alone is not the binary; `git lfs pull`, archive SHA and inner manifest must be checked.
