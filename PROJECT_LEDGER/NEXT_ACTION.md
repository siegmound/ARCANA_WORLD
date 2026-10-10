# NEXT: F2B-D1A — exhaustive offline DOF-map attestation (read-only)

**Current gate:** F2B-D1 design is `DESIGN_COMPLETE_PENDING_ATTESTATION`; the plan is `docs/arcana/SI1_BW1_F2B_D1_DOF_PROVENANCE_CONTRACT.md`. This is not an attestation result. Keep `DOF_MAPPING_UNVERIFIED` and the historical `BLOCKED_F2AV_QUALIFICATION` decision unchanged.

## D1A scope
Perform separately authorized offline, read-only verification of the exact permutation JSON, original and reordered FEG, original and reordered runtime package, BW1 manifest/report, and original F2A-V staged-input manifest/files. Verify hashes against their respective authorities before parsing; prove both permutation inverse equations exhaustively; verify node records, triangle connectivity/order/orientation, coordinates, runtime rows/fields, and staged F2A-V linkage; only then produce a separately sealed raw-DOF-to-node/component companion mapping for the census. Fail closed on missing or mismatched evidence. Do not infer geographic axes, plate identities, or physical meaning from component slots.

Keep the geographic local-basis question distinct: D1A may attest node/permutation and source component ordering, but must leave `component_geographic_basis_mapping=DOF_MAPPING_UNVERIFIED` unless independently proven from exact source and coordinate authority. No census geographic/plate attribution while that remains unresolved.

## D1A restrictions and output
- Offline and read-only; no Fair, MPI, Solver, factorization, gauge, assembly, simulation, or canonical/WORLD_HISTORY mutation.
- Do not edit source-locked ShellSet, FEG, runtime, manifests, or historical evidence. Any attestation candidate is new output outside sealed evidence, with its own manifest and links to original source evidence.
- Keep original F2A-V result blocked. A mapping pass is not solver authorization or scientific qualification.
- If source or contents cannot be read/verified, report `BLOCKED_MISSING_SOURCE` (or precise repository equivalent), preserve UNKNOWN, and enumerate missing paths/checks.

After D1A, update the ledger with its actual scope and outcome. D2 operator semantics and D3 resource/residual design remain separate; no Solver execution is authorized.

---

## Historical D1 design checkpoint (preserved)
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
