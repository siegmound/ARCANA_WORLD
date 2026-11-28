# G46 — decisioni T0 e contratto G15 eseguibile

Proposta verificata, nessuna traiettoria o assegnazione. G15 riparte da geometria/termica iniziali non evolute; la meccanica T0 corretta deve essere ricostruita e qualificata prima di avanzare. I checkpoint112/162anni sono esclusi. Il validatore esegue i controlli sui pin e sulla policy senza lanciare solver.

| ID | Decisione autoriale richiesta | Dipendenze | Criterio di ammissione |
|---|---|---|---|
| T0-01 | choose source-supported interior reference model or author-declared fictional interior with explicit uncertainty | outer_geometry | positive mantle thickness, source domain, radial monotonicity, volume closure |
| T0-02 | choose EOS/reference mass/composition and source-consistent pressure/gravity solution | T0-01, T0-04 | dm/dr=4pi*r²*rho; g=Gm/r²; dP/dr=-rho*g; pressure units/reference bound |
| T0-03 | approve deep radial reference, top/basal thermal conditions and 3D anomaly policy | T0-01, T0-02 | enthalpy/EOS phase consistency, integral heat budget, masks/validity |
| T0-04 | select spatial material authority and mixtures, water/redox budget, phase/EOS package | T0-01 | sum fractions1, finite nonnegative stocks, source applicability; UNKNOWN preserved |
| T0-05 | bind pressure reference and equation coupling before compressible admission | T0-01, T0-02, T0-04 | reference source, hydrostatic and EOS consistency, no deltaP relabeling |
| T0-06 | choose valid deep temperature/composition/water/phase/stress dependence and bounds | T0-02, T0-03, T0-04, T0-05 | positive finite dissipation, source validity, uncertainty and numerical cutoffs explicit |
| T0-07 | choose sources and boundary conditions; separate unresolved lithospheric OneBar column from resolved mantle | T0-01, T0-03, T0-04 | energy closure, no overlap/double count, source lineage |
| T0-08 | approve deterministic generation, seed/spectrum/amplitude and relaxation budget after source choices | T0-03, T0-04, T0-06, T0-07 | no artificial immobilization, causal forcing, coupled common gauge, transient separated |
| T0-09 | approve physical stress partition/coupling only after real mesh transfer qualification | T0-01, T0-06 | adjoint force/moment/work, normal/radial partition, no torque projection or arbitrary pin |
| T0-10 | approve uncertainty and storage allocation without losing essential restart information | T0-01, T0-03, T0-04 | UNKNOWN and exclusions, causal checkpoints, anchor invariance, derived queries distinguished |

Tutti i valori assegnati e le scelte sono null. Il JSON contiene alternative, unità, autorità, piano di sensibilità/incertezza e controlli per ogni decisione. Nessuna adozione automatica di un CMB terrestre.

Contratto G15: macrointervalli1,1,10,25,25,25,25,50anni da T0 a162, confronto full/two-half e griglie termiche accoppiate, FB2 slopey/sinA, band/CSR, restart, massa/energia/stress/dissipazione e D12. Le soglie sono quelle delle policy originali; il nuovo adapter di traiettoria richiede ancora implementazione/qualifica e autorizzazione separata. Eseguibile oggi soltanto il preflight di contratto.


Il [contratto G15 JSON](../../experiments/r6_thermo_provider_pilot_v1/g46_constrained_gauge_v1/g15_corrected_executable_contract.json) lega i file effettivi e le policy; la [matrice T0 JSON](../../experiments/r6_thermo_provider_pilot_v1/g46_constrained_gauge_v1/mantle_T0_decision_matrix.json) contiene alternative, unità, sensibilità e ammissione. Il [validatore](../../experiments/r6_thermo_provider_pilot_v1/g46_constrained_gauge_v1/scientific_design.py) esegue soltanto il preflight con `--validate-only`; altri argomenti di esecuzione sono respinti. Nessun valore fisico scelto né adapter di traiettoria dichiarato già qualificato.
