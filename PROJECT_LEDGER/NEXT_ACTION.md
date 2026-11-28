# CURRENT — next: constrained rotational gauge / datum design

Preparare un nuovo contratto sintetico per il gauge rotazionale compatibile con hanging-node, no-normal e operatore discreto; analizzare identità di divergenza/quadratura volume-bordo per il datum e stabilità della velocità a 8 rank. Conservare i fallimenti G45; niente proiezione/fitting per far passare i gate. Riusare plugin/runtime e dati esistenti prima di nuovi run. [Handoff](../docs/arcana/R6_G45_DISTRIBUTED_AMR_CBF_CLOSURE_20261128.md).

Il restart richiede un’API nativa t0 dimostrata o autorizzazione esplicita di un intervallo sintetico nonzero; non chiamare restart un export/readback. Solo progettazione T0/G15 già effettuata, nessun M01 o nuova traiettoria implicito. Futuri run richiedono scope e criteri propri.

A_FULL_MANTLE_ADAPTIVE; D-024/D-025 ACTIVE; physical_T1=null; scientific_promotion=false; physical_acceptance=false; mantle_initial_state_admitted=false; mantle_provider_qualified=false; global_solve_authorized=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false; material_assignments=0; ARCANA_solves=0; additional_time_advance_years=0.
