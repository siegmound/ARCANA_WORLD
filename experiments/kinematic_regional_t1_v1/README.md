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
