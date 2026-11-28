# CURRENT — roadmap dopo G46, 2026-11-28

[Handoff G46](../docs/arcana/R6_G46_GAUGE_DATUM_NATIVE_RESTART_CLOSURE_20261128.md); [decisioni T0 e contratto G15](../docs/arcana/R6_G46_T0_DECISIONS_G15_EXECUTABLE_CONTRACT_20261128.md).

1. HPC G44 qualificato nello scope sintetico, G45 uniforme MPI e traccia AMR nel ramo dichiarato conservati. G46 restart nativo same/rank-change1/2/4/8PASS nel caso bounded; nessuna qualifica fisica globale implicita.
2. Gauge/datum: nuova variante coerente di geometria AMR, moti rigidi, tangenzialità e divergenza. Modi vicini al kernel non nulli; residuo originale saddle1.138e-6 e parità grezza fine ancora fuori soglia. Nessuna proiezione/fitting; esaminare prima gli operatori piccoli conservati.
3. A interfaccia: G36-R2/G37/G37B→trasferimento su mesh SHELLS/ASPECT reali e non coincidenti, lavoro/risultanti/momenti e reazione normale fisica; evitare doppio conteggio della colonna OneBar irrisolta.
4. B mantello completo:10decisioni T0 concrete su geometria interna/EOS/P/termica/composizione/acqua/reologia/flussi/perturbazioni/interfaccia/maschere, con autorità e ammissione. G43 condizionale e B6K geometrico non sono inizializzatori3D; M01 non selezionato.
5. C G15 corretto162anni indipendente: proposta JSON e preflight eseguibili, sorgenti FB2 slopey/sinA band/CSR e input T0 non evoluti verificati. Nuova inizializzazione meccanica e adapter di traiettoria da qualificare, poi matched halving/restart/massa/energia/stress/dissipazione. Nessuna nuova traiettoria autorizzata.
6. D-024 minimo sottosistema fisicamente chiuso→Physical T1→WORLD_HISTORY210Ma→0ka, ultimi200ka inclusi. Risorse naturali/Deep, clima/acqua/erosione/suoli/biomi, flora/fauna e popolazioni/civiltà; HistoryStore causale con query e raffinamento regione-epoca-processo, lineage/convergenza/incertezza,12anchor/CHA-1/H0 e500000000000byte provvisori. Nessun gate universale di tutti gli engine.

A_FULL_MANTLE_ADAPTIVE; D_024=D_025=ACTIVE; physical_T1=null; scientific_promotion=false; physical_acceptance=false; mantle_initial_state_admitted=false; mantle_provider_qualified=false; global_solve_authorized=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false; material_assignments=M01_engine_executions=ARCANA_solves=additional_time_advance_years=0.
