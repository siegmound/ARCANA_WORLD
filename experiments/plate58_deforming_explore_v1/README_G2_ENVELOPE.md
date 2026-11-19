# ARCANA R6 — G2: source PRE vs laboratory rheology (bounded diagnostic)

## Scopo

Il prossimo passo dopo i **6/6 PASS FAIR** sul contatto 5:8 non è un altro preflight geometrico: si valutano in modo quantitativo **i nove profili PRE autentici** rispetto alle due famiglie di proxy esplicitamente sperimentali (quarzite Black Hills senza fusione e mantello dry-olivine). Nessun parametro viene promosso a materiale ARCANA o a record LR SHELLS.

### Provenienza delle leggi

- Gleason & Tullis (1995), doi:10.1016/0040-1951(95)00011-B — quarzite naturale ~0.15 wt% acqua, **senza fusione, non anidra**; n=4, Q=223±56 kJ/mol; finestra ~900–1100 °C, ~1.5 GPa. Il coefficiente tabulato **A=1.1e−4 MPa^−4 s^−1** è riportato anche in Freed & Lin (2010), https://www.eaps.purdue.edu/freed/pdfs/2.pdf e review https://www.sciencedirect.com/science/article/abs/pii/S0264817211001425. Il valore qui è una **scelta esplicita di benchmark letteratura**, non un campo ARCANA. Il legge non include un coefficiente V identificato; l'assenza di V nel calcolo **non prova** che la pressione non influisca.
- Dry olivine: stessi coefficienti del provider esistente `src/arcana_worldsim/r6/material_rheology_provider.py` (ASPECT/Hirth–Kohlstedt 2003); non rappresenta la mineralogia originale ARCANA.
- Hirth–Teyssier–Dunlap (2001), doi:10.1007/s005310000152: la famiglia sensibile alla fugacità è **registrata ma non calcolata** senza un modello acqua/fugacità fisicamente definito.

I valori `GT_Q`, `GT_A`, `GT_n` sono **benchmark documentati**, non costitutivi ratificati. Il grado di estrapolazione va registrato come `UNVALIDATED`.

### Algoritmo

1. Verifica lo staging FAIR immutato da 4 celle e i suoi SHA, senza produrre una nuova FEG.
2. Carica gli autentici 9 nodi/51 campi PRE dal `CASE.json` precedentemente verificato.
3. Valida la continuità dei polinomi termici esistenti a superficie/Moho/LAB e ottiene T(z) a 9 punti per strato.
4. Calcola la **sola pressione litostatica di confronto** integrando le densità PRE e g=9.82 m/s² (stessa scala analitica già usata in FAIR, non pressione efficace/poro).
5. Per le tre larghezze **diagnostiche** 10/100/300 km usa i tassi `opening / width` già contenuti nel `CASE`, non tassi di deformazione osservati.
6. Valuta gli stress differenziali **triassiali, creep-only** della quarzite e, **separatamente**, lo sforzo scalare dal benchmark viscoso ASPECT del mantello \`2ηε̇\`, senza cap fragile; non li equipara tra loro né agli stress verticale-integrati di ShellSet.
7. Misura il confronto con la finestra T di laboratorio della quarzite e l'**errore di sola pendenza** del candidato comune `eCreep=0.267857` dopo ancoraggio degli stress alla fascia 100 km. Non lo interpreta come accuratezza del fit completo.
8. Stampa gli elementi ancora ignoti: fugacità, acqua, pressione di poro, Biot, attrito e resistenza limite, legge P crostale, fit integrato, trazioni N/S, sostegno basale.

**Nota:** il rapporto completo rimane in una directory FAIR di evidenze esterne dedicata, con SHA del `CASE` input e SHA del JSON generato; non si modifica mai il pacchetto sorgente. Il rapporto è una valutazione scientifica **non** un solve.

### Esecuzione nel checkout FAIR isolato e pulito

```bash
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

python -m pytest -q tests/test_r6_plate58_rheology_envelope.py

PRIOR=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_PT_ENVELOPE_NEW_01

python -m experiments.plate58_deforming_explore_v1.rheology_envelope "$PRIOR" "$OUTPUT"
```

**Non eseguire** `ShellSet`, G4, T1 o `HistoryStore`. Resta `G2_G3_PHYSICAL_CLOSURE=PARTIAL` finché non esiste la legge effettiva (compreso brittle/hydrology), e una chiusura meccanica G3 esterna/basale. Non ripetere altri test già PASS.

Il confronto 405/98 MPa a 10 km del precedente rapporto FAIR è indipendente da questo benchmark: **non deve essere riprodotto forzando un prefattore** se la convenzione, lo stato d'acqua o il tasso non coincidono.
