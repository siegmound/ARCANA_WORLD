# ARCANA R6 — Conversione del creep G2 verso la convenzione reale SHELLS

**2026-11-19**. I test del motore G2 `test_r6_g2_whole_column_provider.py` sono **7/7 PASS su FAIR**, checkout isolato, commit `1d2138a46b32622988635a16f515d0e312548c5e`. Nessun esecutore di reologia è stato lanciato sul vero PRE con parametri fittizi. Output del nuovo modulo `shells_lr_bridge.py` NON ancora verificato FAIR.

## Findings nel codice originale di SHELLS (NON dalle sole descrizioni generiche)

Le sorgenti consultate sono:
- `external/ShellSet-v1.1.0/src/MOD_Shells.f90`, `Diamnd` intorno alle righe 2253–2351, 2494–2542, 2868–2904; uso dei parametri nei blocchi di creep `Mohr` 6138–6139;
- `external/ShellSet-v1.1.0/src/MOD_ShellSet.f90`, lettura e descrizioni LR circa 2682–2774.

La forma della legge di creep, nel dominio del medesimo invariante di strain rate, è
```
σ_creep_scale = aCreep * ε_II ^ eCreep
                * exp((bCreep + cCreep * z_absolute) / T(z)).
```
L'origine della pressione per il mantello deve **includere** la colonna crostale preesistente (Moho), non resettarsi a P=0. Per un campo PRE con densità costante per ciascun layer, un candidato dislocation creep ASPECT
`ε_II=A_eff σ_II^n exp(-(E+P V)/(R T))` può essere espresso algebricamente (stesso invariante!) come:
```
eCreep = 1/n
aCreep = A_eff ^ (-1/n)
bCreep = (E + P_intercept V)/(n R)
cCreep = rho_layer * g * V/(n R)
P(z_abs) = P_intercept + rho_layer*g*z_abs
P_intercept_crust = 0
P_intercept_mantle = g*z_Moho*(rho_crust - rho_mantle)
```
L'esattezza è verificata sulle temperature T0 PRE e su tre strain rates esplicitamente all'interno del dominio di calibrazione. **L'equivalenza riguarda la forma costitutiva del creep, non la risposta completa di SHELLS**: `Diamnd` usa invarianti e angoli principali, limite `dCreep`, attrito, transizione fragile/duttile, limiti di viscosità, condizioni al contorno e forze da GPE. Il fattore del valutatore G2 che confronta stress fluente e attrito NON può essere trasposto nel `aCreep` SHELLS: è una conversione tra convenzioni diverse.

### Vincolo bloccante identificato

**Un singolo record LR di SHELLS ha `eCreep` comune per crosta e mantello.** GT95 (`n=4`) e benchmark olivina (`n=3.5`) quindi non possono essere trascritti *esattamente* nello stesso LR: `0.25 != 0.285714...`. Il candidato `common_eCreep=0.267857` noto dal vecchio screening equivale solo a uno slope fit; un errore 4% sulle pendenze non valida il comportamento integrato in P,T né giustifica la mineralogia. L'adattatore emette `SHELLS_eCreep_shared_exactly_compatible=false` e **non** media automaticamente.

### Non confondere `Byerly` e Byerlee

Nel `MOD_ShellSet.f90` il parametro testuale `Byerly` riguarda la *riduzione dell'attrito su faglie con offset*; non è la legge fragile bilineare di Byerlee (1978). `cFric` è un singolo coefficiente di attrito **all'interno dei blocchi**, e la bilineare `τ=0.85 σ_eff` / `50 MPa+0.6 σ_eff` non si converte direttamente in `cFric` senza un modello di pressione efficace, coesione, angoli e piano di frattura. Il coefficiente `Biot` è distinto e impatta la pressione effettiva. Il modello attuale G2 whole-column resta un *envelope di un candidato*, non un `Diamnd` completo.

## Funzione implementata

`candidate_to_shells_form(pre, scenario)`:
- richiede legge esplicita con P/T/strain rate, acqua/fugacità se dipendente, note di provenienza; non introduce parametri default del mondo;
- verifica a due layer il lavoro equivalente sulla forma del creep a più profondità e strain rate, inclusa la correzione di intercetta per pressione al Moho;
- rifiuta estrapolazioni oltre validità dichiarata e parametrizzazioni non finite;
- dichiara se il singolo `eCreep` è **algebricamente compatibile**;
- mantiene `SHELLS_full_LR_coefficients=null`, `dCreep/cFric/Biot/Byerly=null`, `K_G3=null`, `T1=null` anche dopo un pass numerico.

`shells_lr_bridge.py` include inoltre un esecutore facoltativo SHA-bound per 25 colonne PRE dal precedente pacchetto FAIR, **NON DA ESEGUIRE** finché non esiste uno scenario completo con dominio calibrato.

## FAIR — test matematica e sorgenti ShellSet (nessun solve)

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# Se output vuoto, continua:
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
python -m pytest -q tests/test_r6_shells_lr_creep_bridge.py
```

Il nuovo audit verifica una equivalenza **algebrica** in un esempio sintetico, il caso comune `e` valido, il caso n diversi rifiutato, le unità e la pressione stratigrafica, e che non ci sia promozione a un LR fisico. Nessun T1, nessuna modifica al canone.

**Prossima azione sostanziale:** decidere se usare un formalismo di creep comune a entrambi i layer con calibrazione documentabile, modificare SHELLS in una variante sperimentale con `eCreep` distinti e prova di equivalenza, oppure mantenere il codice invariato e qualificare un fit unico su più rate/P/T con errore fisico dichiarato. Questo deve essere risolto insieme a acqua/pressione efficace/frizione ed estensione G3 A per non creare condizioni artificiali.
