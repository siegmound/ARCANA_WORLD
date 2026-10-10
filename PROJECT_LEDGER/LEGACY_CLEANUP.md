# Audit documenti legacy e proposta di pulizia
**Stato:** prima ricognizione, non autorizza cancellazione indiscriminata. La precedente wave C0 ha già rimosso in sicurezza molte centinaia di entrypoint inutilizzati; vedere `docs/arcana/C0_E_CLEANUP_LEDGER.md`, `docs/arcana/CLEANUP_POLICY.md`, `docs/arcana/LEGACY_ARCHIVE_MAP.md`.

## Superfici che confondono la continuazione
| Path | Osservazione al commit df670c8 | Disposizione |
|---|---|---|
| `docs/arcana/ARCANA_CURRENT_STATE.md` | titola PRE-B0 e dice che B0 è prossimo, mentre B0/B6 sono già documentati e F2A-V è l'attività attuale | **SUPERSEDED_OPERATIONAL**; sostituire con pointer a `PROJECT_LEDGER/STATUS.md`, ma recuperabilità Git storica |
| `docs/arcana/ARCANA_BOOTSTRAP.md` | legge il vecchio current-state e parla PRE-B0 | **SUPERSEDED_ENTRYPOINT**; aggiornare il pointer, conservare procedure tecniche ancora valide come storico |
| `README.md`, `ARCANA_WORLD_CURRENT_STATE.md` | rinviano allo stato PRE-B0 | puntare alla nuova cartella |
| `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` | evidenza parallela upstream di successo | **KEEP_AUTHORITY/EVIDENCE**, mai cancellare perché apparentemente legacy |
| `R3/R4/R5` authority/results, manifests, `outputs/`, `local_runs/`, `SIMULATION_RESULTS/` | consumer e valore scientifico variabili | `REVIEW_UNKNOWN`, conservare senza audit file-by-file |
| `ARCANA_EXECUTION_REFERENCE_INDEX.*` | navigation aggregata, potenzialmente stale | `KEEP_REFERENCE`; non usarla come stato o seal |

## Policy per la prossima cleanup wave
1. Inventario dei candidati con percorsi esatti; no delete per semplice prefisso/età.
2. Verificare usi in `src/`, `scripts/`, `tests/`, contracts, manifests, provider bindings, hard anchors, license e ricostruibilità.
3. Per ogni candidato: `KEEP_RUNTIME`, `KEEP_AUTHORITY`, `KEEP_REUSABLE`, `KEEP_REFERENCE`, `DELETE_OBSOLETE`, `DELETE_SUPERSEDED`, `DELETE_TEMPORARY`, `REVIEW_UNKNOWN`.
4. Eseguire test/links e controllare diff e hash; conservare nel ledger path e reason, commit prima/dopo, mezzi per `git show` o recovery; nessuna modifica alle evidenze immutabili.
5. Solo allora eliminare file `DELETE_*`; gli `UNKNOWN` restano. Non imporre un dump di migliaia di file come contesto di nuova chat.

**In questa prima modifica del ledger:** nessun file legacy scientifico viene cancellato. I documenti di navigazione obsoleti possono essere reindirizzati con pointer senza alterare contratti o file di evidenza.
