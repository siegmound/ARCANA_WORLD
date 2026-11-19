# R1 — REDUCED VALIDATE numerica

2026-11-01, Europe/Rome. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.
Radice aperta con identificativo20261031 e conservata senza rinominarla.

`R1_REDUCED_VALIDATE=PASS_NUMERICAL_MANUFACTURED_SCOPE`

**Il solver può iniziare esperimenti fisici circoscritti, dopo l'ammissione degli
input e della loro mappatura.** Questa campagna valida il comportamento numerico
ridotto su condizioni artificiali; non valida la geologia di ARCANA, i dati reali,
un modello accoppiato o una storia planetaria. La vecchia Q1 completa resta distinta.

## Versione unica e perimetro

Congelati prima del lancio il kernel compensato, la costruzione compatta, i driver
e i criteri. Versione SHA256:
`48247787485f611b99efd415b6bcc46e851268a04e92e432eccf6d12de676066`.
Un'unica campagna numerica completa, nessuna correzione al solver e nessun insieme
di risultati provenienti da versioni diverse. Le339identità precedenti
(325storiche+6EXPLORE+8EXPLORE-DT) restano invariate; il contratto congelato include
anche i4nuovi file di campagna. Sorgenti in
`experiments/hr2_p1_reduced_validate_v1`, contratto e snapshot nelle nuove evidenze.

Branch `r6/runtime-copy-r1-fair`, HEAD `2c71370eb9a959c78121ce1c88ec8e9e37187787`,
worktree intenzionalmente non committato preservato.78file pre-esistenti e sorgenti
catturati prima del lavoro; undici archivi precedenti verificati prima/dopo.
Autorizzazione: richiesta utente REDUCED VALIDATE. Nessuna catena di certificati
formali o ratifica intermedia richiesta. No commit/push o modifica agli originali.

Griglie16×8,32×16,128×64,256×128; campi x,y,z,q e
**8+exp(0,5 a·r), a=(1,2,3)/sqrt14**, positivo e non mono-armonico.
R=6371000m, kappa=405896410000m²/anno, T=0,0001anno, tutti artificiali.
45brevi traiettorie principali/rifinite, più controlli e due prove di restart.

## Esiti per area

| Area | Esito | Evidenza principale |
| --- | --- | --- |
| Riferimenti indipendenti | PASS | Quadrature32/48; Legendre e heat-decay separati; riferimento semidiscreto Fourier/full-space |
| Convergenza spaziale | PASS | Tutti i campi e normeL1/L2/Linf: ordine minimo2,7846, contro obiettivo1,5 |
| Precisione temporale | PASS | Tutti i confronti128/256 e256/512 sulla griglia fine sotto5%; ordine0,999966–1,000008 |
| Conservazione/positività/limiter | PASS | Stock rappresentati>=0; limiter attivo su spike/random; invarianti costanti/zero |
| Flussi polari e antimeridiano | PASS | Errori EW/NS, anche prime fasce polari, decrescenti; attraversamento non nullo di y ed esponenziale |
| Restart e identità | PASS |32×16 e256×128: stato completo bit-identico; corruzione e source/geometry errate rifiutate |
| Prestazioni complete | PASS | Tempo/CPU/RSS dell'intero processo e costo effettivo della matrice registrati |

Ordini calcolati con il rapporto reale delle risoluzioni: il salto32→128 non è
trattato come un raddoppio. La64×32 non fa parte di questa campagna ridotta.

## Errori sulla256×128

L2 in metri, stato fine256passi. La frazione mantiene esattamente la definizione
precedente: L2(h128−h256)/L2(h128−riferimento continuo), pesata per area.

| Campo | L2 continuo m | Main128/half256 | L2 temporale vs semidiscreto m |
| --- | ---: | ---: | ---: |
| x | 1.039322e-13 | 4.473904% | 4.510377e-15 |
| y | 1.039292e-13 | 4.474045% | 4.510370e-15 |
| z | 1.317028e-13 | 3.487621% | 4.510291e-15 |
| q | 2.879275e-12 | 0.731674% | 2.095976e-14 |
| exp_rotated | 3.854575e-13 | 0.951746% | 3.645659e-15 |

Il confronto256/512 migliora ulteriormente: circa2,17%x/y,1,71%z,0,364%q,
0,473%esponenziale. Nessuna soglia adattata. Il limiter rimane inattivo nei campi
lisci, permettendo la separazione numerica tra errore spaziale e temporale.

Il riferimento esponenziale integra separatamente vere medie di area; la sua
propagazione continua usa Legendre fino al grado16 con decadimento l(l+1).
Il resto della serie esponenziale è stimato prima dell'esecuzione e non viene
adattato ai risultati. Differenza massima osservata fra quadrature32/48:
1,90e-16m. Il riferimento temporale usa tutti i modi longitudinali della stessa
matrice spaziale e somme estese, con confronto full-space sulle griglie piccole
entro8,67e-19m. Sono controlli numerici indipendenti, non certificati d'intervallo.

I controlli spike/random eseguono16passi a CFL, con attivazione reale del limiter.
Il massimo residuo relativo totale di volume osservato è1,28e-18; ogni passo
rispetta il budget8gamma esistente. Nessun clipping degli stock o rinormalizzazione.
Il principio del massimo è controllato con la tolleranza floating del kernel,
non dichiarato esatto in aritmetica reale. Sono conservati flussi, array e norme
per esclusione delle fasce polari.45riduzioni indipendenti degli stati salvati
riproducono esattamente i rispettivi L2 registrati.

## Riproducibilità e costo

Su32×16 e256×128,16passi diretti coincidono con8+restore+8 sia nello stesso
processo sia in un figlio separato, bit per bit in **hi e correction**.
Rifiutati checkpoint corrotto, geometria errata, sorgente errata anche con SHA
esterno ricalcolato e contratto di versione errato. Il checkpoint fine occupa
525390B e richiede il cache geometrico esterno autenticato. Non è una qualifica
journal/B0/CAS, crash-SIGKILL o reader generale per input ostili.

Misura esterna dell'intera esecuzione: **104,85s wall**, **103,67s CPU user +
1,14s system**, piccoRSS **495888KiB =484,27MiB**. Include costruzione fresca,
riferimenti, tutte le traiettorie, serializzazione e attese dei restart; non è
il solo kernel. RSS è il massimo per processo riportato dalla misura esterna,
non una somma della memoria simultanea di tutti i processi. Il risultato interno
pre-ricevuta misura104,648s; gli ambiti si sovrappongono e non vanno sommati.

La matrice256×128 ha5816832coefficienti e70063108B (**66,817MiB**); costruzione
fresca completa **5,421s**, identica byte per byte alla matrice archiviata.
CFL polare invariato: **2,2674130355e-6anno**. Nessuna estrapolazione a tempi lunghi.
BLAS/OMP/MKL a un thread; carico della sessione non controllato.

## Decisione e limiti

**PASS numerico ridotto: procedere alla prossima integrazione fisica sperimentale
breve.** Prima di usare dati reali occorrono identità, unità, copertura/UNKNOWN,
parametri fisici dichiarati e una mappatura conservativa sulle celle. Una quota
altimetrica non diventa automaticamente spessore di copertura; densità e diffusività
mancanti non vengono inventate. Questi sono requisiti degli input, non una richiesta
di nuovi certificati formali sui momenti. Nessun esperimento fisico reale viene
avviato automaticamente da questa chiusura.

Restano fuori: stabilità generale su qualsiasi forcing, calibrazione geologica,
accoppiamenti idrologici/termici/Deep, recupero B0 completo e simulazioni storiche
1000Y/10k/100k. Compensazione e cache devono restare nello stato di restart.
Nessuna dichiarazione di vecchia Q1 completa o autorità scientifica/produttiva.

Evidenze: `ARCANA_WORLD_EVIDENCE/R6/R1_REDUCED_VALIDATE_20261031_01`:
FROZEN_VERSION, campaign_v1/RESULT, ERRORS_AND_COSTS, SPATIAL_ORDERS,
POLAR_AND_SEAM_FLUX, ARRAY_CATALOG, SAVED_STATE_AUDIT e REDUCED_VALIDATE.png.
Il primo catalogatore offline si è fermato sul checkpoint deliberatamente corrotto;
la versione2 lo conserva per hash senza decodificarlo. Nessun rilancio numerico
o modifica alla versione congelata: tutti gli esiti sopra provengono dalla sola
campaign_v1. Manifest e finalizzazione sigillano anche questo dettaglio.
