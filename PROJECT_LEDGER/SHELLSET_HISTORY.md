# ShellSet — risultati precedenti vs qualifica ARCANA attuale
**Non ripartire da zero** o affermare che ShellSet non ha mai risolto nulla in parallelo.

## Qualifiche pregresse Fair, scope UPSTREAM
Fonte primaria `R6_SHELLSET_FAIR_RUNTIME_QUALIFICATION.json` (2026-09-28):
- compilazione con NVIDIA HPC SDK 25.11, MPI NVHPC, BLAS/LAPACK supportati;
- LAPACK smoke `DGBSV`, `DGESV`, `DSYSV` PASS; startup MPI 2 ranks PASS;
- upstream `ListEx1` n10_t5: **9/9 modelli completati**, 711.95 s stock; variant capacity 9/9, 661.07 s; altri parallel-run confrontati a precisione dichiarata;
- differenza stock/capacity a precisione riportata: zero;
- `qualified_for_upstream_scientific_example=true` e capacity patch only, `arcana_t0_mechanics_authorized=false`.

Fonte `R6_T0_ORBDATA_ARCANA_FAIR_RUNTIME_QUALIFICATION.json`:
- build/patch ARCANA runtime + input setup, smoke MPI, esecuzione `ListEx1` 9/9 con output reference confrontato per global model ID;
- **non** esecuzione OrbData T0 né qualifica completa meccanica ARCANA, `shellset_mechanics_authorized=false`.

**Interpretazione:** abbiamo già provato il funzionamento parallelo del programma sulla configurazione upstream. Quanto della CPU sia stato impiegato va letto dai log/risorse della specifica prova; `n10_t5` non è automaticamente una misura di core effettivamente occupati.

## Nuova qualifica ARCANA SI1/BW1, scope diverso
`configs/r6_shells_si1/engineering_case.json`: caso globale ARCANA (64,442 nodi, 128,880 triangoli, zero fault elements), parametri di riferimento `ENGINEERING_SOLVER_REFERENCE_NOT_ARCANA_GEOLOGY`, 1 modello, 2 rank MPI. Non è una simulazione canonica. F1 e F2A-V terminano **prima del Solver** per caratterizzazione del caso ARCANA; non sono test di accelerazione parallela o solve di ListEx1.
- dimensione matrice: nRank 128884, kl=ku=727, nKRows 2182;
- valid 186,996,964, nonzero 1,804,327, nonfinite 0; 10 coppie asimmetriche su 93,434,040; 0 righe strettamente diagonaldominanti nel conteggio F2-A;
- F2A-V MPI stop 75; parser blocca il CSV a causa dei campi invertiti. I risultati F2A-V non sono ancora completamente adjudicated.
- DOF mapping autorevole non verificato: non localizzare coppie o assumere gauge.

**Decisione da prendere dopo recovery:** se il caso ARCANA richieda modifica dell'approccio numerico o solver, confronto con altri metodi, e quale interfaccia tettonica effettivamente serva al multi-tool orchestrator.
