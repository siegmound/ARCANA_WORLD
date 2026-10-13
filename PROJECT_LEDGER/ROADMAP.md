# ARCANA R6 — Roadmap operativa corrente (2026-10-13)

**Obiettivo completo:** storia mondiale causale 210 Ma→0 ka, interrogabile e ricostruibile per geografia/tettonica, geologia, clima, idrologia, risorse, Deep, flora/fauna, popolazioni e società. **Priorità ora:** integrare motori esistenti su una finestra candidata, misurare i risultati e *poi* decidere la retention. Le dipendenze non sono una percentuale o una scadenza.

| Gate | Risultato atteso | Stato |
|---|---|---|
| **INT-0A** | Runner minimo che collega realmente 2+ componenti, con tempo/supporto/provenance coerenti | `INT0A_INTEGRATION_CODE_READY__NONCANONICAL_RUN_NOT_YET_EVIDENCED`; suite offline mirata 20 PASS |
| **INT-0B** | Noncanonical T-F2B 5:11 engineering run, samples, comparison, restart, manifest | R4 completed on 91fc83d; bundle/samples/replay/restart verified. INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED. _01-_03 remain immutable failures. |
| **INT-0B-R2** | Isolamento ambiente corretto e tentativo finale bounded | Preflight provider PASS su `311550d`; esecuzione singola fallita su endpoint diagnostico dopo 22.190863 s (exit 1). La diagnosi R3 identifica mismatch di schema `elapsed_years` assente dal final payload, non prova una divergenza numerica; la regressione sintetica e la correzione supervisor passano. Nessun quarto run autorizzato. |
| **INT-0B-R3** | Correzione endpoint e metadata supervisor offline | `INT0B_R3_ENDPOINT_VALIDATION_CORRECTED__REEXECUTION_NOT_AUTHORIZED`; report del run fallito immutato e campioni non recuperati. |
| **INT-0B-R4** | Validazione E2E sintetica, provider preflight e un tentativo engineering bounded | Offline suite 70 PASS; quarto run autorizzato su `91fc83d` completato e bundle verificato. Decisione noncanonical: `INT0B_NONCANONICAL_INTEGRATED_RUN_EVIDENCED__SCIENTIFIC_PROMOTION_NOT_AUTHORIZED`. |
| **INT-1** | Empirical full/fixed/event/error/uncertainty retention, reconstruction, replay and byte measurements | Ready for bounded offline analysis of the verified noncanonical R4 trajectory; no canonical retention decision or scientific promotion. |
| **INT-2** | Query/refinement/reconstruction di una traiettoria multi-provider | Dopo INT-1 |
| **INT-3** | Provider aggiuntivi, estensione geografica e temporale | Solo con input/applicabilità/contratti adeguati |
| **Produzione WORLD_HISTORY** | Stati/eventi causalmente verificati per tutti i domini fino a 0 ka | Non autorizzata |

## Inventario con scope (non trasformare PASS tecnici in qualifica scientifica)

INT-0B provider input audit era passato sul commit `311550d` con source identity HEAD-bound `a19070287adedb0bb009ce5c56380892ca173d4eee30b662c6c1a7d34406b34a`; tale audit non si trasferisce automaticamente a HEAD R4. R4 è solo offline/sintetico e non autorizza una quarta evoluzione. Un audit read-only dei provider sul commit finale di una futura esecuzione resta precondizione, insieme a una distinta approvazione. INT-1 resta bloccato.

- **B0/B6:** HistoryStore/query/replay esistono. B6K candidata geometrica 210→209.97287659484368 Ma e B6N8-A shadow multirisoluzione. Vecchio B6M-R1 bloccato e successivo live-view B6N8-A a due età sono checkpoint distinti; verificare il canonico attuale read-only.
- **Termica/cinematica integrabile:** PRE_ORBDATA, B6N8-O/Q e codice T-F2B con supporto coppia **5:11**, forcing ingegneristico congelato, finestra 1.000 anni e replay/restart. B6N8-R roster real-support ancora incompleto; NON estendere T-F2B alla coppia rift **1:3** per analogia.
- **Post-rift:** B6N5/B6N7 non chiudono la legge di propagazione fisica, eventi di interfaccia/topologia/supporto né `dt2`. Questo blocca la **continuazione fisica post-rift**, non ogni test ingegneristico non canonico.
- **ShellSet/OrbData:** esempio upstream Fair 9/9 nel proprio scope; caso SI1 assembly pre-Solver e recovery, non solve qualificato. W3-C-C ha difetti aperti; W3-C-B-R1, real owner/MPI stop, W4 scala e classi/threshold numerici separati.
- **pyGPlates:** fixture/adapter candidato; reports mapping canonico `PYGPLATES_RUNTIME_UNAVAILABLE` non sono prove runtime positive. Non obbligatorio per INT-0 se Euler/plate support già disponibile.
- **Ambiente/Deep/ecologia/società:** componenti/contratti parziali o legacy, da integrare in futuro senza fabbricare valori UNKNOWN.

## Workstream paralleli (non NEXT generale)

1. **ShellSet SI1:** W3-C-B-R1 → revisione → owner/runtime stop → W4/risorse → criteri fisico-numerici → gate Solver distinto.
2. **Tettonica post-rift:** modello evolvibile e predicati di validità, topologia/interfacce/supporto; non derivare fisica da rigide rotazioni.
3. **OrbData, pyGPlates, BIOME4, risorse e Deep:** provider e input/autorità per estendere vertical slice, solo quando reali dipendenze.

**Non usare le vecchie NEXT storiche.** `NEXT_ACTION.md` è l'unica NEXT attiva. Originali, hash, `BLOCKED` e log sono conservati in `STATUS.md`, `EVIDENCE_INDEX.md`, `LOG.md`, report e storia Git. Conservare separati CODE_READY, NONCANONICAL_RUN, SCIENTIFIC_VALIDATION e CANONICAL_AUTHORITY.

**Gates invariati:** `BLOCKED_F2AV_QUALIFICATION`; `OPERATOR_CLASS_UNVERIFIED`; `THRESHOLD_UNJUSTIFIED`; `RESOURCE_2GB_SCOPE_UNRESOLVED`; `F2B_SOLVER_EXECUTION_AUTHORIZED=false`; `ARCANA_SI1_MECHANICS_QUALIFIED=false`; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
