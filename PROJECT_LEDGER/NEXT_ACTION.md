# CURRENT — prossimo task: G45 synthetic AMR / MPI CBF contract

Preparare e verificare il contratto sintetico per adattività e flussi consistenti distribuiti, usando il runtime HPC qualificato e root nuovi. Leggere [handoff G44](../docs/arcana/R6_G44_FAIR_HPC_QUALIFICATION_CLOSURE_20261128.md), i report G41/G42 originali, le assert singleton e gli hash prima di modificare codice.

Acceptance proposte: Q2 uniforme→AMR;1/2/4/8rank; ownership/ghost e quadratura; gauge/pressione; lavoro, risultanti/momenti e bilanci; convergenza analitica e parità; negativi su orientazione/copertura/duplicazione; restart. Non togliere assert singleton per far passare MPI. Definire prima tolleranze giustificate e budget; non reinterpretare G42rank1 come già MPI.

L'esecuzione di questa futura campagna necessita scope sintetico e contratto espliciti; nessun solve ARCANA è autorizzato dalla chiusura HPC. Poi riprendere reazione normale/mesh reali (A), fonti stato mantellare/M01 (B) e G15corretto162anni/restart (C), secondo dipendenze reali.

Architecture A_FULL_MANTLE_ADAPTIVE; physical_T1=null; scientific_promotion=false; physical_acceptance=false; mantle_initial_state_admitted=false; mantle_provider_qualified=false; global_solve_authorized=false; WORLD_HISTORY_PRODUCTION_AUTHORIZED=false. Material assignments=0, ARCANA solves=0, additional time=0 years. D-024/D-025 ACTIVE.

[Precedenti task storici](archive/G44_20261128_PRE_CLOSURE_NEW01/NEXT_ACTION.md).
