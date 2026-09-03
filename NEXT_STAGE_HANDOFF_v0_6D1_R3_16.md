# NEXT_STAGE_HANDOFF — after R3.16

If the canonical R3.16 run and seal pass, the authoritative biological boundary
is 125 ka. The exact R3.14 environmental restart is 120 ka, leaving a governed
5 kyr synchronization remainder represented by exactly ten 500-y C2 intervals.

Natural next stage:
**v0.6D1-R3.17 — 125->120 ka Exact Recent-Restart Biological Synchronization**.

R3.17 must derive a bounded partial-step treatment or a recent-domain solver
without modifying the R3.7I/R3.8 calibrations by stealth. It must not simply
rename the 125 ka state as 120 ka.


### R3 runtime-A1 container-contract repair
R3.16 reopens the same sealed `FULL_A1_REFERENCE_210_0Ma.npz` as an `NpzFile` for the R3.8 runtime because R3.8 explicitly inspects `a1.files`. R3.14 provider construction continues to use its dict view. This is a container/binding repair only: no arrays, equations, scientific parameters, cadence, or parent authority changed.
