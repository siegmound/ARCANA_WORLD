# ARCANA R6 — Fase 2: 1.000 anni globali, solo cinematica T0

Il benchmark FAIR **Fase 1 (100 anni)** è stato riportato dall'operatore sul commit
`716a1ba770331cd759ee4703545893235b7696bc`:
7/7 test PASS, `PASS_GLOBAL_T0_100Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED`,
64.442 nodi, 128.880 triangoli, 12 placche, 66.435 viste materiali, 30 coppie di placche con nodi sorgente condivisi.

Misure fornite: 0,779333785 s di caricamento, 0,128564689 s per i 100 passi annuali, 0,018483233 s I/O checkpoint, 1,094820146 s fino al rapporto; picco RSS 169.476 KiB. Drift XYZ 5,3291×10⁻¹⁵, norma radiale 5,1070×10⁻¹⁵, area firmata 7,3075×10⁻¹⁷ sr, ripresa 50+50 bit-identica. Questo è un **pass numerico della cinematica globale**, non fisica completa e non un benchmark di ShellSet G2/G3.

Il runner Fase 2 `phase2_1000y.py` **riutilizza senza modificare** il modulo sorgente della Fase 1, lega il REPORT e i tre checkpoint precedenti agli SHA del `MANIFEST.json`, conferma l'origine T0 e il limite temporale del primo segmento, poi esegue 1.000 avanzamenti annuali di tutte le dodici placche.

Confronti: 1.000 × 1 anno contro rotazione diretta; campioni 0/1/10/100/250/500/750/1000 anni; stato al 100-esimo anno **bit-identico** al vecchio checkpoint; nuovo replay 500+500 anni con confronto del campo XYZ; norme e area firmata; separazione di vista ai contatti (solo diagnostica); finestre di prestazione per ogni 100 anni, CPU/RAM/I/O e checkpoint completi agli anni 0,1,10,100,500,1000.

**Nessuna legge G2/G3, G4, evoluzione PRE, nuovo oceano o T1.** D-024 attiva; la ratifica EXPLORE G3 A resta valida per il lavoro successivo.

## Comandi FAIR

Usare lo stesso checkout isolato pulito, senza alterare l'originale né le evidenze esistenti.

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# STOP in caso di modifiche non committate
git fetch origin r6/multiphysics-integration-20261026
git switch --detach FETCH_HEAD
git rev-parse HEAD

source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:.
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

python -m pytest -q tests/test_r6_global_1000y_kinematic.py

PRIOR100=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GLOBAL_T0_KINEMATIC_100Y_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GLOBAL_T0_KINEMATIC_1000Y_NEW_01

python -m experiments.global_t0_kinematic_baseline_v1.phase2_1000y "$OUTPUT" \
  --prior100 "$PRIOR100" --years 1000
```

L'output è un nuovo `REPORT.json`, `MANIFEST.json` e sei checkpoint NPZ, solo nell'esclusiva directory indicata. I byte e gli hash della precedente evidenza 100Y vengono verificati **sia all'inizio che alla fine**. La directory 100Y resta immutata. Il codice `benchmark.py` resta limitato a 100Y; la Fase 2 usa il nuovo modulo.

**Stato atteso (non osservato su FAIR al momento della pubblicazione):**
`PASS_GLOBAL_T0_1000Y_KINEMATIC_BASELINE__CONTACTS_UNRESOLVED`.

Non inferire prestazioni meccaniche G2/G3 dai tempi della sola cinematica, non considerare un nodo ai contatti come un unico grado di libertà cinematico multivalore, e non promuovere un risultato Fase 2 a WORLD_HISTORY canonica.
