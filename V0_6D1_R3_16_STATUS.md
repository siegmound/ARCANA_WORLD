# v0.6D1-R3.16 status

Status: **CANDIDATE — ready for local canonical 250->125 ka run after checks**.

Candidate evidence:
- Formal candidate audit: 318/318 PASS.
- R3.16 unit tests: 9/9 PASS.
- Focused inherited regression R3.14-R3.16: 36/36 PASS.
- Constant-forcing wrapper equivalence: bit-identical R3.8 state.
- No scientific parameter change.
- No adaptive-clock checkpoint promoted to a biology step.
- 150 C2 500-y intervals consumed as exposure quadrature.
- 10 C2 500-y intervals (125->120 ka) explicitly left unresolved for next stage.


### R3 runtime-A1 container-contract repair
R3.16 reopens the same sealed `FULL_A1_REFERENCE_210_0Ma.npz` as an `NpzFile` for the R3.8 runtime because R3.8 explicitly inspects `a1.files`. R3.14 provider construction continues to use its dict view. This is a container/binding repair only: no arrays, equations, scientific parameters, cadence, or parent authority changed.
