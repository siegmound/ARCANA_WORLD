# R3.12 Full Post-CHA1 Diversity-Recovery Evidence Audit

Status: **SEALED**

Verdict: `PASS_R312_CANONICAL_POST_CHA1_61_TO_46_H0_DIVERSITY_RECOVERY__46MA_RESTART_BOUNDARY_SEALED`

## Canonical boundary

- start: 61.0 Ma (`POST_CHA1_5MY_RECOVERY`)
- end: 46.0 Ma (`POST_CHA1_20MY_DIVERSITY_RECOVERY`)
- biology cadence: 125 kyr
- biology steps: 120
- Deep biological coupling: OFF
- CHA-1 reapplication: none
- lifecycle thaw reapplication: none

## Outcome

- species: 95 -> 104
- components: 236 -> 223
- population: 1433.787404643522223
- remaps: 104
- coalescences: 19
- fissions: 15
- speciations: 11
- ordinary extinctions: 2
- clipping steps / contacts: 0 / 0
- peak q: 0.04694482744771825
- final q max: 0.04568960003113533
- final q headroom: 0.03431039996886467

## Diversity interpretation

The recovery metrics are descriptive, not acceptance targets. At 46 Ma the model contains 104 species, equal to 34.10% of the pre-CHA1 305-species reference. The net recovery relative to the +0.5 Myr boundary is 11 species, or 5.19% of the 212 direct CHA-1 species losses.

Guild-level richness at 46 Ma:

- guild 1: 50 species (43 at 61 Ma)
- guild 2: 1 (unchanged)
- guild 3: 6 (unchanged)
- guild 4: 42 (38 at 61 Ma)
- guild 5: 5 (unchanged)
- guild 6: 0 (2 at 61 Ma; both lost by ordinary background extinction)

The two ordinary extinctions are `APX_005` at 57.0 Ma and `APX_001` at 56.5 Ma.

## Speciation provenance

All 11 R3.12 speciations are **not matched to the founder state already active at the 61 Ma boundary**. Therefore none is classified as R3.11 founder carry-over. This is structural timing evidence only: it does **not** by itself prove CHA-1 empty-niche causation.

First R3.12 speciation: 56.0 Ma.

## Numerical / lifecycle closure

- formal independent audit: **218/218 PASS**
- full inherited regression: **281/281 PASS**
- immediate post-run regression: **44/44 PASS**
- population non-negative: PASS
- population on inaccessible cells: exactly zero
- reduced segregation potential `S`: symmetric, zero diagonal, non-negative within tolerance
- q ceiling 0.08 respected with positive headroom
- independent final checkpoint load-save-load identity: exact
- summary/checkpoint SHA-256 bindings: PASS

## Canonical hashes

- summary: `404c43c80af5f10ff1d00ad0cfc51f21abbe3e566e3d040e4faa2e84d33a6230`
- checkpoint JSON: `6189f16fd3d7b390ad33afb57eaa36fef0bdbcf7f1498fa7396d3d1f81843269`
- checkpoint NPZ: `92b410ce3258c44ba0f4b911776628d880fbe5a5fe3be3b9b6fe13dc34973948`
- returned evidence ZIP: `85ace28f79e7de2ec9119fe1afd4c1a8e57d517c05132f3f6281addb6291d43c`

## Seal conclusion

R3.12 is authorized as the canonical H0 restart boundary at **46.0 Ma**. No claim of Earth-analogue recovery rate or CHA-1 causal attribution is sealed by this stage.
