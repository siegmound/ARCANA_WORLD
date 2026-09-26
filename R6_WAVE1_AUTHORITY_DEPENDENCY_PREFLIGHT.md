# R6 Wave-1 Authority Dependency Preflight

**Repository:** `siegmound/ARCANA_WORLD`
**HEAD / `origin/main`:** `592b1651b405363373590092e133bd25569d99a5`
**Determination:** `AUTHORITY_REGISTER_RECONCILIATION_REQUIRED`
**Wave-1 disposition:** `PARTIAL_SCOPED_REFERENCE_ONLY_WAVE1_FIXTURES_ALLOWED`

The checked-in Scientific Authority Register has basis HEAD `9577f1331e2f9715eb897c8330aedca58ae24f3a`, older than the current repository HEAD. Its exact climate, hydrology, paleohydrology, and freshwater entries and referenced hashes were checked narrowly. The referenced payload/authority-record hashes match the register. This supports only the entry's recorded, scoped status; it does not reconcile the register globally or certify the evidence afresh at current HEAD.

| Artifact | Register entry | Hash result | Recorded role | Wave-1 use |
|---|---|---|---|---|
| R3.14 `recent_paleoclimate_history.npz` | CLIMATE / PALEOCLIMATE | match | Direct legacy climate authority in register | Metadata/reference only; climate adapter uses a local synthetic fixture |
| `R5_17_B6_D3_CANONICAL_PALEOHYDROLOGY_REPLAY.json` | HYDROLOGY / PALEOHYDROLOGY | match | B6 replay authority/result descriptor | Identity/reference only; no payload replay or read |
| `R5_17_B6_H3_NATIVE_HYDROLOGY_GENERATOR_SEMANTICS.json` | HYDROLOGY | match | Native-generator semantic audit | Reference only; no generator call |
| `R5_17_B6_D4_FRESHWATER_ACCESS_AND_RELIABILITY.json` | FRESHWATER | match | Bounded derived-support authority descriptor | Reference only; no freshwater values consumed |

No recorded `superseded_by` value exists on these register entries. That is not a global claim that no newer provider/artifact exists. Wave 1 persists only fixture-labelled values and metadata. It performs no scientific simulation, provider acquisition, climate-value ingestion, hydrology replay, or authority promotion. Before any R6 scientific provider/domain run, reconcile the authority basis and bind its exact inputs under a scoped decision.
