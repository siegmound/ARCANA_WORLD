# R6 C11 — FAIR operator receipt and archived runners

2026-11-27. Scenario: `C10_R8_DIORITE2_KINEMATICALLY_CONTROLLED_FREE_SLIP_V1`.

This is a transcription of operator-supplied terminal receipts, not a new FAIR execution or an independent rehash of FAIR archive members by ChatGPT. The three original runner files are published byte-identically under `experiments/r6_thermo_provider_pilot_v1/`. Execution source remains pinned to C10 `901cbb4a38916190df6a881bb561b6558dd997dd`; publishing scripts does not change that execution source.

| Stage | Archive under ARCANA_WORLD_EVIDENCE/R6 | Manifest SHA-256 | Exit |
|---|---|---|---|
| C10 | R6_THERMO_C10_CONTROLLED_REGIONAL_MECHANICAL_CONFIGURATION_NEW01 | 4e57523471281983aa228ddb82cd582f09c76129eeeb694460f0cfd2ad9108d7 | 0 |
| C11A | R6_THERMO_C11A_OPERATOR_ASSEMBLY_NEW01 | 58914c9318b2ac342bf13fef89fc6e2c7a4d3b1cc54e057b9abe549a513de5a3 | 0 |
| C11B | R6_THERMO_C11B_FIRST_CONTROLLED_SOLVE_NEW01 | c667fdbfde09fe1e15cd157ac8ed5be259db7dde5f54566666c4faebecd67b40 | 2 |
| C11BR1 | R6_THERMO_C11BR1_CONVERGENCE_NEW01 | ab2c576dee82f9feb797568d1ec7ee873a15523877140427df11f3bff755e974 | 0 |

C10: 743/743 regressions in 27.43 s. C11A: 98 free DOF, rank 98, condition 46.59366422338433; constrained rank 162, condition 48.22601672597663; no solve. C11B: native convergence after 22 iterations, free residual 0.021913754132917247 and work defect 0.004437210771905248; diagnostic blocked. C11BR1: native convergence after 79 iterations, scoreB 4.617380758272628e-7, stress refresh 1.2073465162484113e-5, free residual 1.291141947924418e-5, work defect 5.089725979620279e-6, maximum linear backward error 1.163382075045484e-16, quadrature relative defect 6.393033280337055e-14, final free condition 2558.8037682627883. Zero negative relative stress power densities and zero tangential basal eta. Numerical screen passed; natural exterior, cap activation, sensitivity, independent traction/work closure and physical acceptance remain open.

Status: `C11BR1_CONTROLLED_SOLVE_NUMERICAL_SCREEN_PASS__SENSITIVITY_REQUIRED`.

## Exact runner hashes (SHA-256)

```text
af9afbd8d337f00e8d23c2681c25b2542a788b10302d0c3cafef0c888845780c  arcana_c11a_assembly.py
7b17dc4f7371a436b24f94672a58ee82797132b0f3a6eecf6925652afde9cc2b  arcana_c11b_first_solve.py
ba76597ceb1d40eca8939f21764e4667048d2b4428430bd820efe11007a8d65b  arcana_c11br1_convergence.py
```

The archival runners must be invoked from the clean C10 checkout, not from a later HEAD. Keep the three scripts together in an external directory or a separate runner checkout. Fetch the publishing branch and use git show to extract the three exact files. Do not rerun against existing evidence directories. No further solve or time advance is authorized by this receipt.

Next: C11-C controlled sensitivity and cap-activation audit, followed by physical acceptance review and G4 only if justified. D-024/D-025 remain active. No canonical natural material placement, no physical T1, no WORLD_HISTORY production.
