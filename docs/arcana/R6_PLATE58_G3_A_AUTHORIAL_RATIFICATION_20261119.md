# ARCANA R6 — Ratifica autoriale circoscritta: G3 A, continuo regionale esterno

**2026-11-19.** Decisione esplicita dell'autore: «sì, sono d'accordo» alla domanda
«Vuoi che adottiamo questa architettura A come base sperimentale, mantenendo il
solve bloccato fino alla chiusura fisica completa?».

**Esito:** `RATIFY_EXPERIMENTAL_G3_ARCHITECTURE_A_ONLY`.

## Portata esatta della ratifica

L'autore **approva l'architettura EXPLORE A**, cioè un continuo deformabile
source-bound per il contatto placche 5:8, accoppiato a un **continuo esterno
fisicamente chiuso**. Le condizioni meccaniche nord/sud saranno derivate dal
modello esterno e trasferite in modo compatibile al dominio interno. Il contatto
rimane continuo con nodi FEG condivisi, senza introdurre automaticamente faglie
o discontinuità.

L'approvazione **non** è un'autorizzazione all'uso in simulazione di parametri
G2 ipotetici, non sceglie il profilo idrico, non ratifica la finestra di creep,
non assegna pressione/forza basale, né valida la larghezza 100 km o un `Δt`.
Non autorizza ShellSet, G4 o HistoryStore e non promuove l'architettura a canon.
D-024 rimane invariata.

Resta **solo alternativa di sensitività** il modello B con bordi nord/sud
`free`, e non è l'architettura scelta per un T1 fisico.

## Stato sorgente su cui si innesta

- FAIR screening quarzite umida: **14/14** test, 81 campioni, 18/81 nella
  finestra T sperimentale più ampia, 9/81 nelle intersezioni diagnostiche T–P;
  acqua/fugacità sconosciute, nessuna validazione di legge completa.
- FAIR benchmark G2 precedente: **12/12**, 0/81 nella finestra T GT1995.
- FAIR G3 16-cell **9/9** e compatibilità ai due nodi di uscita **6/6**:
  una singola velocità per ciascun DOF FEG continuo, mai due Euler in conflitto.
- Tutti i risultati provengono dal terminale FAIR riportato dall'operatore;
  gli artefatti esterni non sono stati copiati nel repository.

## Contratto operativo della via A

Il provider del continuo esterno dovrà fornire esplicitamente:

1. **Geometria/provenance:** domini interno ed esterno, ID dei parent,
   discretizzazione e convergenza della scala spaziale. Una raffinazione
   numerica non crea nuove sorgenti geologiche.
2. **Fisica di bordo:** legge costitutiva in comune con G2; condizioni
   meccaniche esterne motivabili, trazioni/reazioni che attraversano
   le sezioni N/S, trasformazioni di frame e segni/ordine dei DOF.
3. **Base:** bilancio verticale/GPE esistente e verifica che un'eventuale
   forza di sostegno non duplichi `Squeez`/`Fixed`; eventuale trascinamento
   mantellare richiede provider di moto e legge di accoppiamento.
4. **Numerica:** rango e gauge, conservazione del lavoro ai bordi,
   equilibrio delle forze, sensibilità all'estensione del dominio
   e convergenza mesh; nessuna velocità contraddittoria a nodi condivisi.
5. **Temporalità e G4:** fascia di validità del forcing, passo meccanico,
   conservazione di massa e risorse per strato, flussi al bordo e
   aggiornamento termico prima di scrivere uno stato storico T1.

L'approvazione riguarda il punto architetturale, non la disponibilità di
questi dati. Il provider fisico è attualmente **mancante**, non viene
sostituito con un `free` o `zero` implicito.

Il JSON della ratifica registra ogni campo ancora assente come `null`:
`experiments/plate58_deforming_explore_v1/G3_A_AUTHORIAL_ARCHITECTURE_RATIFICATION.json`.
La precedente proposta
`PHYSICAL_EXPERIMENT_DECISION_PROPOSAL.json` resta intatta per preservare
la distinzione tra **proposta completa non ratificata** e
**architettura G3 A ratificata**.

## Prossimo lavoro tecnico sostanziale

**G2 e G3 devono essere chiusi in modo integrato**, non con altri smoke
topologici o ulteriori screening T/P:
- identificare la legge efficace che copra *tutta* la crosta, incluse
  le porzioni fredde, con fragile/ductile e una dichiarazione esplicita
  dello stato idrico e dei parametri di pressione efficace;
- confrontare le famiglie costitutive nei limiti documentati, ridurre
  una possibile legge in coefficienti SHELLS e valutarne resistenza
  integrata ed errori, senza fingere che il 4.197% validi la geologia;
- derivare il carico/reazione del **dominio esterno A** e chiudere
  le forze normali/tangenziali alla base, verificando sia l'equilibrio
  sia l'assenza di carichi duplicati;
- solo dopo una **selezione autoriale dei parametri** e un controllo
  d'idoneità si potrà deliberare un singolo solve EXPLORE regionale.

```text
G3_ARCHITECTURE_A=AUTHOR_RATIFIED_EXPLORE_ONLY
G3_EXTERNAL_CONTINUUM_PROVIDER=NOT_YET_AVAILABLE
G2_EFFECTIVE_CONSTITUTIVE_CLOSURE=UNRESOLVED
G3_NS_FORCING=UNRESOLVED
G3_BASAL_NORMAL_SUPPORT=UNRESOLVED
FULL_EXPERIMENT_SCENARIO=NOT_RATIFIED
MECHANICAL_SOLVE_AUTHORIZED=false
PHYSICAL_DEFORMING_T1=BLOCKED
```
