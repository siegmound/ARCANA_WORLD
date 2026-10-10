# SI1 / BW1 — F2-B Solver Preflight Design (non-esecutivo)
**Classificazione:** `DESIGN_ONLY__NO_SOLVER_AUTHORITY`.
**Fonte del checkpoint:** ricognizione Codex locale del 2026-10-10 sul branch `r6/si1-bandwidth-f2av`, HEAD locale `6e6bd36f3db2e6e07f406d757721f7a4b552cf8b`, riportata dall'operatore. Lo stato remoto del repository prima della redazione è `bb3b6c781e6d8dac20c446ab9b0e97fe634cb61d`, un commit documentale successivo. La ricognizione è read-only e non è un result/manifest sealed. Nessun nuovo test, Fair, MPI, Solver o simulazione.
**Fonti primarie:** `external/ShellSet-v1.1.0/src/MOD_Shells.f90`, `external/ShellSet-v1.1.0/src/SHELLS_v5.0.f90`, `configs/r6_shells_si1/engineering_case.json`, `contracts/R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json`, `docs/arcana/SI1_BW1_F2AV_DIAGNOSTIC.md`, F2-A sealed e F2A-V recovered identificati in `PROJECT_LEDGER/EVIDENCE_INDEX.md`. Questa specifica deriva dal report e richiede ulteriore attestation end-to-end; non conferisce autorità scientifica.

## 1. Esito della ricognizione
**`F2B_PREFLIGHT_DESIGN_RECON_COMPLETE__EXECUTION_NOT_AUTHORIZED`** è una etichetta di workflow proposta, non uno status definito dal contratto scientifico.
Il caso è `NON_CANONICAL_ENGINEERING_CANDIDATE`: continuum globale su sfera chiusa, 64.442 nodi, 128.880 triangoli, zero elementi di faglia, zero condizioni di velocità prescritte. Parametri `ENGINEERING_SOLVER_REFERENCE_NOT_ARCANA_GEOLOGY`. Risultato storico F2A-V `BLOCKED_F2AV_QUALIFICATION` preservato; derived recovery `F2AV_OFFLINE_RECOVERY_COMPLETE_REQUIRES_NUMERICAL_ADJUDICATION` e adjudication GO-design-only sono tre livelli separati.

## 2. DOF, permutazione e base locale
- ShellSet usa `x = 2*node - 1` e `y = 2*node`. La banda LAPACK rappresenta `A(i,j)` in `AB(iDiagonal+i-j,j)` con `iDiagonal=1455`.
- Candidato di mapping: DOF grezzo -> componente 1/2 e nodo del FEG staged -> nodo di origine mediante `new_to_old`; inversa attesa `old_to_new`.
- La ricognizione segnala file di permutazione, FEG derivato, runtime derivato, con soli prefissi SHA rispettivamente `a0895fd9…`, `18d78ec0…`, `a68c0730…`. **Non trattare i prefissi come identificatori completi verificati**; attestare path, contenuto, hash completi e provenienza con gli input staged realmente utilizzati.
- Verifiche progettate: bijezione su `1..64442`; `old_to_new(new_to_old(i)) == i`; no duplicati/out of range; connettività dei 128880 triangoli rispetto alla permutazione; round-trip record FEG (coordinate e indici) e riallineamento dei campi runtime e metadati; linkage rigoroso ai file staged del run F2A-V. Verificare anche il senso concreto della base componente 1/2 in funzione delle coordinate e della geometria, senza attribuirlo automaticamente al sistema geografico.
- **Stato:** `DOF_MAPPING_UNVERIFIED` per l'export F2A-V fino a prova end-to-end; il solo mapping nodo/componente può diventare `DOF_MAPPING_PARTIAL` soltanto come classificazione di verifica distinta da una mappa geografica completa. Nessuna attribuzione geospaziale o di placca alle 10 anomalie.

## 3. Operatore, asimmetria, nullspace e gauge
- Assembly percorso riportato: `FEM -> BuildF -> BuildK -> AddFSt -> VBCs -> Solver -> DGBSV`. Il debug F2A-V si arresta prima di `Solver`.
- `nRank=128884`, `kl=ku=727`, `nKRows=2182`, `iDiagonal=1455`, storage generale a banda. F2A-V riporta 93.434.040 coppie upper confrontate, 10 discrepanti sopra soglia relativa `1e-12`: una `ZERO_NONZERO` per `(128678,128873)` (valori `1.4073748835532800E+014` e zero), nove `NONZERO_VALUE_MISMATCH`. Discrepanza relativa massima `1.0`; discrepanza massima row-scaled circa `6.0872e-18`.
- Dalla matrice osservata segue solo che **non è esattamente simmetrica alla precisione esaminata**. La presenza di tangente `alpha` strain-dependent non stabilisce l'aspettativa teorica di simmetria; approfondire source/equazioni, linearizzazione, vincoli e assembly prima di classificare l'operatore. Nessun `(A+A^T)/2`, nessuna causa attribuita alle 10 coppie.
- `VBCs` con `nCond=0` non applica vincoli cinematici nel caso riferito. Possibili rotazioni globali/modi rigidi sono ipotesi, non autovalori/nullspace dimostrati. `NO_GAUGE_IN_INITIAL_RUN`; vietata gauge automatica. Ogni richiesta di test di nullspace o intervento gauge necessita gate specifico.

## 4. Solver path, preservazione di A e RHS, budget
- In `MOD_Shells.f90` la routine `Solver` chiama `dgbsv(n,kl,ku,nrhs,ab,ldab,ipiv,b,ldb,info)`. `ab` viene sovrascritto dalla fattorizzazione e `b` dalla soluzione; `INFO=0` da solo non dimostra accuratezza/validità fisica.
- Array `REAL*8` `2182 * 128884 * 8 = 2249799104` byte (~2.095 GiB) **per istanza**, non RSS né memoria totale su 2 rank. La banda include righe addizionali di workspace/fill legate al pivoting nella rappresentazione `DGBSV`; non presumere una *seconda* copia della matrice creata automaticamente dalla routine, ma censire copie e allocazioni effettive nell'applicazione, RHS, pivot, dati FEM, MPI/runtime e eventuali buffer di residual.
- Prima di un futuro run, dimensionare allocazioni per ciascun rank e aggregate e legarle a limiti imposti realmente (vs meri limiti dichiarati dall'operatore). Provare che `nrhs`, iterazioni e numero di chiamate Solver siano bounded. Nessuna allocazione/fattorizzazione in questo gate.
- La verifica residuo usa proposta `||b_0 - A_0 x||_inf/(||A_0||_inf ||x||_inf + ||b_0||_inf)` su A e b **pre-solve**; bisogna documentare strategia riproducibile di ricostruzione/reassembly o matvec approvato. Soglie non stabilite; prevenire overflow/underflow negli accumulatori; zero denominatore e residui nonfinite devono fallire closed.
- Futuro output solver deve includere almeno `INFO`, soluzione finita, residuo/backward error, identità sorgenti e input, limiti risorsa realmente verificati, classe operatore/gauge, e failure evidence. Non usare `INFO=0` da solo come PASS.

## 5. Proposta gates distinti, tutti fail-closed
| Gate | Prova richiesta | Stato attuale | Azione consentita |
|---|---|---|---|
| F2B-D0 — design reconnaissance | source/evidence review e inventory | `COMPLETE_AS_REPORT` | documentare |
| F2B-D1 — DOF provenance | SHA completi, contenuti, bijezione, inverse, FEG/runtime linkage, raw-index mapping | `UNVERIFIED` | progettare attestation offline |
| F2B-D2 — operator contract | sorgente equazioni/assemblaggio/BC, simmetria attesa, 10 pair e limiti | `UNKNOWN` | source trace e specifica controlli |
| F2B-D3 — resources/residual | allocation graph per rank, limite effettivo, strategia A_0/b_0 residuo, metriche | `PARTIAL` | budget/contract senza run |
| F2B-D4 — NVHPC instrumentation | compile-only corrected writer, IEEE sticky behavior, linkage tests | `NOT_QUALIFIED` | progettare gate separato |
| F2B-E — engineering solve | precedente gate + approvazione operatore esplicita | `NOT_AUTHORIZED` | nessuna esecuzione |
| SCIENCE/CANONICAL | autorità geofisica ARCANA e provenance completa | `NOT_AUTHORIZED` | nessuna promozione |

Il prossimo lavoro concreto è **F2B-D1**, con una mappa di corrispondenza attestata o una lista puntuale di artefatti mancanti. Evitare di riscrivere la logica ShellSet source-locked o generare un file di mapping fittizio in assenza dei dati.

## 6. Acceptance del futuro preflight design
Il documento progettuale può essere classificato `DESIGN_COMPLETE_PENDING_EXECUTION_AUTHORITY` solo quando i requisiti, gli input realmente disponibili, le verifiche e i blocchi sono esplicitati e lo scope di un eventuale run è chiuso. Questo stato **non** implica `F2B_SOLVER_EXECUTION_AUTHORIZED`. Se mancano artefatti/autorità: `DESIGN_BLOCKED_MISSING_SOURCE_OR_AUTHORITY` con `UNKNOWN` preservati.

**Divieti:** nessun Fair/MPI/Solver/factorization/auto-gauge/forward evolution/canonical WORLD_HISTORY write. Non ripetere ListEx1 9/9 upstream parallel proof. Non sostituire target ARCANA R6 con output R3–R5.
