# Visione e criteri di successo di ARCANA WorldSim R6

**Obiettivo finale:** generare una storia mondiale causale, coerente, interrogabile e ricostruibile da circa **210 Ma a 0 ka**. Non solo popoli: evoluzione di geografia, tettonica, geologia, clima, idrologia, risorse naturali, campi/trasporti Deep, flora, fauna, popolazioni e società. Deve essere possibile chiedere, per luogo e tempo, cosa esisteva, quanto era disponibile, come si è formato e con quale incertezza; e richiedere un replay più fine di una finestra/regione.

ARCANA orchestra **tool scientifici specializzati**, ne governa input/output, semantiche, validità, dipendenze, conflitti, conversioni e gap. Si costruiscono nuovi modelli/integratori solo quando un provider non copre il fenomeno e una soluzione fisica è giustificata. I provider non promuovono autonomamente WORLD_HISTORY.

## Tempo e conservazione
- Non esiste un unico `dt` globale **fissato a priori** per la simulazione. Ciascun motore può avere passi numerici e limiti diversi; il controller potrà adattare i passi quando autorizzato.
- ARCANA esegue **finestre temporali candidate**. Analizza cambiamenti, eventi, propagazioni causali e incertezza; seleziona **stati significativi** da conservare; mantiene eventi e forcing distinti dagli stati.
- Il `INTERNAL_DT` dei modelli non è il `PERSISTENT_STATE_INTERVAL` di WORLD_HISTORY. Per ricostruzione servono checkpoint, recipe, source/version/seed/config, dipendenze, step decisions, forcing, event brackets, incertezza e tolleranze di dominio. Se non può essere dimostrata una ricostruzione sufficiente, conservare i campioni richiesti o fallire chiusi.
- Nessuno stato temporale o anchor legacy è un target da raggiungere. Gli anchor scientifici possono essere dati di validazione indipendenti, non stati R5 da replicare.
- Deep e vincoli canonici di ARCANA rimangono proprietà del modello; non fabbricare dati di Deep/risorse/biologia tramite interpolazione non qualificata.

**Criterio di successo architetturale:** per ogni finestra simulata, output dei provider + closure causale + stati/eventi selezionati + ricostruzione entro criteri dichiarati + provenance verificabile. **Criterio finale:** WORLD_HISTORY mondiale fino al presente, interrogabile e raffinabile selettivamente.

Fonti primarie: `docs/arcana/WORLD_HISTORY_ARCHITECTURE.md`, `docs/arcana/B6N6_ADAPTIVE_PROPAGATION_STATE_EXTRACTION_ARCHITECTURE.md`, `contracts/R6_ADAPTIVE_PROPAGATION_CANDIDATE_TRAJECTORY_V1.json`, `contracts/R6_SIGNIFICANT_STATE_EXTRACTION_RECONSTRUCTION_V1.json`.
