# ARCANA R6 — G2/G3 fisica-first: integrazione idrostatica e GPE sorgente

**19 novembre 2026.** La decisione dell'autore è di *procedere alla chiusura della fisica G2/G3*, **non** di ratificare ex ante parametri idrologici, geologici o condizioni ai bordi ancora sconosciuti. Il contesto è EXPLORE non canonico; D-024 vieta ancora il solve fisico e il T1.

## Evidenza FAIR entrante

Commit `239f9d1a04e79fb816110306de5ba50ec26eb25b`. Risultato riferito dall'operatore:
```text
tests/test_r6_g3_force_budget.py: 9 passed in 0.13s
PASS_G3_A_FORCE_SOURCE_INVENTORY__LOAD_PHYSICS_UNRESOLVED
8x8: 32 bordi, 120 triangoli basali esterni, placche [5,8], 0 giunzioni triple
16x16: 64 bordi, 504 triangoli basali esterni, placche [5,8,11], 1 giunzione tripla
mechanical_solve_authorized=false, solver_runs=0, physical_T1=null
```
Evidenza raw sul server FAIR: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_FORCE_REQUIREMENTS_NEW_01`; qui non importata. La fisica delle trazioni NON era presente nell'output.

## Cosa è stato aggiunto: un vero termine gravitazionale candidato, non un altro inventario nullo

`g3_gpe_hydrostatic.py` calcola da campi PRE (densità e spessore di crosta/mantello, densità dell'astenosfera e dell'acqua) e elevazione FEG:
- la **pressione normale idrostatica richiesta** sulla superficie di riferimento comune;
- il **momento di pressione / energia potenziale gravitazionale per unità di area** della colonna fino alla superficie, includendo eventuale acqua marina;
- il **gradiente tangenziale GPE** discretizzato sui triangoli originali con formula P1 della superficie a faccette, proiettato sulle DOF East/North e sommato per ID nodo sorgente;
- variazione min/max e dispersione relativa della pressione basale, per evidenziare colonne NON isostaticamente bilanciate anziché inventare la reazione di base.

Per superficie con elevazione `h` (positiva in alto), spessori `c,m`, base `b=h-c-m` e riferimento `z_ref<b`, si integra la massa degli intervalli crosta `[h-c,h]`, mantello `[b,h-c]`, astenosfera `[z_ref,b]`; se `h<0` si integra l'acqua tra `h` e `0`. In simboli:

```text
W = g [rho_c*c + rho_m*m + rho_ast*(b-z_ref) + rho_water*max(-h,0)]  [Pa]
U = integral_{z_ref}^{max(h,0)} rho(z)*g*(z-z_ref) dz                [J/m2]
F_GPE,e(i) = -(A_e/3) * projection_E/N_i(grad_facet(U))              [N]
```
**Attenzione:** `U` è un integrale fino a un riferimento scelto. La scelta `z_ref=-200 km`, `g=9.80665 m/s²` è un **esperimento Earth-analogue esplicito**, NON una costante geologica ratificata per ARCANA. `g` corrisponde al benchmark numerico R6 già documentato. Il valore di riferimento della pressione normale, necessario per un effettivo bilancio isostatico, resta **null** e non viene autofittato.

**Motivazione scientifica:** nelle formulazioni thin-shell le differenze del momento di pressione/GPE generano forzanti orizzontali, mentre il bilancio verticale e la base devono rispettare isostasia e pressione dinamica. Modelli alternativi del GPE possono richiedere topografia dinamica e livello di compensazione diversi. Fonti: Bird et al. 2008 DOI `10.1029/2007JB005460`, Flesch et al. 2007 DOI `10.1111/j.1365-246X.2007.03274.x`, Neres et al. 2018 DOI `10.1029/2017JB015002`, e Bird 1999 DOI `10.1016/S0098-3004(98)00142-3`. Cfr. https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2007jb005460 e https://agupubs.onlinelibrary.wiley.com/doi/full/10.1029/2017JB015002 .

### Sicurezze e limiti

Il dato FEG contiene effettivamente `elevation_m`, ma la **provenienza fisico-geologica di quel valore va ancora qualificata**. Un campo numericamente presente non è automaticamente topografia storica T0. La densità `rho_asthenosphere` proviene dal PRE; la componente `chemical_density_anomaly_kg_m3` nel FEG richiede un confronto esplicito per evitare doppie interpretazioni prima di dichiarare parità con SHELLS.

Il modulo rifiuta piani di compensazione che intersecano il fondo della litosfera, righe PRE mancanti, hash sorgente difformi e duplicazioni di nodi. I risultati reali del **test GPE Earth-analogue** sono *candidate_GPE_force_vector_N*, non `physical_force_vector`.

Questo GPE esterno non deve MAI essere sommato alla pressione/GPE già computata dalle routine `Squeez` e `Fixed` di SHELLS; la parità fra le due formulazioni e l'esclusione dei duplicati non sono ancora dimostrate. I test sintetici verificano anche che `U` uniforme produca ESATTAMENTE forza nulla: si sottrae `U_0` prima della derivata per evitare forze spurie per arrotondamento di energia assoluta ~10^15 J/m².

## Stato G2: perché non possiamo attribuire un'unica curva alla crosta

Dal precedente test T0: `T_crust=280..1051.558 K`. La legge GT95 con `n~4` si basa su misure ad alte temperature `1173.15..1373.15 K` e campioni con acqua ~0.15 wt%. Una conversione del coefficiente creep, il valore di fugacità dell'acqua nel mondo, l'estensione alla crosta fredda e una pressione dei pori valida **non esistono ancora** come input scientificamente qualificati. L'uso di olivina secca per il mantello è soltanto il benchmark Earth-analogue R6 (`A=1.1e-16 Pa^-n s^-1, n=3.5, E=530 kJ/mol, V=14e-6 m³/mol`), non prova che il mantello ARCANA sia olivinico o secco. Pubblicazioni: GT95 DOI `10.1016/0040-1951(95)00011-B`; Hirth & Kohlstedt, DOI `10.1029/138GM06`; Brace & Kohlstedt 1980 DOI `10.1029/JB085iB11p06248`; ASPECT https://aspect-documentation.readthedocs.io/en/stable/parameters/Material_20model.html .

**Decisione tecnica G2:** la futura legge deve trattare pressione efficace `P_eff=P_lith-Biot*P_poro`, rottura fragile del continuo (Drucker–Prager oppure un modello esplicito di faglia/frottamento), creep profondo con acqua e domini di validità, e una transizione fra i meccanismi senza usare GT95 a 280K. I coefficienti sono **una scelta scientifico-autoriale**, non un risultato degli audit PRE. L'operatore sperimentale a due esponenti è già verificato FAIR 11/11, ma non equivale ancora a `SHELLS OneBar/Mohr/Diamnd`.

## Esecuzione FAIR non canonica (senza solve)

Il test di algebra e identità va eseguito prima dell'esperimento su profili reali:
```bash
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_PLATE58_VERIFY
git status --short
# Solo se pulito:
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
python -m pytest -q tests/test_r6_g3_gpe_hydrostatic.py

MULTISCALE=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_OUTER_MULTISCALE_NEW_01
MECHANICAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_A_MECHANICAL_INTERFACE_NEW_01
NODAL=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G2_NODAL_SOURCE_BINDING_NEW_01
HYPOTHESIS=experiments/plate58_deforming_explore_v1/G2_G3_EARTH_ANALOGUE_GPE_HYPOTHESIS.json
OUTPUT=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_G3_GPE_HYDROSTATIC_HYPOTHESIS_NEW_01
python -m experiments.plate58_deforming_explore_v1.g3_gpe_hydrostatic "$MULTISCALE" "$MECHANICAL" "$NODAL" "$HYPOTHESIS" "$OUTPUT"
```
Questo comando calcola vere **quantità fisiche candidate sui campi T0**, ma NON invoca SHELLS, non assegna G2 e non produce un T1. Il risultato può essere numerico anche se l'elevazione FEG non è fisicamente qualificata; gli indicatori di autorità rimangono falsi.

## Prossimo hinge, senza microgate

Usare l'energia/pressione risultante per stabilire se il modello presenta uno squilibrio basale fisico che necessita compensazione dinamica, non inventare un carico per annullarlo. Contemporaneamente fissare il modello effettivo fragile/creep/hydration che copra l'intero profilo, e derivare le trazioni laterali/basali dal continuum esterno 5:8:11 e dal campo del mantello inferiore con una sola ownership GPE. Verificare congruenza tensoriale con SHELLS prima di un solve EXPLORE autorizzato, poi solo successivamente valutare T1.
