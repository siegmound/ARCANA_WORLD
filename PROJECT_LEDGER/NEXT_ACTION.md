# NEXT — R6-INT0A: prima integrazione osservabile dell'orchestratore

**Una sola priorità corrente (2026-10-12).** Preparare il runner che usi provider scientifici già presenti su uno stesso supporto ed epoca, dimostrando uno scambio vero output→input, non due output affiancati. Non avviare un nuovo run numerico o un job senza il gate specifico INT-0B. W3-C-B-R1 rimane il prossimo fix **interno a ShellSet**, non la NEXT generale.

## Sorgenti e primo caso

Verificare e riusare `src/arcana_worldsim/r6/functional_development.py`, `functional_spatial_support.py`, `plate_support_adapter.py`, `pre_orbdata_t0_initializer.py`, `b6k_candidate.py`, `b6n8a_shadow.py`, B0 HistoryStore/query/replay e `scripts/r6_functional_development_t_f2b.py` con test. Controllare SHA, branch, contratti, versioni e output esistenti; non duplicare kernel/equazioni.

Vertical slice iniziale proposta: **coppia continentale 5:11** di T-F2B, supporto/lineage verificati, cinematica Euler a T0 210 Ma e colonne termiche. I 1.000 anni a forcing congelato di T-F2B costituiscono **scenario ingegneristico non canonico**, non prova di evoluzione geologica. B6 rift 1:3 non è la stessa coppia: nessuno splice di risultati o leggi senza binding.

## Esecuzione di INT-0A — audit, implementazione e test offline

1. Seguire `PROCEDURE.md`, verificare remoto, HEAD, worktree, source/input SHA e output immutabili. Non toccare untracked, storico o sorgenti bloccati.
2. Identificare il minimo **contratto condiviso**: support IDs/plate IDs, unità, frame, origine temporale, durata, forcing, proprietà termiche, stato, provenance, incertezza e intervalli di validità. Documentare ogni campo owner/produttore/consumatore.
3. Implementare/adattare il minimo runner ARCANA riusando i kernel: un output calcolato da un componente deve essere consumato e verificato come input da un altro. L'esistenza di T-F2B da sola non qualifica un nuovo orchestratore. Se non è possibile senza forzanti inventate: `INT0_BLOCKED_INPUT_BINDING` con gap esatti.
4. Progettare staging **non canonico** in nuova root: campioni e differenze numeriche, forcing, eventi candidati se giustificati, UNKNOWN, source/config/seed/provider IDs, manifest/hash, checkpoint/recipe per replay/restart. Non mutare `WORLD_HISTORY` canonico.
5. Test offline: validazione interfacce/tempi/supporti, controllo unità, fallimenti fail-closed, assenza di interpolazione/fisica inventata, invarianti pertinenti, determinismo quando previsto, no import/write canonico. Non chiamare un dry-run la prova di una simulazione.
6. Prima di un **nuovo run numerico** definire input e SHA, budget di tempo/RAM/output, destinazione, criterio di stop e autorizzazione delimitata INT-0B. INT-0A non autorizza per implicazione evoluzione, MPI, Fair, ShellSet, Solver, OrbData o produzione.
7. Registrare `CODE_READY` vs `INTEGRATION_EXECUTED_NONCANONICAL` vs `SCIENTIFIC_QUALIFIED` vs `CANONICAL_AUTHORIZED`, test e gap nel ledger; preparare INT-0B come prossima NEXT soltanto dopo la chiusura di INT-0A.

## Traguardi successivi (NON autorizzazioni correnti)

- **INT-0B:** vera finestra candidata con output numerici, manifest, restart/replay, dopo autorizzazione.
- **INT-1:** confrontare full-state temporaneo, cadenza fissa, evento/errore/incertezza su campioni **misurati**: storage, tempo replay, perdita di eventi ed errori **per dominio**. Nessun `dt` o soglia arbitraria.
- **INT-2:** query/refinement/reconstruction multi-provider in staging.
- **INT-3+:** adapter pyGPlates/OrbData/ShellSet quando idonei, poi geologia, clima, idrologia, risorse, Deep, biosfera, popoli e storia 210 Ma→0 ka.

**Gates invariati:** `BLOCKED_F2AV_QUALIFICATION`, `OPERATOR_CLASS_UNVERIFIED`, `THRESHOLD_UNJUSTIFIED`, `RESOURCE_2GB_SCOPE_UNRESOLVED`, `F2B_SOLVER_EXECUTION_AUTHORIZED=false`, `ARCANA_SI1_MECHANICS_QUALIFIED=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
