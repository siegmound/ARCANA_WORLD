# ARCANA WorldSim v0.6D1-R5.0
## Selective High-Resolution Nested Replay and Arbitrary-Age State Query Contract

R5.0 is a **derived-state query layer** over the sealed WorldSim. It does not create a second canonical simulator and it does not reopen R4 multi-engine revalidation.

## Authority

1. Governance baseline: post-`v0.6D1-R4.56` SEALED with exact verdict
   `ARCANA_MULTI_ENGINE_23_JOB_FULLY_REVALIDATED_WITH_EXACT_INTEGRITY_AND_GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM`.
2. Population authority: sealed R3.28 high-resolution replay.
3. Holocene environment/resource authority: sealed R3.33 landscape.
4. Flora operational-taxon authority: sealed R3.34 producer landscape.
5. Fauna scope in R5.0 is deliberately partial: the sealed R3.33 24 ecological-partner registry and interaction trajectories. R5.0 **does not invent a global fauna raster**.

All scientific parent files consumed by the resolver are exact-SHA256 pinned in `SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_0.json`.

## Query contract

A query contains:

- `query_id`
- `target_age_ka`
- requested domains
- optional native World1 grid window
- `resolution_profile = NATIVE_90X180_WITH_DEME_DETAIL`
- interpolation permission
- extrapolation forbidden
- canonical write forbidden

R5.0 does not synthesize a finer spatial grid. "Higher resolution" in this first implementation means selective temporal/detail recovery from the already sealed high-resolution products, not visual upsampling.

## Resolver rule

Each product resolves independently.

- If the target age exists in the parent authority, R5 returns it as `EXACT`.
- Otherwise R5 may use only bracketing states that surround the target age and records both parent ages and interpolation weight.
- R5 never extrapolates outside the authority interval.
- No one interpolation rule is silently applied to every domain.

### Population

R3.28 `species_summary` is authoritative on its 280-state age axis. At 17.5 ka the population summary is therefore exact.

Detailed spatial/deme state is exact when a stored R3.28 snapshot or CHA-2 detail state exists. Between stored detailed snapshots, R5 performs a deterministic bounded spatial reconstruction:

- continuous fields interpolate between the two sealed detailed states;
- longitude follows the shortest cyclic path on the 180-column grid;
- no new deme slots are created;
- total population is constrained to the target R3.28 population summary;
- active-deme count is constrained to the target R3.28 summary;
- no random movement, demographic update, selection, mutation, or external-engine call occurs.

This is a **derived spatial reconstruction**, not a canonical historical state rewrite.

### Environment / surface paleogeography / climate / hydrology / resources

R3.33 provides nine 90x180 sealed environmental anchor states at 20, 15, 14, 13, 12, 11, 10, 5 and 0 ka. Between those anchors R5 uses bounded interpolation and records provenance.

R5.0 surface-paleogeography coverage is limited to sealed land-fraction and sea-level support; it is not a deep geology/lithology claim. Hydrology coverage is likewise limited to the sealed hydroclimate-resource and coastal-edge fields; no river network is invented.

### Flora

R3.34 provides 36 anonymous functional operational producer taxa and four landscape variables on the same nine age anchors. R5 interpolates only between those sealed anchors. It does not convert operational taxa into named retrospective species or phylogeny.

### Fauna

R5.0 exposes the sealed R3.33 24 animal ecological-partner candidates and their interaction trajectories. It explicitly marks this as partial fauna coverage and makes no global abundance/distribution raster claim.

## Demonstration contract

The integrated R5.0 run must execute both:

1. **20 ka** — exact population summary, exact population detail, exact environment, exact flora and exact fauna-partner trajectory.
2. **17.5 ka** — exact R3.28 population summary; population detail reconstructed only from 20/15 ka detailed snapshots; R3.33 environment, R3.34 flora and R3.33 fauna trajectories bracketed only by 20/15 ka.

The run must prove:

- exact parent hashes unchanged before/after;
- no full 210 Ma -> 0 rerun;
- no external-engine execution;
- no temporal extrapolation;
- no canonical write;
- no Deep biological coupling;
- deterministic repeated 17.5 ka semantic state hash.

A run made with the explicit developer-only missing-R4.56 allowance is `NON_SCIENTIFIC_DEV_VALIDATION` and cannot seal R5.0. The normal PowerShell runner never enables that allowance.

## Final seal closure

The final R5.0 seal is part of this same substantive stage; no R5.0A/B administrative split is introduced.

The seal must fail closed unless all of the following remain true at runtime:

- post-R4.56 multi-engine closure is independently discoverable and semantically verified;
- all 9 immutable R3.28/R3.33/R3.34 parent artifacts retain their pinned SHA-256 values;
- the integrated scientific candidate remains 23/23 PASS and `scientific_candidate_eligible=true`;
- the candidate output manifest contains exactly the 15 allowlisted R5.0 candidate artifacts and no prior seal artifacts;
- every candidate artifact matches the byte count and SHA-256 stored in that manifest;
- semantic state hashes recomputed directly from the two derived-state NPZ packages remain:
  - 20 ka: `ad0770c10074a5030a74f641ff3852372aab6806089f5512b605a718cb6c5554`;
  - 17.5 ka: `bc70bf068154be48f5d3ffe981d02833f55b8448b59ae3bf9f78d6b34a9313ef`;
- provenance modes remain exact/bounded as authorially accepted by the live scientific candidate;
- no temporal extrapolation, stochastic replay, external-engine execution, full-history rerun, canonical write, or Deep biological coupling occurs;
- deterministic replay-recipe self-hashes remain valid.

The seal freezes the derived-state query capability and demonstrations, not a rewrite of canonical WorldSim history. Local high-resolution refinements remain derived unless separately promoted by future explicit authority.

Final verdict:

`PASS_R50_SELECTIVE_HIGH_RESOLUTION_NESTED_REPLAY_AND_ARBITRARY_AGE_STATE_QUERY_SEALED`
