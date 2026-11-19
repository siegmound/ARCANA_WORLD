# ARCANA R6 — Contatto 5:8: FAIR G3 PASS e incompatibilità ai nodi di uscita

**Data:** 2026-11-19. **Stato:** diagnostica FAIR confermata dall'operatore; nuovo audit statico di compatibilità non ancora eseguito su FAIR. **D-024 invariata.**

## Evidenza già ottenuta

Nel checkout FAIR isolato `ARCANA_WORLD_R6_PLATE58_VERIFY`, l'operatore ha riportato:
- `tests/test_r6_plate58_envelope.py`: **9/9 PASS**;
- `envelope`: `PASS_16_CELL_G3_SOURCE_DIAGNOSTIC__NS_BASAL_UNRESOLVED`;
- `check_envelope`: `PASS_G3_NEIGHBOR_DIAGNOSTIC__SOLVE_BLOCKED`;
- dominio 16 parent / 25 nodi / 32 triangoli / 6 segmenti contatto fonte T0;
- lato N: `[8,5,5,5]`; lato S: `[8,8,8,5]`;
- nessun solve e nessun T1.

Questi sono **risultati del terminale FAIR riportati dall'operatore**. I relativi membri dell'evidenza esterna non sono stati importati né verificati bit-per-bit su GitHub. Il rapporto precedente e i suoi source SHA restano intatti.

## Decisione G3: non imporre due campi Euler allo stesso nodo

Il dominio FEG usa **nodi condivisi**. Il contatto 5:8 attraversa i tagli nord e sud; nel punto di uscita i segmenti contigui del bordo appartengono rispettivamente alle placche 8 e 5. La velocità Euler sorgente per ciascuna placca è nota, ma non è una condizione sul continuo deformante.

Se entrambe le velocità sono diverse, prescriverle sullo **stesso DOF tangenziale** è matematicamente incompatibile. Non è consentito risolvere la contraddizione duplicando implicitamente il nodo, mediando i due campi, assegnando a caso un proprietario, o convertendo silenziosamente un bordo in `free`, `zero`, `periodic` o `fixed`. Una discontinuità richiederebbe una legge di interfaccia e un nuovo binding fisico. Un continuo unico richiede una condizione esterna esplicita che determini il campo compatibile.

Il modulo **read-only** `boundary_junctions.py` misura, sui nodi di uscita autentici, i due campi Euler sorgente trasformati in coordinate SHELLS e il loro salto (m/s e m/anno). **Non** prepara VBC, trazioni, file solve, effetti termici o T1. `1e-10 m/anno` è una semplice soglia di indistinguibilità numerica, non un criterio di validità geologica.

## Contratto per la prima chiusura fisica G2/G3

| Tema | Decisione necessaria | Invarianti |
| --- | --- | --- |
| G2 leggi costitutive | confrontare quarzite proxy e legge con acqua/fugacità, mantello olivina, fit SHELLS con esponente comune | non equiparare differenza di fit del 3.1% a incertezza reale; stress nominali FAIR 405/98 MPa a 10 km **prima** del limite fragile, non parametri validati |
| G2 fragile e pressione | pressione porale, Biot, attrito, limiti `dCreep`/`visMax`, range P–T–tasso e unità | se ignoti, restano null |
| G3 N/S | provider di trazioni e continuazione esterna, oppure geometria fisica ampliata e BC chiuse | non doppia Dirichlet su un nodo comune; il campo Euler è solo osservazione cinematica |
| G3 banda/time | larghezza fisica, risoluzione e convergenza, finestra di validità | 100 km resta EXPLORE; griglia ~1° non risolve una zona per definizione |
| G3 base | sostegno normale coerente con il peso/GPE; legge tangenziale/drag e frame mantellare, o disaccoppiamento esplicito | free-slip tangenziale da sola non definisce la forza normale |

**Stato:** `G3_TOPOLOGICAL_JUNCTION_CONSTRAINT=IDENTIFIED`; `G2_G3_PHYSICAL_CLOSURE=PARTIAL__AUTHORIAL_INPUTS_PENDING`; `PHYSICAL_DEFORMING_T1=BLOCKED`.

## Unica prossima verifica FAIR (non un nuovo stage di evidenza)

Dal checkout isolato pulito, dopo `git fetch` e `git switch --detach FETCH_HEAD`:

```bash
python -m pytest -q tests/test_r6_plate58_boundary_junctions.py

ENV=/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_NEIGHBOR_16_NEW_01
python -m experiments.plate58_deforming_explore_v1.boundary_junctions "$ENV"
```

Il comando legge il pacchetto FAIR esistente e riporta i due salti senza creare directory o modificare le evidenze. Se lo SHA o i proprietari non coincidono: STOP. **Non ripetere i test già PASS, non eseguire ShellSet.** Dopo questo controllo, il prossimo lavoro sostanziale è la **selezione documentata di un modello G2/G3 fisicamente chiuso**, non altri smoke di preparazione.
