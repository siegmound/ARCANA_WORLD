# R3.15 Full Late-Cenozoic Secular Biology Evidence Audit

Stage: **v0.6D1-R3.15**

Canonical replay evidence received from the user:

- 30.0 Ma -> 0.25 Ma
- 238 fixed biology intervals at 125 kyr
- verdict `PASS_CANONICAL_R315_30MA_TO_250KA_H0_LATE_CENOZOIC_SECULAR_BIOLOGY__PRE_C2_200KA_BRIDGE_CHECKPOINT_READY`
- final species: 134
- final components: 295
- final population: 1218.3485572325976
- event delta: remap 216, coalescence 45, fission 126, speciation 23, ordinary extinction 0
- CHA-1 delta 0; lifecycle-thaw delta 0
- peak q 0.05161661899812446
- final q max 0.04765910934404694
- final q headroom 0.03234089065595306
- clipping steps / contacts 0 / 0
- adaptive clock used as biology timestep: false
- C2 200--120 ka bridge crossed: false
- next nominal 125 kyr biology step crosses the 200 ka bridge: true

Canonical checkpoint hashes:

- JSON `4fb4ffdd711b7a5439ffff15a0a6f381e42ca560b00a2338d70edb77d848bcf6`
- NPZ `f8e79ea862de6c48f01784c727ca15abf9d8fd53b07f47d1aaab5bf589ee5692`
- canonical summary `d50c157acd51ac9c0023d810e75bd775ff9ae28740b887de7621d84334535d1f`

Independent evidence-only post-run audit performed on the uploaded checkpoint: **234/234 PASS**.
It reloaded the restartable state, recomputed event totals and deltas against the 30 Ma R3.13 checkpoint, recomputed q/S/population invariants, checked every NPZ array for expected shape and finiteness, verified all scheduler/governance guards, and performed a fresh save->load->compare roundtrip.

Full inherited regression: **312/312 PASS** in non-overlapping pytest groups.

Interpretation guard:

R3.15 does not authorize a 250 ka -> 125 ka ordinary biology step. The next nominal 125 kyr interval crosses the C2 bridge beginning at 200 ka. R3.16 must define and audit a multirate coupling rule. The C2 200--120 ka bridge remains replay-safe boundary continuation, not sealed high-resolution historical glacial chronology.
