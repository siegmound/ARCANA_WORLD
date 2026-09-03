# R3.16-R3 — Runtime A1 NpzFile Contract Repair Audit

## Trigger
The real Windows canonical R3.16 run reached `r38.advance_state()` and failed at `a1.files` because `validate_parent_r315_authority()` propagated the R3.14 provider-oriented A1 `dict` into the sealed R3.8 runtime.

## Root cause
R3.14 intentionally loads `FULL_A1_REFERENCE_210_0Ma.npz` into a plain mapping for late-Cenozoic provider construction. R3.8 predates that provider layer and has a concrete container contract: it checks optional `lat`/`lon` channels through `a1.files`. The R3.15 canonical script independently reopened the NPZ, so it never exposed this type mismatch. R3.16 parent validation reused the provider dict and therefore did.

## Repair
R3.16 now reopens the **same sealed A1 NPZ authority** specifically for the R3.8 runtime boundary and requires the `NpzFile.files` contract plus the `age_ma`, `lat`, `lon`, and `population` channels. R3.14 remains unchanged and continues to own its provider-oriented dict representation. R3.8 remains unchanged and its fail-closed concrete contract is preserved.

The canonical runner additionally fails early if the returned runtime A1 does not expose `.files`.

## Scientific effect
- A1 data: unchanged; same file authority.
- C2 provider: unchanged.
- R3.8 equations: unchanged.
- Biology cadence: unchanged at 125 kyr.
- Gene-flow cadence: unchanged.
- Lifecycle gates: unchanged.
- Environmental exposure integration: unchanged.

This is a runtime container/binding repair only.

## Verification evidence
- R3.16 unit/regression: 11/11 PASS.
- R3.15 regression: 12/12 PASS.
- R3.14 binding/portability regression: 13/13 PASS.
- Focused total: 36/36 PASS.
- Formal candidate audit: 318/318 PASS.
- Full-path synthetic bridge proof using the real R3.15 250 ka checkpoint and real A1 NPZ container reached `r38.advance_state()` and completed one 125 kyr macro-step to 125 ka with 150 C2 exposure segments consumed.
