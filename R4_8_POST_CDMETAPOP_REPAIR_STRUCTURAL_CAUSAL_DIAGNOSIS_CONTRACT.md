# v0.6D1-R4.8 — Post-CDMetaPOP-Repair Structural Causal Diagnosis

R4.7 preserved one structural disagreement after dynamic-forcing parity repair: H0_POST_CHA1_RECOVERY × population_persistence, PRIMARY CDMetaPOP J09.

R4.8 does **not** change R3.11, replay the canon, or retune CDMetaPOP. It diagnoses a remaining semantic confound: R4.7 configures each CDMetaPOP patch with `N0 ≈ 0.5 × K_start`, so the 5-generation absolute population response contains both environmental forcing and relaxation toward carrying capacity.

The diagnostic control uses the exact J09 contract and exact four frozen seeds, with identical runtime, habitat start, migration/gene-flow parameters and initial N0 policy. The sole change is `dynamic_end_support_ratio = 1.0`, keeping K constant through the existing CDClimate knots.

The causal external-engine response is the paired ratio-of-ratios:

`(dynamic_final/dynamic_initial) / (neutral_final/neutral_initial)`.

ARCANA's corresponding causal reference is obtained from R4.6:

`canonical_65p5_to_55_ratio / reference_population_hold_counterfactual_ratio`.

R4.8 uses the already-frozen R4.4 5% neutral band and q10–q90 robustness rule. It preserves the R4.7 matrix as immutable parent evidence and only chooses the appropriate R4.9 diagnostic/evidence path.
