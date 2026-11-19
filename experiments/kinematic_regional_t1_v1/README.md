# Trasporto cinematico regionale R6

Dal worktree FAIR, con l'ambiente Python ARCANA e una directory di output nuova:

```sh
PYTHONPATH=src PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1 \
  python experiments/kinematic_regional_t1_v1/run.py /percorso/output-nuovo
```

Il driver verifica i pin, usa il ritaglio regionale già disponibile e registra
il caso a tassi Euler T0 fissi. Il figlio di restart apre il checkpoint salvato
e la relativa forzante nel backend HistoryStore. `RESULT.json` contiene gli
ID per `HistoryStore.read_state` e `read_forcing`; `T1_GEOMETRY.json` espone
latitudine, longitudine e XYZ canonico dei nove nodi. I payload mantengono PRE
come proprietà di riferimento T0. Scope `PRESCRIBED_KINEMATIC_ONLY`.

## Input per un checkout separato

Usare i byte originali degli archivi FAIR. Accanto al checkout predisporre:

```text
<directory comune>/
  ARCANA_WORLD/
  ARCANA_WORLD_EVIDENCE/R6/SHELLSET_REGIONAL_CASE_20261118_01/
    MANIFEST.json
    CASE.json
    regional.feg
    ... tutti gli altri file elencati in MANIFEST.json alla voce files
  _ARCANA_EXTERNAL_SOURCES/r6/
    tectonic_t0/R6_T0_VECTOR_PLATE_PARTITION.npz
    initial_world/r6run_2688234592b36fcdfe43428725d1369927c7f7625929c9ee1aad7f123ac9ba2b/
      R6_INITIAL_PHYSICAL_GEOGRAPHY.npz
```

1. Copiare il caso regionale sigillato nella directory sorella mantenendo
   i percorsi dei membri, inclusi quelli sotto `source/`. Il loader verifica
   tutti i membri elencati nel suo manifest. Copiare anche i due NPZ originali
   da `_ARCANA_EXTERNAL_SOURCES/r6/` nelle posizioni indicate.
2. Conservare i file di autorità T0 e i contratti B6I/B6J/B6K già presenti nel
   checkout. Preservare i byte anche nei checkout con conversione dei fine
   riga. `CASE.json` e i manifest B6 identificano i file del repository da
   verificare.
3. Se la partizione si trova altrove, impostare `ARCANA_EXTERNAL_ROOT`
   alla directory che contiene `r6/tectonic_t0/`. Il runner registra
   percorsi relativi alla directory comune, quindi anche la radice configurata
   deve trovarsi al suo interno. Il caso regionale e la geografia iniziale
   continuano a usare le directory sorelle indicate sopra.

| Input | SHA-256 |
| --- | --- |
| Manifest del caso regionale | `39072160dc78ef280bd423c04fd510754e1a9a775ac9f002ab6f4a182d7cfd90` |
| Partizione vettoriale T0 | `a3768b82598fb13a780c9c363f7031a437f952e75223d4400bfb5909461275ab` |
| Geografia fisica iniziale | `a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c` |

Dalla radice del checkout, con Python 3.11+ e le dipendenze ARCANA installate,
verificare gli input prima di scegliere una directory di output. Il controllo
legge i file, verifica gli SHA e la coerenza dei contratti.

```sh
PYTHONPATH=experiments/kinematic_regional_t1_v1:src PYTHONDONTWRITEBYTECODE=1 \
  python -c 'from run import load_inputs; _, pins, _ = load_inputs(); print(len(pins), "input verificati")'
```

Lo staging richiede solo il caso sigillato e i due payload indicati. Il report
FAIR e `KINEMATIC_REGIONAL_T1_20261118_01/campaign/INPUT_SHA256.json` documentano
l'esecuzione originale. [Report cinematico](../../docs/arcana/R6_KINEMATIC_REGIONAL_T1_EXPLORE_FAIR_20261118.md)
