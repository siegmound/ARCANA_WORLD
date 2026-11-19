# ShellSet regionale ARCANA T0

Dal worktree, con Python dell'ambiente ARCANA e NumPy, eseguire:

```bash
export PYTHONPATH=src
export PYTHONDONTWRITEBYTECODE=1
python experiments/shellset_regional_explore_v1/build_case.py /tmp/arcana-region-new
python experiments/shellset_regional_explore_v1/check_case.py /tmp/arcana-region-new
```

Il primo comando richiede una directory nuova. Il secondo usa `gfortran` per
provare i lettori PRE globale e regionale in una directory temporanea.
La prova confronta i record PRE, temperatura e proprietà a quattro profondità
per nodo e controlla il mapping degli output con dati di prova.

`regional.feg` usa la numerazione locale 1–9. `CASE.json` conserva il riferimento
ai nodi e ai triangoli parent, gli owner PRE e il circuito di bordo. Il submodello
PRE ha marker e schema propri e richiede la ricompilazione isolata con
`MOD_ArcanaRuntime.regional.f90`. In una futura directory privata del caso,
lo staging esistente di ShellSet cerca il payload regionale sotto il nome
`INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat`. Usare quel nome solo
nella directory privata. Il test compila il solo lettore con un programma
di prova. L'integrazione con il binario ShellSet completo è ancora da verificare.

`solution_mapping.bind_solution` prende i campi estratti da un risultato
convergente, già associati a questa FEG e in unità SI. Il chiamante deve
verificare gli SHA del caso e della configurazione e la convergenza. La funzione
riporta al frame canonico le velocità nodali e conserva la base runtime e le
sette coppie di indici elemento/punto EDot per il tensore di deformazione.

Il verdetto del caso è `BLOCKED_EXACT_G2_G3_INPUTS`. La configurazione
meccanica rimane incompleta e la directory non contiene un comando di solve.

## Smoke del modulo SHELLS completo

Preparare una nuova directory con `stage_smoke.py` (stesso PYTHONPATH).
Compilare in quella directory. Il comando e le misure originali sono in
`build_final.time` nell'evidenza dello smoke.

```bash
sdk=/opt/nvidia/hpc_sdk/Linux_x86_64/25.11
"$sdk/compilers/bin/nvfortran" -O0 -Mbackslash -Kieee \
  MOD_SharedVars.f90 MOD_ArcanaRuntime.f90 MOD_ShellSet.f90 DMods.f90 \
  MOD_Shells.f90 SHELLS_v5.0.f90 smoke_driver.f90 \
  -L"$sdk/compilers/lib" -Wl,-rpath,"$sdk/compilers/lib" -llapack -lblas \
  -o regional_smoke.exe
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 timeout 60 ./regional_smoke.exe > solve.stdout 2> solve.stderr
printf '%s\n' "$?" > solve.exit
```

Dal worktree, `check_smoke.py` riceve il percorso della directory e legge solo
gli output salvati. Lo smoke appartiene a ENGINEERING_ONLY e chiama SHELLS
direttamente da un driver seriale.
