# NEXT — R6-INT0B: esecuzione candidata non canonica T-F2B 5:11

**Una sola priorità corrente (2026-10-12).** INT-0A è chiuso nel perimetro codice/test offline con `INT0A_INTEGRATION_CODE_READY__NONCANONICAL_RUN_NOT_YET_EVIDENCED`. Il prossimo task è l'esecuzione numerica non canonica del runner multi-provider esistente, previa autorizzazione distinta. Non iniziare un altro workpack di design aperto. W3-C-B-R1 rimane nel filone parallelo ShellSet SI1.

## Pacchetto delimitato

1. Input: branch `r6/si1-bandwidth-f2av` e commit verificato al momento dell'autorizzazione; runner `scripts/r6_functional_development_t_f2b.py`; pair 5:11; supporti esatti selezionati dall'audit lower-median; profili T0 ammessi; durata engineering 1.000 anni; forcing Euler congelato; fattori `0.001`, `0.0005`, `0.00025`. Passare `--expected-branch r6/si1-bandwidth-f2av` esplicitamente.
2. Preflight: ripristinare l'input fisico-geografico esterno nella posizione governata e verificare manifest/hashes B4/B5/B6N8-N; registrare inventario, commit e versioni Python/NumPy. Se input o identità mancano, fermarsi senza sostituti.
3. Destinazione: directory nuova e univoca sotto `outputs/r6_functional_development`, ad esempio `INT0B_TF2B_5_11_<run-id>`. Non riusare il percorso storico T-F2B né sovrascrivere output. Eventuali output parziali dopo errore restano non autorevoli.
4. Prima del run, ottenere autorizzazione INT-0B separata che dichiari accesso agli input, budget CPU/tempo/RAM/output, ambiente, directory, comando e condizioni di arresto. Nessuna autorizzazione deriva da INT-0A.
5. Eseguire soltanto il runner non canonico previsto dall'autorizzazione: nessun ShellSet, MPI, Solver, evoluzione post-rift o modifica `WORLD_HISTORY`. Verificare finitezza, invarianti governate, replay/restart e manifest; riportare costi e UNKNOWN senza promozione scientifica/canonica.

Report INT-0A: `docs/arcana/INT0A_MULTI_PROVIDER_INTEGRATION.md`. I test provano solo l'integrazione su fixture sintetiche; il risultato provider-backed resta non evidenziato. Gate F2A-V, Solver, mechanics e WORLD_HISTORY invariati.
