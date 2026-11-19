# ARCANA R6 — Primo modello fisico matematico G2 fragile–duttile

Prosecuzione della chiusura fisica EXPLORE (2026-11-19) dopo commit G3-GPE `a76cd5c7d7ce0bab26aa1b1b0afecdd47acce3d3`.

## Formulazione e significato

Il nuovo `g2_viscoplastic_explore.py` è un modello **di continuo viscoso-plastico regolarizzato** (non una legge di faglia) composto da:
1. creep di dislocazione a legge di potenza, con `A,n,E,V`, sorgente/convenzione, intervalli sperimentali P/T/rate e fugacità dell'acqua dichiarati;
2. limite di resistenza del **continuo** di Drucker–Prager 3D, con coesione `C`, angolo d'attrito `φ` e pressione efficace `P_eff=P_lith−Biot*P_poro`, ottenuta da una frazione di pressione dei pori esplicitamente fornita;
3. regolarizzazione morbida/convessa della transizione mediante lo stress armonico `s = s_creep*s_y/(s_creep+s_y)`. **Non** è un return mapping plastico ideale né la legge bilineare di Byerlee su una faglia. È una **ipotesi costitutiva noncanonico-sperimentale** che ha un tensore tangente differenziabile e non richiede di modificare in modo scorretto il vecchio `eCreep` condiviso di SHELLS.

Con invariante tridimensionale incomprimibile `r=sqrt(e.Q.e+eps_floor²)`, creep `s_creep=C(z)*r^(1/n)`, yield DP `s_y`, il potenziale integrato in profondità è:

```text
Phi(e) = integral_z integral_[eps_floor,r(e)] 2*s(r',z) dr' dz
N      = dPhi/de = integral_z 2*s(r,z)/r * (Qe) dz
D      = dN/de   = integral_z [2*s/r*Q
                    + 2*(s' r - s)/r³ * (Qe)(Qe)^T] dz
```

La derivazione si verifica per differenze finite. Il potenziale è integrato numericamente in **log-rate**, non lungo una scala lineare, per evitare un errore di quadratura vicino a eps_floor quando `r/eps_floor` è grande. Test locali con moduli R6 simulati: **7/7 PASS**; l'esatta integrazione nel package repository e test FAIR sono pending.

## Base scientifica e limitazioni

- Forma ASPECT del creep per olivina/quarzo e variabile invariante stress/strain: https://aspect-documentation.readthedocs.io/en/stable/parameters/Material_20model.html
- Drucker–Prager 3D come limite del continuo nei modelli geodinamici: https://aspect.geodynamics.org/doc/doxygen/classaspect_1_1MaterialModel_1_1ViscoPlastic.html
- Byerlee (1978) e Brace & Kohlstedt (1980): legge dello scorrimento ed envelope fragile/duttile, **non identificazione matematica automatica** con un criterio DP di un FEG privo di faglie. DOI 10.1029/JB085iB11p06248.
- GT95 quarzite su 900–1100 °C (~1173–1373K): i veri PRE della crosta 5:8 precedentemente esaminati sono a 280–1051.56 K. Per questo i coefficienti GT95 non possono essere trattati come la legge del continuo completo T0; il test sintetico usa un dominio di validità artificiale chiaramente dichiarato.
- La legge referenziale dry-olivine R6/ASPECT di Hirth–Kohlstedt è un benchmark mineralogico, non un'etichetta già assegnata al mantello ARCANA.
- Senza acqua, P pori e identità delle rocce autentiche, la funzione **non** deve essere invocata per generare l'effettiva risposta materiale T0 5–8–11. Richiede valori espliciti, o rifiuta l'operazione.
- L'output resta `physical_material_G2_authorized=false`, `ShellSet_Diamnd_Mohr_OneBar_parity=false`, `physical_T1=null`.

## FAIR

```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# if clean:
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
python -m pytest -q tests/test_r6_g3_gpe_hydrostatic.py tests/test_r6_g2_viscoplastic_explore.py
```

I controlli rimasti per la **chiusura fisica reale**, senza ulteriore proliferazione di moduli disgiunti, sono: 
- qualificare dalle sorgenti/decisioni d'autore la reologia valida in tutta la crosta fredda e nel mantello, compreso il comportamento dell'acqua e della pressione efficace;
- qualificare la geologia del campo `FEG.elevation_m`, il riferimento idrostatico e l'eventuale pressione dinamica alla base;
- derivare trazione lontana e corrente mantellare (placche 5,8,11) e dimostrare l'assenza di doppio conteggio GPE quando si integra con `Squeez`/`Fixed`;
- testare rank/gauge, conservazione forza/torque/energia, estensione 8x8 e 16x16, seguito solo dopo scelta/approvazione di un solve **EXPLORE limitato**, non di T1 canonico.

Il consenso dell'autore a *procedere con la chiusura della fisica* non autorizza i valori numerici dei fluidi, della falda, la litologia o l'avanzamento T1.
