# R3.7C Invalid Selection Evidence Audit — retained diagnostic evidence

The local R3.7C execution is retained as **diagnostic evidence only**. It is not valid calibration evidence for `K_eff`.

Observed facts from `local_runs/v0_6D1_R3_7C_SELECTION`:

- 16/16 chains completed at engine level.
- 80/80 expected NEMO phase executions returned successfully and produced qfreq evidence.
- 32/32 selected-vs-matched-neutral qfreq checkpoint pairs (fragmented + reconnected across 16 chains) are byte-identical.
- Therefore the realized selection response is exactly null in the evidence surface used by R3.7C.
- Parent R3.7C reported `NEMO_SELECTION_EVIDENCE_COMPLETE_REVIEW_REQUIRED` because completion was gated only on engine/qfreq availability; that status is superseded for scientific interpretation by R3.7C-R1.

Root cause: standalone `viability_selection` cannot be ordered after `breed_disperse` in the Wright–Fisher setup because `breed_disperse` performs the WF generation transition internally, leaving no offspring in `OFFSx` for the subsequent viability event. Ordering viability before breeding is also invalid because offspring do not yet exist. R3.7C-R1 therefore uses NEMO's composite `breed_selection_disperse` event for the selected branch.

Governance:

- Invalid R3.7C results are preserved, not deleted or silently reinterpreted.
- They must not be used to estimate `K_eff`.
- No WorldSim runtime, canonical parameter, or parent R3.7A/B authority is changed by this repair.
