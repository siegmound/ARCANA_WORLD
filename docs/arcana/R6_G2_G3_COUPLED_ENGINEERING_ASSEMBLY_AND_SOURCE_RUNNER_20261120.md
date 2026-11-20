# ARCANA R6 — Integrazione software G2/G3 (weak form accoppiata)

**Data:** 2026-11-20. **Modello selezionato:** `REGIONAL_THIN_LITHOSPHERE_SPHERICAL_P1_FACET_VISCO_PLASTIC_EXPLORE`. **Stato:** codice candidato, verifica FAIR da eseguire, **non** solve fisico e **non** autorizzazione di T1.

## 1. Significato di «integrazione completa»

L'integrazione **strutturale e numerica** dei canali G2 e G3 ora è un'unica chiamata esplicita, costruita usando le implementazioni preesistenti. Non significa che sia stato identificato un materiale reale, determinata una trazione geologica, o risolto un modello di faglia. I dati fisici mancanti sono `null`, mai riempiti con zero o con valori di letteratura extrapolati.

Codice nuovo:
- `experiments/plate58_deforming_explore_v1/g2_g3_coupled_weak_form.py`: assemblaggio globale source-ID keyed;
- `experiments/plate58_deforming_explore_v1/g2_g3_source_coupled_runner.py`: collega gli artefatti autentici FAIR (multiscale → G3 interface → G2 nodal/PRE → G3 force inventory), con SHA256/manifest chain verificata e scenario candidato **obbligatorio**;
- `experiments/plate58_deforming_explore_v1/G2_G3_EXPLICIT_ENGINEERING_INPUT_TEMPLATE_V1.json`: template JSON **non eseguibile finché incompleto**;
- `tests/test_r6_g2_g3_coupled_weak_form.py` e `tests/test_r6_g2_g3_source_coupled_runner.py`: calcolo integrato su piccola geometria **SINTETICA**, più fail-closed dei provider.

## 2. Un solo sistema di DOF

La mesh G3 A autentica ha 81 nodi nel rettangolo 8×8 e 289 nel 16×16, ma il **dominio esterno meccanico G3 A** esclude un nodo interno al core: i gradi di libertà East/North sono perciò **80 nodi/120 triangoli/32 tagli** per 8×8 e **288 nodi/504 triangoli/64 tagli** per 16×16. Il nodo parent 34587 resta nel T0 source e nella giunzione tripla 5:8:11; la sua appartenenza ai nodi del solo esterno non è presunta. Non vengono duplicati nodi o stati meccanici sul confine o sulla giunzione.

Il runner legge `CONTINUATION_A.json`, `MULTISCALE_INTERFACE.json`, `SOURCE_NODAL_ELEMENT_G2.json` e `FORCE_BUDGET_REQUIREMENTS.json` con tutti i relativi `MANIFEST.json`, ne controlla status, file hash e catena d'origine. Poi verifica gli hash della FEG e del PRE originali e ricostruisce solo i nodi/triangoli `source_exterior_triangles` di G3. Il provider `node_id`, gli ID dei triangoli, i codici di configurazione e le quadrature source sono mantenuti senza inferenza di mineralogia.

## 3. G2 → G3: potenziale e tangente

Per ogni elemento P1 originale e ogni velocità nodale locale (u_e) in m/s:

```text
B_e = spherical_triangle_geometry(lat_lon_originale).strain_operator
epsilon_e = B_e * u_e

[Phi_e, N_e, D_e] =
    vertex_quadrature_response(
      source_owned_parent_triangle, original_PRE_nodes,
      EXPLICIT_candidate_laws_by_source_node,
      epsilon_e, evaluator=g2_viscoplastic_explore.potential_gradient_tangent
    )

f_internal,e = A_e * B_e^T * N_e
K_tangent,e  = A_e * B_e^T * D_e * B_e
```

Somma delle componenti per la stessa coppia parent-node East/North; `f_internal` in N, `K_tangent` in N s/m, potenziale di dissipazione integrato. **Il G2 candidato include due esponenti di creep indipendenti e un cap armonico 3D Drucker–Prager, ma NON un return mapping elastoplastico né una legge fisica di faglia.** La quadratura 1/3 per vertice non costituisce una legge fisica ratificata per materiali eterogenei. Tutte le singole colonne PRE e gli scenari G2 sono richiesti; nessun materiale viene dedotto dal codice di configurazione o da assenza di flag.

## 4. Forzanti G3 e GPE: un solo proprietario

La stessa esatta lista di parent-node EN DOF è inviata a `g3_force_budget.assemble_explicit_g3_loads` e `g3_gpe_force_accounting.compose_candidate_nodal_loads` con **tutti** i tagli e triangoli basali originali e coefficienti esplicitamente forniti.

```text
f_external = f_outer_cut + f_basal_tangential + f_GPE_external_once
R(u)       = f_internal(u) - f_external
K(u)       = d f_internal(u) / d u
virtual_power_residual = u · R
```

Sono forniti residuo, tangente, lavoro virtuale per canale, risultanti e momenti 3D dei carichi. Il GPE esterno richiede esattamente `EXPERIMENTAL_EXTERNAL_GPE_ONLY__ORIGINAL_SHELLS_GPE_NOT_COMBINED`, e l'assemblaggio rifiuta mismatch di ordine, forze extra nascoste e doppio conteggio. I valori di GPE numerici del modello attuale restano un **esperimento**, non il sostegno verticale fisico. Nessuna reazione basale normale è generata automaticamente.

**Non viene invocato alcun Newton solve, KKT aggiornato, inserimento G4 o HistoryStore.** Un residuo numerico calcolato non è un residuo di equilibrio fisicamente valido se manca la vera forza o il materiale.

## 5. Input richiesto prima del runner reale

Il template `G2_G3_EXPLICIT_ENGINEERING_INPUT_TEMPLATE_V1.json` contiene deliberatamente `null`. Per ciascun parent-node G3 esterno occorrono: legge G2 **esplicita** con P/T/rate domain, acqua/fugacità, pore/Biot e riferimento scientifico, più velocità EN. Per ogni taglio esterno: `source_parent_node_ids`, lato, owner, trazione tangente nodale in N/m. Per ogni triangolo basale: owner e trazioni in N/m². Il `external_gpe` deve avere forza nodale, lista **identica** dei parent DOF e unico proprietario GPE. Le quattro SHA dei manifest originali devono corrispondere ai file FAIR disponibili.

Il runner rifiuta `null`, canali incompleti o fonte incoerente. Esempi con trazioni esattamente zero sono **solo test sintetici**, non input per l'esperimento geologico.

## 6. Bloccanti scientifici per la fisica G2/G3 reale

Già registrati in `docs/arcana/R6_G2_G3_A_PHYSICAL_CLOSURE_ADJUDICATION_20261119.md`, `docs/arcana/R6_G2_G3_EMPIRICAL_CALIBRATION_FAIR_PASS_20261120.md` e `docs/arcana/R6_G2_G3_PAIRED_PHYSICAL_SCENARIO_DECISION_20261119.md`. Occorrono congiuntamente:

1. G2: minerali e acqua della crosta/mantello ARCANA, leggi di laboratorio con vera copertura P/T/rate e misure individuali, pore/effective stress, attrito, danno/faglia, selezione del solver (original SHELLS con esponente comune oppure EXPLORE 2 esponenti provato completo). GT95 non copre la crosta fredda a T0, quindi non può essere estrapolato silenziosamente.
2. G3: provider fisico per tutte le trazioni ai tagli N/S/E/W, velocità mantello profondo, taglio/pressione basale e risposta verticale; rango/gauge e forza/torque/virtual-work su campo realmente qualificato; GPE senza duplicare il `Squeez/Fixed` di SHELLS.
3. Contatto: scelta fisica autorizzata fra una vera legge thin-sheet di faglia/slip/trasmissione e una geometria volumetrica 3D orientata. Le precedenti aperture firmate dei bordi materiali sono diagnostiche della shell, **non** un gap solido.
4. Solo dopo una autorizzazione esplicita per un esperimento meccanico non canonico, si potrà integrare temporalmente con controlli di stabilità, conservazione e successivo coupling G4.

**Decisione:** `SOFTWARE_COUPLING_IMPLEMENTED__PHYSICAL_INPUTS_AND_LAW_NOT_RATIFIED` (soggetta a FAIR PASS del nuovo codice). `D-024=ACTIVE`; `physical_T1=null`; `mechanical_solve_authorized=false`; `physical_solver_runs=0`; nessuna promozione canonica.
