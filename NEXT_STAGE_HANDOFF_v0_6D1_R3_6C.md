# Next-stage handoff after R3.6C

R3.6C establishes the fair cadence mapping required before running NEMO. Do not copy ARCANA 125-kyr exchange values directly into per-generation NEMO dispersal.

Next natural stage: `v0.6D1-R3.6D — NEMO 2.4.2 Executable Reference Binding & Ensemble Run Evidence`.

R3.6D should:
1. validate/install `nemo2.4.2` (WSL2 on Windows is acceptable upstream);
2. bind an upstream-valid NEMO 2.4.2 `.ini`/input mapping without guessed parameter names;
3. run B0/B1 and C3 ensembles with cadence-normalized per-generation dispersal;
4. run N sensitivity;
5. parse VA/trait/allele-frequency/population outputs into `ScientificEvidenceBundle`;
6. compare control-normalized admixture excess against ARCANA 125k and 5×25k;
7. keep `mu`, `b`, q*, ceiling and D3 authorities unchanged until evidence is reviewed.
