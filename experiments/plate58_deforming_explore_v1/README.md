# ARCANA R6 — Contatto 5:8, preparazione EXPLORE senza solve

**Scope:** modello NON CANONICO, autorizzato soltanto a caratterizzare e preparare
il primo transetto deformante. **Non** promuove proxy quarzite/olivina, acqua,
larghezza della fascia, forza basale o trazioni laterali a proprietà del mondo.

Fonte: rapporto FAIR G2/G3 2026-11-19, analisi del transetto 5:8;
\`docs/arcana/R6_FIRST_DEFORMATION_MODEL_DECISION_FAIR_20261118.md\`.
D-024 rimane invariata.

## Cosa genera

- FEG 9 nodi / 8 triangoli source-bound delle celle R100–101/C021–022,
  PRE regionale con i record parent e reader Fortran *isolato* (nessun solve).
- Contatto derivato dalle adiacenze **reali** fra plate ID 5/8,
  con due segmenti e tre nodi condivisi, frame e segni controllati.
- Sei vettori distali (3 ovest placca 8, 3 est placca 5) in coordinate
  sud/est SHELLS; nord/sud lasciati \`null\`, senza sostituire automaticamente
  free/periodic/fixed. Angoli, attributi e local ID espliciti.
- Inviluppo 16 celle R099–102/C020–023 *solo diagnostico* per i gradini
  del contatto, senza costituire una mesh risolta del rift.
- Sensitività **diagnostiche** alle larghezze 10, 100, 300 km.
  La fascia 100 km è ipotesi EXPLORE: la griglia di un grado non fissa
  la scala di deformazione e il fit reologico non prova la mineralogia.

## Staging su FAIR

Da un checkout che contiene gli input R6 e i payload esterni verificati
(vedere anche il README dell'esperimento cinematico):

\`\`\`bash
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
  python -m experiments.plate58_deforming_explore_v1.prepare \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
PYTHONPATH=src:. PYTHONDONTWRITEBYTECODE=1 \
  python -m experiments.plate58_deforming_explore_v1.check \
  /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/PLATE58_STAGE_NEW_01
PYTHONPATH=src:. python -m pytest -q tests/test_r6_plate58_deformation_prepare.py
\`\`\`

L'output deve trovarsi in una **directory nuova**; non sovrascrivere
nessuno degli archivi sigillati esistenti. \`MANIFEST.json\` lega gli SHA
dei quattro membri generati e quelli delle autorità T0 usate.

## Hard gate fisico

\`CASE.json\` resta con \`readiness.mechanical_solve_authorized=false\`.
I campi \`decisions\` sono separati dai dati source-bound e contengono
\`null\` per coefficienti G2, pressione efficace, legge idrica, applicabilità
dei fit, larghezza/risoluzione fisica, validità temporale deformante, condizioni
nord/sud e supporto normale alla base. Lo scenario *free-slip tangenziale*
è solo un'ipotesi, **non** una legge di sostegno verticale.

Non usare il file regionale come input per un solve ARCANA finché
non sono chiuse tali decisioni mediante un input revisionato e testato.
Non eseguire T1, né rimappare masse, stock o temperature.

## Nota importante sul confronto delle due leggi crostali

Le cifre 405/98 MPa a 10 km e il fit \`eCreep=0.267857\`
provengono dalla scheda decisionale FAIR, non sono nuove misure o
una calibrazione effettuata da questo preparatore. Il fit di esponente
differisce ~3,1% sulle curve testate, non sull'incertezza geologica reale.

Lo scopo della prova è localizzare gli input mancanti, **non**
costruire un forcing artificiale per far convergere SHELLS.
