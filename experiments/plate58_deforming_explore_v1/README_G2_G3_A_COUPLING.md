# ARCANA R6 — G2/G3 A: prima integrazione strutturale continua 5:8

**Status di questo commit:** codice di integrazione e test pubblicati; **NON ancora eseguiti su FAIR**. G3 esterno A è approvato per EXPLORE (non sono approvati materiali/forze) e D-024 resta bloccante.

## Risultato tecnico (non smoke aggiuntivo)

I due artefatti FAIR già presenti contengono il nucleo centrale **4 celle/9 nodi/8 triangoli** e il dominio di continuazione **16 celle/25 nodi/32 triangoli**. Il codice `coupling_A.py` congiunge attraverso identità sorgente e archivi SHA-verificati:
- gli **8 nodi e 8 archi condivisi** core/exterior, mantenuti come **un singolo DOF fisico per nodo** nel continuo;
- i **16 nodi esterni-only** e **24 triangoli** dell'anello;
- le **25 colonne PRE source-bound** dell'intero dominio, con stato idrico/materiale e numeri LR rigorosamente non assegnati;
- i **sei segmenti di contatto T0** nel 16-cell, con mapping source IDs e senza inventare una faglia.

La vera integrazione meccanica non consiste nell'imporre Euler diversi allo stesso nodo. L'interfaccia G3 A usa la *risposta meccanica del continuo esterno*:

`K_eff = K_bb - K_be K_ee^{-1} K_eb`, `f_eff = f_b - K_be K_ee^{-1} f_e`.

Il modulo contiene già la condensazione numerica esatta di un **tangente esterno realmente fornito**, la soluzione di recupero del dominio eliminato e test di equilibrio/reazioni. I test usano una **matrice sintetica dichiarata** e non sono un solve geofisico. L'input fisico `K` e `f` è intenzionalmente **null**: serve una reologia G2 completa e un dominio esterno A vincolato da condizioni di bordo e bilancio basale documentati. Non si derivano trazioni dall'Euler né si impongono `free` o `zero` sui tagli N/S. Una matrice reale ShellSet deve prima essere tradotta in DOF e frame coerenti, con verifica di gauge/rango, lavoro e residui.

**Il 16-cell rappresenta il primo anello numerico di connessione, non un esterno sufficientemente esteso e con BC validate.** Il futuro provider deve espandere e qualificare l'esterno; non sostituire questa necessità con un anello di 16 celle già dichiarato fisicamente chiuso.

## FAIR (worktree pulito isolato; nuova evidenza esclusiva)

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# Se sporco: STOP. Se pulito:
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

python -m pytest -q tests/test_r6_g2_g3_A_coupling.py

STAGE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
HALO=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_NEIGHBOR_16_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_G3_A_COUPLING_NEW_01

python -m experiments.plate58_deforming_explore_v1.coupling_A "$STAGE" "$HALO" "$OUTPUT"
```

Il modulo genera `GEOMETRY.json`, `G2_PRE_BINDING.json`, `G3_A_TRANSFER_CONTRACT.json`, `MANIFEST.json` in nuova directory. Le evidenze precedenti e le autorità canoniche restano immutate.

**Output previsto, da confermare FAIR**:
`PASS_G2_G3_A_SOURCE_INTERFACE_BOUND__PHYSICAL_CLOSURE_OPEN`.

## Azioni successive fisicamente sostanziali

1. **G2:** identificare/motivare le leggi reologiche con fonte e unità per l'intera crosta (inclusi intervalli freddi, fragile/duttile, P efficace, acqua, Biot) e mantello; calcolare proiezione sui 25 nodi, parametri SHELLS e valutare integrated-strength, non presumere GT95 valido per 81 campioni.
2. **G3 A:** continuare il dominio almeno fino a condizioni distali fisicamente motivabili, costruire un reale operatore esterno derivato da quelle leggi G2 e dalle forze incluse in SHELLS; base normale/tangenziale e non duplicazione GPE.
3. Solo a quel punto applicare il trasferimento condensato all'interno, chiudere residui/reazioni e proporre un **singolo solve EXPLORE non canonico**, previo titolo di autorità. Il primo layer planetario 1000Y rimane semplice baseline cinematica e non validazione di questa fisica.
