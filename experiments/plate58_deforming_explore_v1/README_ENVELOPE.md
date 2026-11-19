# ARCANA R6 — Step 2 G3: sorgente 16 celle e bordi esterni

Questo è uno **staging sperimentale di diagnostica fisica**, non un solve.
Si parte dal **pacchetto a 4 celle già verificato su FAIR** e si amplia la lettura
a 16 parent (R099–102/C020–023). Non si riscrive il pacchetto precedente.

## Contenuto e obiettivo

Il modulo `envelope.py` costruisce `REGIONAL_16.feg` (solo geometria parent)
e `NEIGHBORHOOD.json` verificando 25 nodi / 32 triangoli, plate ID,
topologia del contatto 5:8, orientamenti e registro autentico dei segmenti
`R6BND-T0-...`. La corrispondenza dei **due ID** del transetto originale
viene verificata sul registro di T0, non dedotta da un ordinamento.

Sui quattro tagli della regione salva per **ciascun segmento** il plate ID
sorgente, un campione della velocità Euler tangente nel frame sud/est
di SHELLS, geodesica, coordinate e i nodi di uscita del contatto.

Questi campioni sono **osservazioni cinematiche**, NON condizioni
meccaniche sul taglio. Su nord/sud `prescribed_velocity=null` e
`exterior_traction=null`; il solver non è autorizzato. La base normale
resta `null`. L'ipotesi precedente di *free-slip* tangenziale non genera
il sostegno normale, né il gauge Euler è un modello del moto del mantello.

Il rapporto riporta gli spaziamenti ortogonali dei lati FEG: la banda
sperimentale da 100 km è vicina alla griglia di un grado e non è stata
dimostrata convergente. I valori 405 e 98 MPa di due leggi candidate a
10 km sono **diagnostici riferiti dall'operatore FAIR**, non coefficienti
costitutivi già assegnati a SHELLS.

## Esecuzione FAIR (ambiente preesistente)

Nel checkout isolato del branch d'integrazione:

```bash
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1

python -m pytest -q tests/test_r6_plate58_envelope.py

PRIOR=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_NEIGHBOR_16_NEW_01
python -m experiments.plate58_deforming_explore_v1.envelope "$PRIOR" "$OUTPUT"
python -m experiments.plate58_deforming_explore_v1.check_envelope "$OUTPUT"
```

`OUTPUT` deve essere una directory **nuova**. Nessun file FAIR originale
deve essere sovrascritto. Conservare `MANIFEST.json`, `NEIGHBORHOOD.json`
e la FEG nella nuova radice di evidenze esterne.

## Decisioni fisiche successive

1. Valutare se l'estensione nord/sud può essere legata a una regione esterna
   con dati e legge di continuazione sorgente; altrimenti **STOP**, senza
   free/periodic/zero arbitrari.
2. Quantificare una reologia efficace crosta/mantello P–T–acqua tramite le
   due formule candidate, includendo limite fragile e errore di fit.
3. Definire sostegno normale basale e validità temporale del problema.
4. Soltanto dopo questi gate, qualificare un dominio adeguatamente
   risolto e un solve meccanico EXPLORE. Il contatto 5:8 non è una faglia
   ratificata, e un solver convergente non produce da sé T1 materiale.

**Status previsto:** `PASS_G3_NEIGHBOR_DIAGNOSTIC__SOLVE_BLOCKED`.

Referenze:
- `docs/arcana/R6_FIRST_DEFORMATION_MODEL_DECISION_FAIR_20261118.md`
- `experiments/plate58_deforming_explore_v1/README.md`
- D-024; decisioni originali su FAIR in
  `ARCANA_WORLD_EVIDENCE/R6/G2_G3_PHYSICAL_CLOSURE_20261119_01`.
