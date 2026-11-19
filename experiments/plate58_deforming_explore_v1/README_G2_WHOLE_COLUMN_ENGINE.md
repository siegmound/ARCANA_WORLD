# ARCANA R6 — G2 calcolo di resistenza integrata, 25 colonne (candidato parametrico)

**2026-11-19** — Il collegamento G2/G3 A sul 5:8 ha passato **9/9 test FAIR** al commit `bac3977fbec872850e00b155105f275b36012291`, e ha restituito correttamente 8 nodi di interfaccia, 24 triangoli esterni, 16 nodi esclusivi, **25 colonne PRE**. Questi sono dati di terminale FAIR comunicati dall'operatore; i file esterni non sono stati importati.

## Il nuovo componente fisico implementato

`full_column.py` è un valutatore di una **ipotesi costitutiva esplicita** di crosta e mantello. Per ogni profondità usa:
- i polinomi di temperatura PRE T0 e la stratigrafia a due layer;
- la pressione litostatica `g*(rho_crust * min(z, Moho) + rho_mantle * max(0,z-Moho))`, con g **obbligatoriamente scelto** e non attribuito al canone;
- la pressione normale efficace `sigma_n_eff=(normal_over_P_lith - Biot*pore_fraction)*P_lith`;
- la formula di frizione Byerlee come **riferimento sperimentale** in due rami continui: `tau=0.85*sigma_n_eff` sino a 200 MPa e `tau=50 MPa+0.60*sigma_n_eff` sopra; nessuna assegnazione automatica come reologia ARCANA;
- una legge duttile ad esponente generico con A, n, E, V e, se richiesto, `f_H2O^r` NORMALIZZATA esplicitamente al riferimento, usando la scala di stress ASPECT; la conversione a una grandezza confrontabile con la resistenza fragile deve avere una convenzione dichiarata;
- l'inviluppo fra fragile/duttile per la crosta; per il mantello è disponibile anche la variante duttile pura, ma solo come ipotesi esplicita motivata;
- integrazione numerica sull'intera crosta e mantello a due risoluzioni, con tolleranza specificata dall'esperimento, ritorno in **Pa·m=N/m** e arresto in caso di extrapolazione T/P/strain rate o fugacità mancante.

Non si stima una deformazione dalla sola apertura Euler. Il programma rifiuta parametri incompleti e NON produce dati ShellSet LR da una corrispondenza non verificata di invarianti di stress.

`g2_candidate_runner.py` verifica gli SHA del pacchetto FAIR G2/G3 A e unisce le 25 colonne agli ID dei parent. Un risultato numerico di scenario rimane SEMPRE **`ENGINEERING_CANDIDATE_NOT_AUTHOR_RATIFIED`** e non autorizza alcun solve o T1.

## FAIR — solo test del motore; nessuna legge ARCANA assegnata

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# Se pulito:
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
python -m pytest -q tests/test_r6_g2_whole_column_provider.py
```

I test sono sintetici e includono un caso chiuso analiticamente, validità del dominio, Biot/pressione, l'assenza di fugacità, il divieto di promozione canonica e la lettura 25 colonne in un fixture artificiale. **Non** rilanciare qui `g2_candidate_runner.py` sulle PRE reali con parametri fittizi: il template `G2_EXPLICIT_CANDIDATE_TEMPLATE.json` lascia `null` tutti gli input ancora privi di autorità, volontariamente.

## Riferimenti e limiti

- Byerlee, J. D., **Friction of rocks** (1978): https://landslides.usgs.gov/static/lfs/research/rockphysics/Friction_of_rocks.pdf
- Buiter et al., **101 geodynamic modelling...** (2022): https://se.copernicus.org/articles/13/583/2022/
- ASPECT, material model diffusion/dislocation creep conventions: https://aspect-documentation.readthedocs.io/en/latest/parameters/Material_20model.html
- R6 source benchmark G2, G3 A and PRE: `rheology_envelope.py`, `wet_quartz_screen.py`, `coupling_A.py`.

L'uso della legge Byerlee richiede un'ipotesi di piano di scorrimento e stress normale, non nota dal solo PRE; l'ASPECT stress scale non è la stessa convenzione della tensione di taglio fragile se manca la conversione esplicita. Il criterio di validità originale va studiato caso per caso, e `valid_*=[...]` va popolato solo da fonti autentiche, non allargato per forzare il calcolo. Il metodo di calcolo è pronto, **ma la reologia G2 del mondo non è ancora scelta**.

## Passaggio per G3 A

Una volta individuate almeno due famiglie materiali **scientificamente applicabili** all'intera colonna (un riferimento e una alternativa water-sensitive), e verificato l'errore di stress integrato, si potrà convertire la risposta nella legge **effettiva del solver reale SHELLS**, costruire K e f del continuo esterno, verificare bilancio della GPE/sostegno basale e il transfer meccanico N/S. La ratifica G3 A NON autorizza automaticamente valori materiali, condizioni esterne, un solve ShellSet o un T1.
