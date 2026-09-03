# R3.8 Full 150 Ma Checkpoint Evidence Audit

The governed local run completed the fixed 210→150 Ma materialization and the 150→149 Ma direct/restart equivalence gate.

## Result

`PASS_CANONICAL_150MA_CHECKPOINT__R37I_EQUIVALENT__150_TO_149_RESTART_EXACT__POST_PROMOTION_CONTINUATION_READY`

- 210→150 biology steps: 480
- direct 150→149 biology steps: 8
- restart 150→149 biology steps: 8
- sealed R3.7I exposed-state equivalence: PASS
- checkpoint serialization identity: PASS, zero reported error
- direct/restart future-state identity: PASS, zero reported error

## Canonical 150 Ma state

- total population: `1940.1122015319092`
- species: `133`
- components: `454`
- max normalized VA `q`: `0.04594493338329716`
- median normalized VA `q`: `0.0445537006799661`
- cumulative events: 432 conservative paleogeographic support-loss remaps, 14 deme coalescences, 335 deme fissions, 13 speciations.

## Checkpoint identity

- JSON SHA-256: `8a8fbe9da857c6b278c2c8856a4b989a40a0a5ec2087af64a2ce0e9c1a6a2853`
- NPZ SHA-256: `0d253babcd74bdfcf4590bb6f51ac4ce99aabcb8f224d00a4c59fd148021cc32`
- validation summary SHA-256: `58019980b3c28903b9ffd4836f0be9dfc35e0621be764fc974e13974e7117796`

The NPZ materializes 454 components on the 90×180 grid, with the full `454×454×3` neutral segregation-potential tensor plus within-VA, ancestry/LD covariance and adaptive coordinate. Lifecycle registries and pair-state dictionaries are stored in the JSON sidecar.

No scientific constant is changed by this seal. R3.7I remains the scientific runtime authority; R3.8 authorizes the 150 Ma serialized state as the canonical H0 continuation boundary.
