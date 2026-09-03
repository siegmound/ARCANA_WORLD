# v0.6D1-R3.6D R2 — NEMO 2.4.2 qfreq finalization repair

## Scope
Technical evidence-output repair only. No ARCANA scientific authority, QTL realization, seed policy, migration mapping, population size, lifecycle, `mu`, `b`, `q*`, ceiling, or canonical state is changed.

## Observed real-engine evidence
The first WSL2 smoke executed 10/10 NEMO 2.4.2 jobs with return code 0, but produced 0 parseable `.qfreq` files.

## Root cause
NEMO 2.4.2 `TTQFreqExtractor` persists `.qfreq` when its file-handler callback occurs at the final generation. R3.6D originally set `quanti_freq_logtime = generations - 1`; with the standard one-interval run this was `25000` while `generations = 25001`. The callback therefore occurred at generation 25000 but not at the final generation, so the engine completed successfully without persisting `.qfreq`.

## Repair
- default `quanti_freq_logtime = nemo_generations`;
- reject custom qfreq logtimes that do not divide `nemo_generations` exactly;
- record the persistence schedule in the binding manifest;
- retain final-only qfreq output for the primary protocol because the exact initial QTL state is already present in the governed input manifest.

## Governance
This is an executable-evidence scheduling repair. It does not change the biological experiment.
