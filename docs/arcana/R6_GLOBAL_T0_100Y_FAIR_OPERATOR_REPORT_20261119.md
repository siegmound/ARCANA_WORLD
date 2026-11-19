# ARCANA R6 — Risultato FAIR comunicato: benchmark globale 100 anni

Data: 2026-11-19. Report di terminale fornito dall'operatore, **non un nuovo accesso ai file FAIR**.
Sorgente GitHub testato: `716a1ba770331cd759ee4703545893235b7696bc`.
Output esterno:
`/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GLOBAL_T0_KINEMATIC_100Y_NEW_01`.

```text
tests/test_r6_global_100y_kinematic.py = 7/7 PASS
status = PASS_GLOBAL_T0_100Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED
model_years = 100
64,442 canonical unique vertices, 128,880 triangles, 64,800 faces, 12 plates
66,435 plate-local temporary material views
30 plate pairs with shared source node identities
max_xyz_drift_unit = 5.329070518200751e-15
max_radial_norm_error = 5.10702591327572e-15
max_triangle_area_change_sr = 7.3075226425523e-17
restart_50_plus_50_xyz_error = 0
all_milestones_accepted = true
source_load_wall_s = 0.7793337851762772
step_wall_sum_s = 0.12856468930840492
step_cpu_sum_s = 0.1284725430000001
step_wall_p50_s = 0.0012844931334257126
step_wall_p95_s = 0.0013042837381362915
step_wall_max_s = 0.0013717971742153168
checkpoint_io_wall_s = 0.018483232706785202
peak_rss_kib = 169476
instant_rss_kib = 113860
total_until_report_wall_s = 1.0948201455175877
solver_runs = 0
physical_deforming_T1 = null
```

## Adjudicazione

La Fase 1 di sola cinematica globale e PRE passivo è **PASS numerico**. Le differenze contro la rotazione diretta, l'area e la norma sono inferiori ai limiti dichiarati; replay 50+50 esatto nel campo XYZ. Questo non dimostra correttezza dei contatti G2/G3: il reporter stampa i massimi errori numerici, **non** il dettaglio delle separazioni tra placche ai milestone; i valori di `REPORT.json` restano nell'evidenza esterna e si leggeranno nella successiva comparativa.

La misura riguarda il software di rotazione rigida e caricamento sorgenti, non 100 anni di dissipazione, deformazione, erosione, trasporto risorse o storia biologica planetaria. Non estrapolare i tempi verso ShellSet meccanico.

Per la Fase 2 si può fare un benchmark 1000Y **solo** dopo verifica SHA del rapporto originale, dei tre checkpoint e della coerenza T0; questi vincoli sono ora integrati nel nuovo runner separato. **Non sostituire l'output Fase1, non riscrivere T1 canonico e non mutare lo stato del mondo.**

```text
GLOBAL_100Y=PASS_FAIR_OPERATOR_REPORT
GLOBAL_1000Y=CODE_PUBLISHED__FAIR_PENDING
PHYSICAL_G2_G3_SOLVE=BLOCKED
AUTHOR_RATIFIED_G3_A_EXPLORE=UNCHANGED
```
