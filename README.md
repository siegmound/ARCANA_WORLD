# ARCANA_WORLD1_v0_6D1_R3_6B

Current stage: **v0.6D1-R3.6B — NEMO 2.4.2 Governed QTL-Ensemble Reference Benchmark**.

Verdict: `PASS_QTL_ENSEMBLE_REFERENCE_IMPLEMENTATION__NEMO_2_4_2_ENGINE_EXECUTION_PENDING`.

R3.6B extends the governed scientific-engine bridge without changing the canonical WorldSim biological model. It materializes reproducible genetically explicit QTL ensembles and four controlled reference scenarios so the R3.5 `V_A` problem can be cross-validated against NEMO 2.4.2 before any change to `mu`, `b`, gene-flow moment mixing, or the numerical ceiling.

Key invariants:
- ARCANA owns canonical world state, clock, species registry and speciation authority.
- NEMO is an independent reference oracle only.
- `q*=0.045` remains fixed.
- R3.5 150 Ma remains diagnostic, not a canonical continuation checkpoint.
- no guessed NEMO `.ini` parameter semantics are accepted.

Run validation on Windows:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\run_v0_6D1_R3_6B_checks.ps1 -Threads 12
```

Prepare the governed benchmark ensemble:

```powershell
$env:PYTHONPATH = "$PWD\src"
python scripts\prepare_nemo_qtl_ensemble_v0_6D1_R3_6B.py local_runs\R3_6B_NEMO --replicates 8 --individuals 2000 --loci-per-trait 64
```

See `README_R3_6B.md` and `NEXT_STAGE_HANDOFF_v0_6D1_R3_6B.md`.

## v0.6D1-R3.6C
Current candidate adds cadence-normalized three-way quantitative-genetics validation. See `README_R3_6C.md`.


## v0.6D1-R3.6D — NEMO 2.4.2 Executable Reference Binding & Ensemble Run Evidence

See `README_R3_6D.md`. R3.6D binds the independent NEMO reference to official 2.4.2 parameter/lifecycle semantics and provides WSL ensemble execution plus governed evidence collection. It does not alter canonical D3 behavior.

## v0.6D1-R3.6E — NEMO Evidence Closure & Quantitative-Genetics Causal Inference Gate

Real NEMO 2.4.2 evidence is now bound: 40/40 jobs executed and 40/40 parsed. R3.6E adds an analytic 64-QTL infinite-population comparator and concludes that the dominant R3.5 VA inflation is structural in the current whole-trait admixture moment operator. No calibration or production replay is authorized by this stage. See `README_R3_6E.md` and `QUANTITATIVE_GENETICS_CAUSAL_INFERENCE_GATE_v0_6D1_R3_6E.md`.

## v0.6D1-R3.7 — Segregation-Aware Admixture Variance State & Reduced-Order Genetic Mixing Repair

R3.7 introduces a non-production candidate that separates persistent `VA_within`, signed transient `C_ancestry_LD`, and pairwise trait-specific segregation potential `S_ij`. On the real R3.6D 64-QTL references it reproduces direct polygenic allele-frequency mixing to numerical precision while preserving the existing D3.3A mean-flow semantics. Production binding remains blocked until R3.7A defines initialization/evolution and fission/coalescence/speciation lifecycle rules for the new genetic-distance state.

See `README_R3_7.md`, `SEGREGATION_AWARE_ADMIXTURE_VARIANCE_CONTRACT_v0_6D1_R3_7.md`, and `NEXT_STAGE_HANDOFF_v0_6D1_R3_7.md`.

## v0.6D1-R3.7A — segregation-potential lifecycle candidate
R3.7A adds minimum-information 210 Ma initialization, D3.3A-consistent drift transfer, explicit selection-coordinate semantics, and exact fission/coalescence/speciation/remap lifecycle for the segregation-aware state. It also provides a governed NEMO 2.4.2 B2 isolation→fragmentation→reconnection chain. Production binding remains fail-closed until B2 evidence is reviewed. See `README_R3_7A.md`.

## v0.6D1-R3.7B
Neutral segregation-potential lifecycle closed against real NEMO B2 evidence; neutral World-interval shadow binding ready. Directional-selection `K_eff` remains explicitly pending external calibration.

## v0.6D1-R3.7C candidate
Adds the governed NEMO 2.4.2 directional-selection oracle needed to calibrate adaptive segregation participation after neutral R3.7B closure. External NEMO selection evidence remains pending; production genetic-state binding remains forbidden.

---

## v0.6D1-R3.11 candidate

R3.11 restarts ordinary H0 biology at the R3.10 65.5 Ma post-CHA1 checkpoint and
runs to 61.0 Ma. See `README_R3_11.md` and
`CANONICAL_POST_CHA1_H0_RECOVERY_ADAPTIVE_RADIATION_RESTART_CONTRACT_v0_6D1_R3_11.md`.

## v0.6D1-R3.12 — SEALED

Canonical H0 diversity-recovery continuation is sealed at **46.0 Ma**: 104 species, 223 components, zero q clipping, exact checkpoint serialization identity, and no second CHA-1/thaw. See `README_R3_12.md` and `R3_12_FULL_POST_CHA1_DIVERSITY_RECOVERY_EVIDENCE_AUDIT.md`.

## v0.6D1-R3.13 — SEALED

Canonical H0 long-term post-CHA1 continuation is sealed at **30.0 Ma**: 111 species, 219 components, zero q clipping, exact checkpoint serialization identity, and exact environmental handoff identity to the late-Cenozoic provider. See `README_R3_13.md` and `R3_13_FULL_LONGTERM_REASSEMBLY_EVIDENCE_AUDIT.md`.
