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
