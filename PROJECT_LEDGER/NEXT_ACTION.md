# Prossimo incarico — acquisire il companion F2-A sealed, poi chiudere F2A-V offline
**Stato:** `BLOCKED_F2AV_RECOVERY_MISSING_F2A_REFERENCE` (resoconto Codex locale del 2026-10-10; non un seal/commit). Il nuovo writer e il runner recovery sono modifiche **non committate** nel worktree Windows.

## Cosa abbiamo già
- F2A-V originale conserva `BLOCKED_F2AV_QUALIFICATION`, MPI exit 75 e stop pre-Solver.
- Il recovery parziale riporta: nRank 128884, valid 186996964, nonzero 1804327, nonfinite 0, symmetry pairs 93434040, 10 divergenze (1 `ZERO_NONZERO`, 9 `NONZERO_VALUE_MISMATCH`), histograms/extrema/IEEE reconciled.
- Originale verificato prima/dopo: 79 file, 8 staged inputs, SHA invariati **come dichiarato nel report locale Codex**; la riconciliazione incrociata F2-A non è ancora possibile.
- Test del worktree Windows: `139 passed, 2 skipped` (report). BW0/BW1 extra bloccati da SciPy mancante in quell'interprete; `py_compile`, JSON/manifest hash, diff check dichiarati PASS. Nessun Fair/MPI/Solver eseguito in recovery.

## Prossima azione
1. Su Fair: verificare che il bundle di recovery originale esista **senza modificarlo**:
   `$HOME/ARCANA_WORLD_QUALIFICATION_EVIDENCE/BW1_F2A_RECOVERY/dbd8ccf15b72e1819d0fba68eb8e3fc4526060c3-20261008T222906Z`.
   Controllare file `F2A_RECOVERY_RESULT.json` e `F2A_RECOVERY_ARTIFACT_MANIFEST.json`, e SHA256 esatto del manifest `451687659a6de511aa423cdac400685c718ff2dfb24f10d97b76fd24f61b6936`.
2. Archiviare *tutto* il bundle sealed con tar, SHA256 esterno, senza scrivere al suo interno. Aggiungere l'archivio a Git LFS su un evidence worktree (o branch di evidenza dedicato), commit+push append-only; niente force.
3. Windows: fetch ref esplicito, LFS pull, verificare SHA256 dell'archivio e del manifest interno, estrarre in directory nuova esterna al repository.
4. In worktree di sviluppo che contiene il nuovo runner non committato, rieseguire **offline**:
   `python scripts/r6_si1_bandwidth_f2av_recover_evidence.py --source-evidence-root "<F2A-V_SOURCE_BUNDLE>" --f2a-recovery-root "<F2A_RECOVERY_BUNDLE>" --output-dir "<NEW_EMPTY_OUTPUT_DIR>"`.
5. Riesaminare risultato nuovo: fail-closed su qualunque inconsistenza; in caso di PASS solo `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION`. Non riscrivere alcun verdict storico. Confrontare SCIENTIFIC metrics, verificare DOF mapping; documentare controprove.
6. Prima di commit del codice: review del diff e test F0/F1/F2-A/F2A-V/recovery; eseguire BW0/BW1 con env SciPy valido (es. ambiente Linux esistente) senza nuovi run MPI. Commit+push solo dopo review; aggiornare ledger insieme al gate chiuso.

**Proibito:** nuovi run Fair MPI/Solver/fattorizzazione, mutazioni di manifest source/legacy, gauge, world evolution/canonical promotion per risolvere un errore di postprocessing. Recovery output precedente resta evidenza derivata parziale, non seal.

## Sequenza macchina / branch — evitare pull non necessari
L'unica operazione su **Fair** ora necessaria è push dell'archivio sealed F2-A dal worktree evidence; **non** aggiornare tramite pull il branch scientifico Fair. Su **Windows**, prima recuperare l'archivio con fetch/LFS pull del worktree evidence e rilanciare il recovery nel worktree che conserva il codice Codex non committato. Il branch `docs/r6-project-ledger-20261010` è ancora remoto: recuperarlo con `git fetch` **senza merge** finché le modifiche Windows non sono state salvaguardate, revisionate e committate.
