# R6 C06 · Ipotesi materiali regionali e chiusura fisica minima

27 novembre 2026. Sviluppo FAIR/Linux nel worktree dedicato, a partire da
`e37d68092c140455dc97213200097ce5ef407a6a`.
`C06_WINDOWS_ENVIRONMENT_RESTRICTION_REMOVED__IMPLEMENTATION_RESUMED`.
D-024 e D-025 attive.

## Evidenza e replay

La ricevuta C05R registra la trascrizione dell'operatore per lo SHA di
ingresso: import PASS, 223/223 in 1,38 s, exit 0, zero engine aggiuntivi,
manifest `cc854bdd67132471f87c64beeb285550fc3e48b881b40ea69c2396472e058b1a`.
Il campo di provenienza della ricevuta conserva il significato originale.

Il replay di sviluppo in memoria ha verificato l'inventario sigillato,
ricostruito C04 e C05 dalle fonti originali, confrontato ogni gruppo e i
due report C05R e riprodotto entrambi gli ancoraggi di design con lo scarto
documentato di un ULP. Su 370 record di colonna, 740 profili e 3700 campioni
si contano 912 hit native esatte e 456 collegamenti di fonte aggiuntivi.
Restano 2332 confronti senza corrispondenza, zero profili completi e zero
assegnazioni. Le due estensioni sono scope distinti e possono sovrapporsi.
Restano 35 stati, 14 chimiche sorgente, 62 solve di ricerca storici,
6 equilibrî diagnostici di riferimento e 4 candidati Cold MORB.

## Fonti e alternative

Il runner usa FEG e PRE regionali autenticati, la triangolazione canonica,
la griglia T0 e la partizione di placca originali, la membership D12 e le
regole di origine del provider di composizione. Ogni nodo conserva le
celle native incidenti, il proprietario numerico PRE, le placche, i
confini e i flag di supporto. I dati PRE descrivono proprietà di riferimento
e termica autoriali. La classificazione diretta appartiene alla cella
nativa. La classificazione al nodo è condizionale e richiede supporto
incidente coerente. La proprietà di lato di faglia resta irrisolta.

| Scope | Continentale condizionale | Oceanico condizionale | Misto o conflittuale | UNKNOWN |
| --- | ---: | ---: | ---: | ---: |
| 8×8 primario | 56 | 0 | 25 | 0 |
| 16×16 sensibilità di dominio | 161 | 21 | 104 | 3 |

Nell'8×8, UCC, MCC e LCC sono tre endmember omogenei distinti, con
qualifica felsica fredda mancante. Il proxy basaltico MORB base/wet
ha supporto condizionale solo nel 16×16. DMM è un analogo di ricerca per
il mantello litosferico. Le sensibilità low/high H₂O e high ferric si
confrontano singolarmente con M01 base. La composizione omogenea di
engineering può essere discussa come alternativa di screening, con
approvazione esplicita del supporto misto. La stratigrafia, l'acqua
strutturale, la pressione di poro e la fugacità richiedono autorità
distinte. Tutti i candidati sono unselected.

## Piano e chiusura

Il replay di sviluppo conta 951 identità di confronto distinte. Sette
riusano evidenze di ricerca, due esatte native e cinque ancorate alla fonte.
Sette richiedono valutazione di proprietà ereditate senza equilibrio di
default. Le altre 937 sono gap P/T condizionali. Tutti i 944 punti senza
una corrispondenza in archivio cadono fuori dall'intervallo comparativo della
stessa ricetta nativa. Gli estremi archiviati non delimitano la validità
scientifica del provider. Preservare i supporti di ogni occorrenza e
approvare prima la domanda di proprietà, poi la chimica, il modello, la
politica delle fasi e la pressione assoluta. A 280 K, ΔP condizionale
zero lascia P assoluta sconosciuta. Query nuove eseguibili: zero.

- **SHELLSET_MINIMUM.** Il contratto nativo permette di procedere con
  FEG, termica e riferimenti PRE dopo la selezione della configurazione
  fisica. Servono proprietà di riferimento applicabili e anomalie/curvatura
  governate, reologia, attrito e condizioni regionali, qualificazione
  di runtime e normalizzazione dei risultati. Non richiede pressione
  assoluta esterna o copertura di equilibrio su cinque profondità.
- **G2_G3_FULL_COUPLED.** La matrice conserva gli otto gruppi sorgente.
  Le ipotesi di composizione, pressione/acqua e calibrazione possono
  informare i tre gruppi G2. Restano indipendenti i carichi ai tagli e
  alla base completa, GPE, interfaccia/faglia e compatibilità del solver.
  L'8×8 conserva 81 nodi, 162 DOF EN, 32 spigoli esterni e 120+8
  facce basali. Il 16×16 conserva 289 nodi, 578 DOF, 64 spigoli e
  504+8 facce. I carichi mancanti restano sconosciuti. Euler e LAB
  termica non determinano la trazione o la LAB meccanica.

L'approvazione di un'ipotesi di ricerca fissa proxy, supporti ed esclusioni.
Prima di ogni assegnazione fisica servono condizioni materiali/fluide
autorizzate, validità costitutiva e chiusura meccanica indipendente.
Le assegnazioni restano 0, la selezione è nulla, T1 è nullo e l'autorità
di solve meccanico e WORLD_HISTORY production è falsa.

## Controlli e qualifica FAIR

Sviluppo: import e replay read-only in memoria, 13 nuovi test, 707 PASS
sulla selezione cumulativa qui sotto. La qualifica sulla revisione
pubblicata e l'archivio C06 restano da eseguire. Nessun motore è stato avviato.

Dal worktree di verifica esistente, recuperare il branch e creare un
worktree dedicato e pulito sullo SHA **pubblicato per C06**. Attivare
`arcana-r6-linux` e usare la stessa selezione. Impostare
`C06_SHA` allo SHA esatto pubblicato. Il runner verifica l'HEAD, gli
archivi originali e il percorso nuovo prima dell'output.

```bash
set -e
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD" PYTHONDONTWRITEBYTECODE=1 OPENBLAS_NUM_THREADS=1
test "$(git rev-parse HEAD)" = "$C06_SHA"
test -z "$(git status --porcelain)"
python -c 'from experiments.r6_thermo_provider_pilot_v1 import run_c06_regional_material_hypothesis'
python -m pytest -q -ra --tb=short -p no:cacheprovider tests/test_r6_thermo*.py \
  tests/test_r6_g2_g3_physical_source_packet.py tests/test_r6_g2_g3_source_to_coupled_handoff.py
rc=0
python -m experiments.r6_thermo_provider_pilot_v1.run_c06_regional_material_hypothesis \
  --expected-sha "$C06_SHA" --offline-regional-hypothesis-only || rc=$?
printf 'C06_EXIT=%s\n' "$rc"
exit "$rc"
```

Attesi 707 test nella selezione, exit 0 e
`C06_SOURCE_KEYED_REGIONAL_HYPOTHESES_READY_FOR_AUTHORIAL_REVIEW`.
L'archivio di sola nuova scrittura
`ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_C06_REGIONAL_MATERIAL_HYPOTHESIS_NEW01`
contiene replay, autorità geologica, report delle due regioni, piano
query, matrice delle due vie, scheda decisionale e manifest.
