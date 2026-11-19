# Primo esperimento termico verticale 1D — EXPLORE

2026-11-02, Europe/Rome.

`THERMAL_1D_EXPLORE=PASS_SHORT_AUTHORIAL_T0_WITH_ISOLATED_INTERFACE_FIX`

Eseguite due colonne originali C028/C029 per **10 anni**, senza deformazione o
accoppiamento laterale. Il risultato è un esperimento fisicamente motivato di
conduzione/radiogenesi sui dati autoriali ARCANA, non una ricostruzione osservativa
né una validazione geologica. R1 non è importato o modificato; il suo
`R1_REDUCED_VALIDATE=PASS_NUMERICAL_MANUFACTURED_SCOPE` resta invariato. Il precedente
blocco sulla copertura mobile resta valido nel suo ambito.

## Input e condizioni determinate

Provider originale: `src/arcana_worldsim/r6/functional_development.py`,
`evolve_fixed_geometry_thermal_profile` e `_explicit_thermal_update`.
Legge: rho Cp dT/dt = d/dz(k dT/dz) + A; profondità positiva verso il basso.
Nessun moto imposto, densità/capacità/conducibilità costanti per materiale.
Le temperature iniziali e i materiali sono letti dal caso `UNCoupled_reference`,
`state_initial` dell'E0 originale, non dagli stati finali deformati.

PRE_ORBDATA contiene due record esattamente owner-bound R091/C028 e C029:
nodi32792/32793. I loro polinomi riproducono i73 campioni E0 entro2,274e-13K.
Questa è una corrispondenza di profilo/supporto, non un peso areale FEG.
Le due colonne hanno gli stessi dati termici: non sono due contesti fisici distinti.
Epoca T0 nominale210Ma; i10anni sono tempo di modello da T0.

| Grandezza | Valore esistente e significato |
| --- | --- |
| Profondità |0–80000m; Moho28000m;73nodi originali, senza rimappatura |
| Bordi | Superficie280K; base1671,771417700828K, mantenuti fissi secondo il provider |
| Crosta | k2,5W/(m K), rho2800kg/m³, Cp1000J/(kg K), A8e-7W/m³ |
| Mantello | k3,3W/(m K), rho3300kg/m³, Cp1200J/(kg K), A2e-8W/m³ |
| Flusso iniziale | Superficie0,085W/m²; Moho0,0527782494341273W/m² |
| Produzione integrata |0,02344W/m² sull'intera colonna |

Materiali e radiogenesi sono riferimenti autoriali con prior/range nei contratti
PRE_ORBDATA, non misure locali o valori calibrati in questo esperimento. I bordi
sono condizioni del modello già previste dal provider. Il flusso superficiale è
un dato iniziale, **non** un secondo bordo Neumann imposto insieme al Dirichlet.
La base è lo spessore termico autoriale del modello, non un LAB osservato. Non si
impone la vecchia velocità di estensione né una storia di placche non determinata.
I flag di presenza PRE_ORBDATA sono conservati nei record originali; nessun valore
mancante viene trasformato in zero. Non sono necessari nuovi parametri per questo
scenario specifico a geometria/bordi fissi.

## Difetto concreto e correzione isolata

Il provider originale assegna materiale crostale al nodo Moho e all'intero suo
volume duale, anche per la parte sotto il contatto. L'arco Moho→primo nodo mantello
usa inoltre una resistenza metà crosta/metà mantello, benché sia tutto mantello.
L'effetto iniziale è misurato: tendenza Moho−7,30537e-5K/anno contro il valore
continuo PRE−3,95345505e-6K/anno. Non è un diverso forcing fisico.

Nuovo codice isolato `experiments/thermal_1d_explore_v1/run.py`: integra C_i =
int(rho Cp dz), S_i = int(A dz) sui volumi duali, e g_f = 1/int(dz/k) sugli archi
rispettando il contatto originale a28km. Q_f=g_f(T_destra−T_sinistra) è positivo
verso l'alto; un solo Q viene usato con segni opposti. Aggiornamento Euler esplicito
solo dei nodi interni. Nessun clipping, rinormalizzazione o modifica ai sorgenti
originali. Le due metà del volume Moho condividono una sola temperatura nodale.
La resistenza dell'arco sotto il Moho è quindi dz/k_mantello.

È un nuovo adattatore sperimentale, non una correzione pubblicata del provider.
La baseline originale è realmente eseguita e coincide bit per bit con la funzione
pubblica originale. La nuova tendenza iniziale in tutti i nodi interni concorda
con il rate PRE entro3,313e-25K/s. La continuità del flusso esatto al contatto è
verificata indipendentemente tramite i due polinomi; i flussi sulle due facce
adiacenti non devono essere uguali, essendoci produzione e accumulo tra di esse.

## Risultati numerici reali

Dodici brevi traiettorie:2colonne×2metodi×16/32/64passi sullo stesso intervallo;
più due controlli della funzione pubblica. Parametri e dati iniziali invariati.
Riferimento indipendente nel tempo: assemblaggio separato dell'ODE affine e
`scipy.linalg.expm` su incrementi. È un riferimento semidiscreto standard, non un
oracolo continuo dello spazio. Il controllo indipendente dei polinomi PRE verifica
in aggiunta profilo, flusso Moho, produzione e tendenza iniziale fisica.

| Misura,64passi | Provider originale | Adattatore d'interfaccia |
| --- | ---: | ---: |
| Variazione massima temperatura K |7,303059e-4 |3,953456e-5 |
| RMS rispetto a esponenziale stesso metodo K |5,65138e-10 |1,19731e-11 |
| Produzione intera colonna W/m² |0,0238625 |0,02344 |
| Min/max finale K |280 /1671,771418 |280 /1671,771418 |
| Max residuo energetico/passo J/m² |0,01564 |0,01635 |

Dati identici per entrambe le colonne. Il rate PRE suggerisce inizialmente un
raffreddamento uniforme di−3,953455e-5K in10anni: la differenza interna finale
massima è4,359e-9K, dovuta anche ai bordi fissati, non a un forcing nuovo. Questo
sviluppo lineare è un controllo di breve tempo, non una soluzione esatta a tutti
i tempi con Dirichlet fissi. Gli ordini temporali baseline sono1,00006/0,99994;
nuovo adattatore0,99823/0,88277, con errore ultimo vicino all'arrotondamento. Non si
rivendica un ordine asintotico da quest'ultimo rapporto né una convergenza spaziale.

CFL monotono C_i/(g_sopra+g_sotto):7,041667e11s nell'adattatore,6,605364e11s
nel provider. dt ultimo4,930875e6s, rapporto7,0024e-6; tutti i passi sono molto
entro il limite, temperature positive e finite. Questo non è uno stress-test di
stabilità vicino al CFL.

Bilancio E = sum_interni(C_i T_i) per unità di superficie: deltaE = dt ×
(Q_base_interna−Q_top_interna+sum_interni S_i). Per l'adattatore64passi il saldo
integrato è−11091056,817J/m²; residuo cumulativo−1,01149J/m², circa9,12e-8 del
saldo. Il residuo per passo rispetta il budget d'arrotondamento proporzionale agli
stock (circa1,20J/m²), senza correzioni. La radiogenesi intera colonna in10anni
è7397101,44J/m². **Il ledger evolve solo i volumi interni:** i mezzi volumi ai
nodi Dirichlet sono serbatoi vincolati, esclusi dall'energia evoluta e dalla sua
produzione. Perciò la produzione interna è0,0229625W/m², diversa da quella totale.
I flussi del ledger sono sulle facce interne dei serbatoi, non spacciati per flussi
continui esatti alla superficie fisica. Un modello con serbatoi evolutivi richiede
un diverso bilancio esplicito; qui il sistema è termicamente aperto.

## Costo, iterazioni e conservazione

Campagna finale:0,37s wall esterno, CPU0,33s user+0,03s system, piccoRSS57080KiB
(55,74MiB). Include import, lettura DAT, tutti gli avanzamenti, expm e output.
Wall interno0,18735s, sovrapposto al totale; nessuna somma tra questi ambiti.
BLAS/OMP/MKL a1thread; nessuna installazione o vincolo artificiale RAM.
Array NPZ conservano traiettorie, flussi di ogni passo, riferimenti, capacità,
sorgenti e residui. Hash, input e versione sono nel manifest.

Primo tentativo conservato: stop sul controllo assoluto0,02J/m², residuo0,02159
contro scala di arrotondamento eps×stock≈0,0758J/m². La versione finale sostituisce
questo controllo diagnostico con8eps×sum(C_i(|T0_i|+|Tfine_i|)); nessuna modifica
alla legge, ai parametri o ai passi. Cambia anche il metadato non utilizzato del
flusso iniziale da placeholder0 a derivata quadratica T0. Il primo codice/output/
exit sono conservati. Tutti i risultati sopra sono della sola versione finale.
Nessuna soglia precedente Q1/R1 è coinvolta o modificata.

## Decisione e prossimo passo

**Esperimento termico fisico di modello riuscito nel breve perimetro dichiarato.**
Il nuovo adattatore elimina il difetto d'interfaccia osservato senza cambiare
materiali o sorgenti. Prossimo passo utile: piccoli confronti di raffinamento
verticale con integrazione esatta dei materiali, flussi ai bordi e sensitività dei
parametri già dichiarati; poi eventuale integrazione con cronologia/checkpoint.
Non si autorizzano automaticamente né nuove storie fisiche né accoppiamenti.
Non è qualificata la termica globale, la convezione, la deformazione, la petrologia
reale o un modello laterale equivalente. Nessuna simulazione1000Y/10k/100k,
commit/push, modifica R1/provider o promozione scientifica.

Evidenze: `ARCANA_WORLD_EVIDENCE/R6/THERMAL_1D_EXPLORE_20261102_01`.
Prima/dopo verificati343pin validati, tutti i sorgenti del package e i21input già
autenticati. Report, codice, tentativo fallito e campagna finale sono sigillati
separatamente; gli archivi precedenti restano invariati.
