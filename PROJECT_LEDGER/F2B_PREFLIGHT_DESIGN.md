# F2-B preflight — specifica del lavoro da PROGETTARE
**Stato:** `DESIGN_ELIGIBLE_NOT_EXECUTION_AUTHORITY` (giudizio della review F2A-V 2026-10-10). Documento di scope non sostituisce il contratto F2-B che deve ancora essere progettato.

## Domanda
Può un futuro run bounded engineering-only di ShellSet sull'operatore ARCANA SI1 produrre una soluzione numericamente interpretabile e riproducibile, rispettando source locks, vincoli di risorse e separazione dalle autorità fisiche/canoniche? Non basta che un solve termini con exit 0.

## Capacità già dimostrate — NON ripetere
- ShellSet upstream Fair NVIDIA/MPI `ListEx1` 9/9 modelli, LAPACK smokes: `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json`.
- ARCANA T0 FEG/runtime load governato (limited): `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json`.
- F2-A/F2A-V matrix assembly e evidence recovery: `docs/arcana/SI1_BW1_F2AV_DIAGNOSTIC.md` + risultati recuperati. Gli stop pre-Solver non sono solve.

## Input specifici
`configs/r6_shells_si1/engineering_case.json`, `configs/r6_shells_si1/shellset_source_lock.json`, sorgente esatto `external/ShellSet-v1.1.0/`, code runner SI1/BW1, sealed F2-A e recovered F2A-V. Il caso ha 64442 nodes, 128880 triangles, 0 fault elements, 0 BC prescribed velocity, parametri `ENGINEERING_SOLVER_REFERENCE_NOT_ARCANA_GEOLOGY`.

## Blocchi tecnici per progettazione
- `DOF_MAPPING_UNVERIFIED` dopo reordering: non attribuire coordinate/placche/strutture alle righe grezze.
- Classificazione dell'operatore e aspettativa di simmetria non provate; 10 pair oltre soglia, 1 zero/nonzero, 9 nonzero mismatch.
- Scala coefficients e non-dominanza (0 strict, 128884 nonstrict) sono diagnostiche, non prove di singularità.
- Nessun test di condizionamento/nullspace/gauge; nessuna riparazione arbitraria o fissaggio di rigid body modes.
- Correzione writer non ancora provata con NVHPC; instrumentation IEEE inherited flags non attribuibile a istruzione/causa.
- Memoria: band `2182*128884*8=2249799104` bytes `~2.095 GiB`, non total process; futuro fattore/solve può richiedere altre allocazioni e risorse.

## Output di design richiesti
- `operator_classification`: aspettativa di simmetria provata dai sorgenti oppure `UNKNOWN`.
- `dof_mapping_contract`: mappa index/permutation/node/basis o `UNKNOWN` con specifica degli artefatti mancanti.
- `gauge_policy`: fonte, ipotesi e limiti, senza alterazione delle equazioni.
- `solver_options`: criteri per scegliere percorso numerico coerente con tipo di matrice e storage; nessun solver selezionato per convenienza.
- `resource_envelope`: stime dimostrate per process/rank, fill/workspaces, limiti HPC e abort.
- `validation_metrics`: residual/backward-error con normalizzazione, significato fisico limitato, reference/reproducibility, failure routing.
- `NVHPC_gate`: compile/source proof del writer e IEEE; distinto dal run risolutivo.
- `execution_authority_request`: gate esplicito separato, motivato, fail-closed. Non invocare Fair senza autorizzazione.

## Criteri chiusura progettuale
Design può chiudere anche con gap irrisolti, ma non promuovere `F2B_SOLVE_AUTHORIZED` fino a prova e decisione separata. Nessun `SYMMETRIZE`, `AUTOGAUGE`, `EARTH BC`, `FORWARD_EVOLUTION`, `CANONICAL_STATE_WRITE`. Conservare `UNKNOWN`.

## Collegamento all'obiettivo ARCANA
Il risultato F2-B, se in futuro autorizzato e valido, riguarda un **provider tettonico** al servizio dell'orchestratore a finestre temporali, della storia causale di risorse, Deep, flora/fauna e comunità. Non ridefinisce né l'architettura B6N6 né la necessità dei provider ambientali/multidominio.
