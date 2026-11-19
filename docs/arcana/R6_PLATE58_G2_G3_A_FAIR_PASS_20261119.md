# R6 5:8 — Esito FAIR collegamento G2/G3 A, comunicato 2026-11-19

Commit verificato dall'operatore: `bac3977fbec872850e00b155105f275b36012291`. Runner eseguito su FAIR, checkout isolato `ARCANA_WORLD_R6_PLATE58_VERIFY`.

```json
{
  "tests": "9 passed in 0.12s",
  "status": "PASS_G2_G3_A_SOURCE_INTERFACE_BOUND__PHYSICAL_CLOSURE_OPEN",
  "halo_nodes": 25,
  "halo_triangles": 32,
  "core_triangles": 8,
  "exterior_triangles": 24,
  "interface_nodes": 8,
  "external_only_nodes": 16,
  "g2_PRE_columns_bound": 25,
  "G3_A_architecture_ratified": true,
  "G2_effective_constitutive_closure": null,
  "G3_A_physical_tangent": null,
  "mechanical_solve_authorized": false,
  "solver_runs": 0
}
```

Evidenza FAIR: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_G3_A_COUPLING_NEW_01`.

Questo rapporto deriva esclusivamente dal terminale riportato dall'operatore: SHA e file dell'evidenza esterna non sono stati importati o autenticati indipendentemente. **PASS = binding geometrico e PRE**, non solve, non forza, non materiale ratificato. La prossima implementazione sostanziale è il motore G2 di resistenza integrata parametrica, già pubblicato con questo report; occorre identificare materiali/coefficenti autorizzabili e confrontabili fisicamente prima di generarne output per le colonne ARCANA.
