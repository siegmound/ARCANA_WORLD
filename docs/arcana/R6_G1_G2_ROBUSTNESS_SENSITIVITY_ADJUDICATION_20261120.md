# ARCANA R6 — Eight-source-scenario sensitivity adjudication (1000 model years)

**Recorded:** 2026-11-20. FAIR code commit `d07ae8038a5ddbcb8b4601e7b54582dc2420818a`; evidence-recording parent `220f1e4676753061cd9530b5fd4150f70be15b1e`.

**Decision:** `PASS_PARAMETER_SWEEP_NUMERICALLY__G2_DRAG_TAU_DOMINATE_REPORTED_DISPLACEMENT_RESPONSE__GLOBAL_SPARSE_G2_FEM_NEXT`.

The FAIR operator extracted the **1000-year** 8×8 and 16×16 per-scenario
maximum displacement and Euler-vs-coupled RMS speed from
`G1_G2_ROBUSTNESS_GLOBAL_SPARSE_NEW_01/ROBUSTNESS_GLOBAL_REPORT.json`.
These numbers are **rounded operator-visible values**, not a full binary
copy of the FAIR report. Original scenario report and manifest have not
been independently fetched. Previous FAIR validation remains 20/20
PASS with global 12-plate sparse graph CG 14 iterations and relative
residual 2.135772214e-10 — **not global P1 G2**.

## Relative changes compared to original manufactured baseline

Baseline 8×8: **104.67588 m** max displacement, feedback RMS
**0.026184 m/model year**; baseline 16×16: **117.31210 m**,
feedback RMS **0.015997 m/model year**.

| Synthetic source scenario | 8×8 max displacement | 16×16 max displacement | 8×8 RMS feedback change | 16×16 RMS feedback change |
|---|---:|---:|---:|---:|
| `baseline` | +0.000% | +0.000% | +0.000% | +0.000% |
| `uniform_viscosity_x10` | +0.000% | +0.000% | +0.000% | +0.000% |
| `crust_viscosity_x10` | -0.106% | -0.440% | +0.588% | +0.294% |
| `mantle_viscosity_x10` | +0.016% | +0.062% | -0.088% | -0.063% |
| `relaxation_half` | -2.644% | -4.488% | +32.245% | +30.756% |
| `relaxation_double` | +2.222% | +2.049% | -25.095% | -23.529% |
| `drive_dashpot_half` | -3.884% | -6.177% | +32.104% | +31.806% |
| `drive_dashpot_double` | +3.722% | +2.869% | -27.803% | -25.655% |

All percentages computed **from rounded operator outputs**, so differences
under the print resolution cannot be resolved. The original full-source
FAIR uniform-viscosity ×10 common-scale check reported a maximum
absolute difference of **6.252776074688882e-13 m**, which is more
accurate than the rounded table.

### Scientific engineering interpretation

1. **Scale degeneracy / structural non-identifiability:** both
   `eta_crust` and `eta_mantle` multiplied by ×10 result in no
   material change to the velocity/displacement. This is an algebraic
   consequence of `K` and `C = alpha*mean(diag(K))*I` scaling
   together, not a rock physics discovery.
2. **Isolated viscosity perturbations:** in this test, crosta ×10
   changes maximum displacement only −0.106% / −0.440% on 8×8 / 16×16;
   mantle ×10 changes it only +0.016% / +0.062%. Do not conclude
   the real crust or mantle is insignificant: the manufactured
   baseline contrast, source thicknesses and artificial force
   normalization dominate the measurement.
3. **Relaxation and dashpot matter:** tau 100 instead of 200 years
   reduces maximum displacement −2.644% / −4.488%, while the
   synthetic dashpot halved reduces it −3.884% / −6.177%.
   Feedback RMS magnitudes rise roughly 31–32% in these cases.
   Doubling tau/drag increases maximum displacement and reduces
   the Euler-vs-coupled RMS discrepancy. These are **observed
   manufactured monotone trends among three chosen levels**,
   not proof of global monotonicity or material calibration.
4. **No full-field instability inference:** no case failed the
   original energy, force, restart and Jacobian guards, but the
   displayed subset has no local stress, displacement map,
   fault/contact opening or per-scenario residual distributions.
   All eight outcomes are on two **different physical extents**,
   not comparable mesh refinements of the same area.

**Important:** An RMS difference in velocities is not equal to a
pointwise or overall slowdown percentage. A maximum displacement
is not an integrated strain or geological plate displacement prediction.

## Consequence for truly global G2 verification

The first global surrogate has **66,435 plate-local material views**,
**132,870 potential EN DOFs**, and avoids a dense ~**131.54 GiB** matrix.
The sparse CSR scalar graph is a feasibility check only, with
**5,750,236 B** operator storage and **14** CG iterations for
`(I+0.05L)x=b`. None of these are actual spherical P1 FEM
constitutive G2/creep solver numbers.

**NEXT:** take the *same* source spherical P1 element tangent and
force/work conventions used in 8×8/16×16 and assemble a sparse
or matrix-free global version (one plate-local DOF per material view),
with explicit contact separation and source SHA. Confirm
dense/sparse `Kx` and `xᵀKy` parity on both regional extents,
symmetry, null modes, positive semidefiniteness, force/torque
and virtual-work identities before a single global synthetic static
solve. Only after that succeeds discuss bounded global
manufactured 100-/1000-year integration, fixed-extent spatial
refinement and separate contact alternatives.

**All physical gates unchanged:** no original mineralogical wet/dry
law, mechanical LAB, crust pore state, natural mantle traction,
GPE closure or G4 actual mass/thermal transport has been supplied.
`D-024=ACTIVE`; `physical_T1=null`; no HistoryStore promotion.

```text
REGIONAL_ROBUSTNESS_8_CASES=PASS_SOURCE_OPERATOR
REGIONAL_ETA_ABSOLUTE_IDENTIFIABILITY=FALSE_FOR_CURRENT_CONSTRUCTION
GLOBAL_SPARSE_GRAPH_FEASIBILITY=PASS_FAIR
GLOBAL_G2_SPARSE_FEM_ASSEMBLY=PENDING
GLOBAL_MANUFACTURED_100_1000Y=PENDING
PHYSICAL_T1=null
D_024=ACTIVE
```
