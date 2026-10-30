# Architettura di orchestrazione e retention

```text
Condizioni iniziali e contratti di autorità
      |
ARCANA scheduler / finestre candidate e dipendenze
      |
Provider qualificati per dominio (tettonica, superficie, clima,
idrologia, suolo/materiali, risorse, Deep, biosfera, popolazioni ...)
      |
ARCANA adapters: coordinate, unità, tempo, support, versioni,
validità, conflitti, UNKNOWN, provenance, forcing, errori
      |
Traiettoria candidata temporanea -> verifica, eventi, raffinamento,
significatività e replay closure
      |
HistoryStore: eventi + stati sparsi + checkpoint + recipes + WHY
```

**Già definite/implementate in parti:** core B0 (store atomico, query, replay/recipes, refinement child branches, retention), B6N4-A policy di significatività, B6N6 architettura del controller adattivo e dell'estrazione. B6N6 è **ARCHITECTURE_ONLY_NOT_EXECUTION_AUTHORITY**: non implica orchestratore produttivo, dt selezionato, propagazione o pubblicazione.

**Gap attuativi distinti:** binding dei provider, disponibilità scientifica e autorità delle leggi, adapter tra domini, decisione su UNKNOWN, controllo numerico/eventi/step, tolleranze di ricostruzione per dominio, valida archiviazione e replay. Non colmare una lacuna di fisica/autorità facendo semplicemente più refinement.

**Stati sparsi, non snapshot a cadenza fissa:** evento != stato. Possono esistere `EVENT_ONLY`, transizioni con PRE/POST, checkpoint per errore di ricostruzione o limiti di validità. Il time bracket di un evento va conservato; non inventare l'istante esatto.

**Ambiti:** ShellSet è un provider meccanico/tectonico candidato, non ARCANA intero. La sua qualifica avviene su una pista indipendente dalla pipeline geometrica/kinematica B6. I risultati legacy R3–R5 non sono output-obiettivo R6.

Fonti: `docs/arcana/B6N4A_EVENT_IMPACT_AND_STATE_SIGNIFICANCE.md`, `docs/arcana/B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE.md`, `docs/arcana/PROVIDER_REGISTRY.md`, `R4_0_MULTI_ENGINE_ORCHESTRATOR_CONTRACT.md` (storico, non governante su R6).

## Direction update — 2026-10-30 (R6-INT10K; not implemented)

**Independently adaptive domain retention, causally consistent WORLD_HISTORY:** logical domain/region streams (geology/materials, hydrology, Deep, climate, biology, populations), each with domain-specific event, delta and state-significance rules, replay/checkpoint coverage and provenance. Calm reconstructible intervals retain sparse states; intense transitions/uncertainty/irreversible impacts retain dense event boundaries and PRE/POST when required. A change in one domain does not cause a redundant global state copy, but genuine cross-domain effects and coupling must be recorded. A global catalog binds compatible domain read views and solver-restart frontiers, with atomic coupling and explicit UNKNOWN. Logical separation does not require new uncoordinated DB servers or replace B0. Based on B6N4-A/B6N6; source contracts remain governing, no numerical thresholds invented.

**Current priority:** eliminate repeated simulation JSON copies/serializations and measure real wall/CPU; requalify exact original oracles before 10k integrated synthetic benchmark. Only after that pursue 100k candidate and retrospective adaptive sampling; long-history B0 manifest/index optimization deferred. See `PROJECT_LEDGER/R6_INT10K_B2B3S_PASS_DOMAIN_RETENTION_RUNTIME_FIRST_20261030.md`. No production/science/solver authorization follows.
