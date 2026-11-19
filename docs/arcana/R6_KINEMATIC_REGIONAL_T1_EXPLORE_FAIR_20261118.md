# ARCANA R6 — Primo T1 cinematico regionale

2026-11-18, Europe/Rome. FAIR_WORKTREE + FAIR_EXTERNAL_EVIDENCE.

**`KINEMATIC_REGIONAL_T1=PASS_PRESCRIBED_KINEMATIC_ONLY`.** Pubblicati due stati
nell'archivio R6 sperimentale, ai tempi 0 e 10 anni del modello. L'età
nominale passa da 210 a 209,999990 Ma. Il risultato riguarda nove nodi FEG e
otto triangoli interni alla placca 5. `PHYSICAL_DEFORMING_T1=BLOCKED_EXACT_G2_G3_INPUTS`.

## Autorità temporale e spaziale

D-024 sostiene il riuso progressivo dei sottosistemi disponibili. La legge
`R6_RIFT_INITIATION_AND_EVENT_GUARD_LAW_BINDING.json` prescrive tassi Euler T0
costanti entro il primo segmento. B6I abilita una sola classe di evento,
l'attivazione di rift. Il primo limite qualificato è a 27.123,405156307464 anni
(coppia 1:3, esterna al ritaglio), con orizzonte aperto. La transizione di
topologia eredita tale evento. Gli eventi non-rift indipendenti sono fuori
dal modello di primo segmento. B6J conferma il limite e l'ammissibilità
di fermarsi prima. Sono stati scelti 10 anni per questa prova regionale, ben
dentro la finestra. Nessun evento di modello cade nella prova e il forcing
oltre l'orizzonte resta senza autorità. B6K aveva già materializzato un
candidato isolato all'orizzonte, con diverso supporto e diversa semantica.

Il ritaglio riusa la CASE sigillata, i parent FEG e i campi originali PRE.
I quattro supporti di riferimento sono R092C030–031 e R093C030–031, con
49.388.202.999,59 m² di superficie triangolata T0. Riletti e verificati gli
SHA dei membri regionali, degli input parent, di B6I/B6J, della geografia
T0 e della partizione. La proiezione PRE e il vettore canonico condividono
le identità della realizzazione T0, della partizione e della cinematica.
Lo SHA del payload cinematico è
`50878031eb67ac699fe29ecc5d3ad7bc7851d653f3b73116376caba29725dcf4`.
Il gauge è il no-net-rotation cinematico del modello autoriale; nessun
riferimento dinamico al mantello viene derivato da quel gauge.
Il confronto con la FEG serializzata verifica `RX_PLUS_0P5_DEG` a
2,22e-16 in XYZ unitario. La rotazione avviene in coordinate canoniche.

## Misure

Usata la rotazione finita a quaternione già presente in R6, con
ω₅ = (−7,341339949e-9, −1,108568762e-8, +1,883467935e-8) rad/anno.
Un controllo indipendente in forma di Rodrigues verifica verso e angolo
(2,305499704e-7 rad), con scarto XYZ di 1,11e-16. Nessuno strain dello smoke
è utilizzato. Temperatura e proprietà PRE restano riferimenti passivi T0.
Il campo trasportato è la geometria delle posizioni e dei supporti materiali;
non si aggiornano contatti, termica, stress, erosione o risorse.

| Controllo | Risultato |
| --- | ---: |
| Spostamento geodetico nodale, minimo–massimo | 1,195955–1,232114 m |
| Variazione massima delle 36 distanze geodetiche | 8,15e-10 m |
| Variazione massima relativa di area per triangolo | 2,05e-14 |
| Orientamento dei triangoli | invariato per tutti gli 8 |
| Spessori, densità, codici materiali, ID e connettività | identici |
| Simmetrico di ∇v, ambiente / proiezione tangente max | 0 / 1,91e-24 anno⁻¹ |
| Scarto XYZ di ripresa 5+5 anni rispetto al passo diretto | 1,11e-16 |

Analiticamente la rotazione ha Jacobiano unitario e ∇v è antisimmetrico.
Il bilancio numerico di massa usa un riferimento esplicito: settori tra
sfere concentriche con spessori e densità PRE, quadratura nodale sui triangoli.
La crosta dà 3,8550e18 kg, con differenza relativa T0→T1 di 5,31e-15; il
mantello litosferico dà 8,3320e18 kg e 5,28e-15. Sono masse di riferimento
sul supporto sferico, senza ricostruzione volumetrica del rilievo o nuova
stima delle masse reali.

## Stato, ripresa e costo

Il nuovo `HistoryStore` in `campaign/history` conserva `ForcingRecord`,
provenienza, due stati, due snapshot e due checkpoint. T1 punta allo stato
T0 e conserva frame, geometria, spessori e PRE per nodo, parent, clock,
forzante, SHA e finestra temporale. I parent identificano il supporto di
provenienza T0; le posizioni mosse sono nel payload. L'archivio non
riassegna celle geografiche. Il ramo di controllo `restart_history` contiene
il checkpoint al quinto anno. Un processo nuovo lo ha riletto e avanzato
di altri cinque anni con lo stesso forcing. Il payload non geometrico è
identico. Cambiare la suddivisione cambia l'arrotondamento delle coordinate;
il replay T0→T1 con la stessa suddivisione riproduce il payload esattamente.

Riletti indice temporale, forcing, parent, identificativi e supporti. I quattro
controlli respingono passo nullo, superamento della finestra sperimentale,
endpoint aperto raggiunto e clock incompatibile. Costo dell'intera prova:
0,70 s wall, 0,47 s CPU user + 0,06 s system, RSS 40 MiB, ripresa figlio
inclusa (0,127 s wall). Il primo tentativo si è fermato prima del calcolo:
la verifica dell'inventario assumeva plate ID 1–12; la fonte usa 0–11.
Corretto il controllo, senza cambiare input, legge o durata. Il tentativo
e i pin ricontrollati sono conservati con le misure finali.

## Decisioni ancora necessarie per ShellSet

- **G2:** associare ai ruoli PRE crosta/mantello litologie, stato d'acqua
  e legge fragile/viscosa. Le alternative di laboratorio della scheda
  precedente (quarzite sperimentale oppure quarzite con fugacità esplicita,
  con riferimento di mantello olivinico) restano riferimenti. Serve un fit
  motivato nelle condizioni P–T del dominio, con conversione degli invarianti
  tensionali, rate in s⁻¹ e unità coerenti con Diamnd. L'interfaccia usa
  `eCreep=1/n` comune; i nominali n=4 e n=3,5 richiedono un esponente
  comune rifittato con errore valutato oppure una variante isolata del
  modello con esponenti separati. Determinare attivazione T/P, acqua o
  fugacità, transizione a creep lineare e pressione efficace/attrito.
- **G3:** assegnare velocità relative o trazioni laterali da un contatto
  reale o uno stato esterno supportato. Determinare la condizione basale
  (per esempio uno scorrimento giustificato o una legge di drag con
  accoppiamento e frame noti) e vincolare i modi rigidi compatibilmente
  con quei dati. Su questo ritaglio l'unico forcing cinematico disponibile
  è il moto comune, a strain nullo. Un'eventuale forzante interna da
  gradienti di energia potenziale gravitazionale richiede un calcolo e
  un bilancio col contorno; la sola variazione del rilievo PRE non li
  stabilisce. Il passo minimo è assegnare una reologia compatibile e una
  forzante differenziale con supporto, bordo e riferimento dichiarati.

Evidenza esclusiva `ARCANA_WORLD_EVIDENCE/R6/KINEMATIC_REGIONAL_T1_20261118_01`.
`RESULT.json` collega gli ID R6; `T1_GEOMETRY.json` conserva i nove nodi;
`READBACK.json` documenta le verifiche da archivio. Nessun nuovo solve ShellSet,
evoluzione globale, mutazione canonica o commit/push.
