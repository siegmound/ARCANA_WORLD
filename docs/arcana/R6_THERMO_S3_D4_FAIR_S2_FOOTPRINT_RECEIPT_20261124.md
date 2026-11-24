# ARCANA R6 — S3-D4: storico footprint dei membri S2 su FAIR (read-only)

**Data:** 2026-11-24. **Decisione:** `S3_D4_S2_FOOTPRINT_READONLY_PASS__S3_IO_MEMORY_BUDGET_NOT_YET_RATIFIED`.

## Provenienza
L'operatore FAIR ha usato `R6_THERMO_S2_REPEATABILITY_NEW01/MANIFEST.json`, SHA256 `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`, e ha controllato SHA256, esistenza, assenza di symlink e contenimento nella root di **tutti i 68 file** elencati in `files_sha256`. Marker `S3_D4_S2_FOOTPRINT_READONLY_PASS`, `S3_ENGINE_RUNS=0`, `S3_D4_FOOTPRINT_EXIT=0`. Questo rapporto registra **l'output condiviso dall'operatore**; il client GitHub non ha accesso diretto ai byte FAIR per ricalcolare autonomamente gli SHA.

## Dimensioni osservate
| Gruppo | File | Byte | MiB |
|---|---:|---:|---:|
| MAGEMIN | 15 | 19.995 | 0.01907 |
| PERPLEX | 50 | 4.319.903 | 4.11978 |
| ROOT_METADATA | 3 | 5.196 | 0.00496 |
| **Somma membri manifestati** | **68** | **4.345.094** | **4.14380** |

Perple_X rappresenta 99.420% della somma. I cinque file più grandi, ciascuno `PERPLEX_0[1-5]/BL691_MEEMUM/solution_model.dat`, hanno tutti dimensione **731.947 byte**, somma **3.659.735 byte**, pari a 84.227% dei byte manifestati. **Stessa dimensione non dimostra identità dei byte:** il report non dispone degli SHA individuali, pur avendo verificato ciascun membro contro il digest del manifest. Non asserire una deduplicabilità certa senza confrontare SHA256/byte originali.

**Potenziale puramente aritmetico, NON autorizzato:** eliminare quattro copie di dimensioni identiche ridurrebbe il conto logico di **2.927.788 byte (2,792 MiB)** soltanto se i byte fossero identici e un contratto futuro consentisse un artifact shared immutabile mantenendo l'integrità per processo. S2 è SEALED: **vietato deduplicare, sostituire, symlinkare, riscrivere o rimuovere qualsiasi vecchia copia**.

L'inventario somma soltanto i **membri** del manifest: non comprende i byte di `MANIFEST.json` stesso, eventuali file non manifestati, dimensioni allocate a blocchi, compressione, inode, né il footprint effettivo di un nuovo studio S3. In particolare non misura RAM (peak RSS), I/O aggregato di futuri processi, dimensioni di output per punti variabili P/T o calcolo scientifico.

## Conseguenze S3-D4
1. **Baseline tempi già disponibile:** S2 Magemin 5 fresh process, 2 casi/processo, somma 31,75680620968342s; S2 Perple_X 5 processi, 1 caso/processo, somma 5,788513708859682s. L'intero S2 ha 37,5453199185431s di elapsed_s registrato, ma non è un tempo per punto S3.
2. **Baseline storico storage:** 68 membri, 4.345.094 byte. I file di modello Perple_X ricopiati dominano i byte, non i dati chimici che possono essere scalati con un fattore 25 senza misurazioni.
3. **Mancano ancora:** peak RSS FAIR, modello volume dati per punto S3, validità fisica della griglia per composizione/redox/soluzione magmatica/metabasica, tolleranze S3 preregistrate, protocollo S3 fail-closed write-once e autorizzazione S3.
4. **Prossima azione scientifica:** per `ig/tc_ds636` (MAGEMin G25) e `hp62ver.dat` (Perple_X BL691) raccogliere evidenze **composizione-specifiche e P/T-X** da riferimenti pubblicati, annotando ogni cella del contratto S3 come SUPPORTED/UNSUPPORTED/UNKNOWN soltanto quando la fonte lo giustifica. Non confondere i bounds P/T del file BL691 con un certificato di calibrazione.
5. **Controllo secondario di storage facoltativo e solo read-only:** confrontare i cinque SHA256 `solution_model.dat` già inventariati; gli identici nomi e le dimensioni non bastano. Nessun nuovo run necessario.

`D-024=ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`. Gli obiettivi di storia geologica/Deep/risorse/biomi di ARCANA non ricevono nuove autorizzazioni.
