# NEXT: F2B-D1 — DOF/permutation provenance closure design (read-only)
**Checkpoint:** ricognizione Codex F2-B del 2026-10-10, locale Windows `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`; branch GitHub successivo include aggiornamenti della bitacora. `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` ne formalizza risultati e vincoli. **Progettazione solamente; non eseguire F2-B.**

## Preparazione
1. Su Windows controllare `git status`, branch, HEAD; preservare i **8 file untracked** in `outputs/r6_si1_bandwidth_f2av_offline_recovery/`. Fare `git fetch origin` e solo `git merge --ff-only origin/r6/si1-bandwidth-f2av` dopo verifica di assenza conflitti. Nessun reset / checkout distruttivo.
2. Leggere `AGENTS.md`, `PROJECT_LEDGER/STATUS.md`, `PROJECT_LEDGER/F2B_PREFLIGHT_DESIGN.md`, `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md`, contratti SI1 e BW1; leggere dati reali disponibili per `new_to_old`, `old_to_new`, FEG derivato, runtime derivato, manifest staged F2A-V.
3. Sono stati riportati solo i **prefissi** degli SHA degli artefatti permutazione, FEG e runtime: `a0895fd9…`, `18d78ec0…`, `a68c0730…`. NON inferire SHA completi né certificare link di provenienza dalla somiglianza dei nomi.

## Workpack F2B-D1
- Inventariare file esatti, SHA256 completi, autorità/contratti/manifest, paths stage e hash di ogni dipendenza del mapping; distinguere original FEG, BW1 permuted FEG e run F2A-V staged, senza back-map non dimostrato.
- Tracciare trasformazione `raw matrix DOF index -> node/permuted component -> original node`; definire equazioni con base 1 e test bijection/roundtrip su `1..64442`, connettività, node coords, runtime fields e identity staged vs sealed F2A-V.
- Identificare come la base locale ShellSet `x/y` dipenda da coordinate, orientazioni e source; se non provato conservare `DOF_MAPPING_UNVERIFIED` per geografia. Non mappare le 10 anomalie a coordinate/placche senza prova completa.
- Proporre **validator offline read-only** con input immutabili, manifest hash, test sintetici piccoli e output nuovo deterministico `DOF_MAPPING_ATTESTATION_CANDIDATE` oppure `BLOCKED_MISSING_SOURCE`. Non implementare/eseguire il validator durante questo gate progettuale senza successiva autorizzazione.
- In parallelo solo source trace di classe operatore/general-band e memory allocation graph `DGBSV`; F2B-D2/D3 restano distinti, non ripetere analisi numeriche già concluse.
- Produrre `docs/arcana/SI1_BW1_F2B_D1_DOF_PROVENANCE_CONTRACT.md` proposto, con matrice `requirement -> artifact -> verified/UNKNOWN -> test -> failure`. Se possibile proporre JSON schema v0 *draft* non executable.

## Acceptance e governance
- Design D1 completo se sono specificati mapping, artefatti, test, criticità con provenance e semantica della base, senza dichiarare verificati i controlli non eseguiti.
- Decisione ammessa `F2B_D1_DESIGN_COMPLETE_PENDING_ATTESTATION` oppure `F2B_D1_DESIGN_BLOCKED_MISSING_AUTHORITY` (workflow labels, non scientific seals).
- Aggiornare `PROJECT_LEDGER/STATUS.md`, `NEXT_ACTION.md`, `LOG.md`, `EVIDENCE_INDEX.md` insieme al milestone e non sovrascrivere il verdict storico.

**Non autorizzato:** Fair, MPI, Solver, factorization, new assembly, gauge, mechanical outputs, modifica ShellSet source-locked, production/canonical WORLD_HISTORY, replicare benchmark upstream.
