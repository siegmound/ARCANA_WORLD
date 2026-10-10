# SI1/BW1 F2-B D1 — DOF and permutation provenance contract

**Status:** `DESIGN_COMPLETE_PENDING_ATTESTATION`\
**Scope:** provenance design for the existing non-canonical SI1/BW1 reordered engineering input and the original F2A-V assembly-only run.\
**Current authorization:** design and read-only evidence review only. This document does not authorize a validator run, Fair, MPI, Solver, factorization, gauge, simulation, canonical mutation, commit, or push.

## 1. Decision and claim boundary

The available files and source define a concrete candidate chain from an F2A-V raw matrix index to a reordered FEG node, ShellSet's component slot, and an original FEG node. The F2A-V staged FEG and runtime package have the same SHA256 identities as the BW1 derived pair. The original F2A-V manifest's eight staged-input entries were individually checked against the files in its `run_f2av/INPUT/` directory; all eight digests match.

This establishes that the required provenance material is present and internally linked by exact file identity. It does **not** constitute a fresh exhaustive content validation of every permutation/FEG/runtime record, nor prove a geographic meaning for ShellSet's local component basis. The sealed F2A-V result and diagnostic contract continue to say `DOF_MAPPING_UNVERIFIED`. Keep that status for all uses requiring the missing independent end-to-end attestation; do not attach geography, plate identity, or physical interpretation to census indices.

The BW1 report remains `BLOCKED_BW1`: its recorded blocker is the absence of an enforced KSize-only Fair preflight runner. The F2A-V original result remains `BLOCKED_F2AV_QUALIFICATION`. D1 changes neither result.

## 2. Artifact inventory and identities

Paths under `outputs/` are repository-relative. The original run bundle below is an external evidence locator and is not itself a portable identity.

| Role | Exact path | SHA256 | Size / structure |
|---|---|---|---|
| Permutation artifact; contains both maps | `outputs/r6_si1_bandwidth_bw1/permutation/BW1_NODE_PERMUTATION_V1.json` | `a0895fd99d3a356de276bd700af1564d951fcb9e4533e103e061aed15a8441e7` | 1,396,149 bytes; schema `R6_SI1_BW1_NODE_PERMUTATION_V1`; `node_count=64442`; two 1-based integer arrays, each length 64,442 |
| Reordered FEG | `outputs/r6_si1_bandwidth_bw1/derived/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg` | `18d78ec0c3382e0408f11f7b9826f5f22db7e6d921884c3375600fb2d447ffd1` | 10,151,672 bytes; 64,442 node records, 128,880 triangles, zero fault elements |
| Reordered runtime package | `outputs/r6_si1_bandwidth_bw1/derived/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat` | `a68c073011b2cb7782b760d5ff43b010610eaaddec731d5b39172c6b08294a31` | 77,832,708 bytes; 64,442 node records, 51 fields including record node ID |
| BW1 input manifest | `outputs/r6_si1_bandwidth_bw1/manifests/BW1_INPUT_MANIFEST.json` | `63099f944c5379172f74831e08991c3dbe3315967de9bffbb639258448749732` | 1,111 bytes; manifest lists derived files, permutation, and staged copies |
| BW1 report | `outputs/r6_si1_bandwidth_bw1/reports/BW1_REPORT.json` | `944dfd039756d8b6cd9faf7ad1907fd034bac09cdbfd563f2385838b2eabc070` | 4,704 bytes; records artifact hashes, counts, validation claims and `BLOCKED_BW1` |
| BW1 staging contract | `outputs/r6_si1_bandwidth_bw1/fair_staging/BW1_FAIR_PREFLIGHT_CONTRACT.md` | `3270c536eb7b54d3b8adf063e62dca695f4112d5d0ebcfeffc5f64d0e93b6ec2` | 1,653 bytes; contract only, not evidence of a Fair execution |
| Original F2A-V evidence manifest | `F:\corsiiiuu\Magistrale\Arcana\F2AV_RECOVERY_INPUT\df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z\BW1_F2AV_ARTIFACT_MANIFEST.json` | `e59a1a31a450c7028b7a405cd6641454d9d67e082c7b62bd2132a0e452852854` | 13,588 bytes; membership states all regular bundle files except the manifest |
| Original F2A-V result | `F:\corsiiiuu\Magistrale\Arcana\F2AV_RECOVERY_INPUT\df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z\BW1_F2AV_RESULT.json` | `02d7d8bd55dbe620f25772212be3db3f3a0c34ccf7e7c61b01af7994b5205fed` | 13,971 bytes; execution source commit `df670c8c4faaed641997f5c4bdb701e2ba0afc7d`; original result remains blocked |

The BW1 report identifies its source as branch `r6/si1-bandwidth-bw1`, HEAD `f838abaeb95d7cfc0f690bf6d120101744e9e00d`, SciPy RCM, and original input identities FEG `34b81c0df350d3b9a4c7df526c9171c89fe2d44d7e17b8662f5a92a9ee4c40b6`, runtime `2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584`.

### F2A-V staged input set

Original evidence directory: `F:\corsiiiuu\Magistrale\Arcana\F2AV_RECOVERY_INPUT\df670c8c4faaed641997f5c4bdb701e2ba0afc7d-20261010T131529Z`. Paths below are relative to that directory. The manifest-listed byte counts and SHA256 values were compared with each actual staged file; each comparison matched.

| Staged path | Bytes | SHA256 |
|---|---:|---|
| `run_f2av/INPUT/ARCANA_PLATE_OUTLINES.dig` | 127,189 | `6fdd149b2e5c8cc84992aa6a55b807867a27bc07bc0d78fdccf7b8bc4465525f` |
| `run_f2av/INPUT/InputFiles.in` | 967 | `d357d5a939a65fc9b8feee0cb0ca2fa0dba243a576249b5781323021ed751ab7` |
| `run_f2av/INPUT/ListInput.in` | 43 | `bb770c1ec132c4d6bee3ee2b12ce5d0dbbafd07147c435162acad2253606a49c` |
| `run_f2av/INPUT/R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat` | 77,832,708 | `a68c073011b2cb7782b760d5ff43b010610eaaddec731d5b39172c6b08294a31` |
| `run_f2av/INPUT/R6_PRE_ORBDATA_SHELLSET_T0_FEG_V1.feg` | 10,151,672 | `18d78ec0c3382e0408f11f7b9826f5f22db7e6d921884c3375600fb2d447ffd1` |
| `run_f2av/INPUT/SI1_ENGINEERING_REFERENCE.in` | 3,887 | `c07834e17d9c6e21bad0d7cd81af20e8a670e0ae9ed481f999c881129ee4a89e` |
| `run_f2av/INPUT/SI1_NO_VELOCITY.bcs` | 52 | `e6fdc6c7d8050df65fb975e79147e981d164e527af948de64f8f7e825becb121` |
| `run_f2av/INPUT/SI1_UNUSED_PLATE_PAIR.dig` | 38 | `991316ececbe0042d8e2b6e6b06e819f9dd00f0bf65a3832fd4e3130cad88268` |

In particular, the actual staged FEG/runtime hashes equal the BW1 derived and BW1 fair-staging copy hashes. This connects F2A-V to the reordered pair by bytes, not by a path or a hash-shaped string alone. It does not independently prove all transformed content is semantically correct.

The local complete recovery manifest is a separate derived artifact, SHA256 `3d1f794f3d642450b59bd484f4802a2c2d93f08c872b80e991ebb20352dd637f`; it does not replace or rewrite the original F2A-V manifest or blocked result.

## 3. Numbering relation

Let `o` be a 1-based node ID in the original governed FEG and `p` a 1-based position in the reordered FEG/runtime pair.

- `new_to_old[p] = o`: reordered position `p` carries original node `o`.
- `old_to_new[o] = p`: original node `o` is placed at reordered position `p`.
- The intended inverse equations are `new_to_old[old_to_new[o]] = o` and `old_to_new[new_to_old[p]] = p`, with array indexing interpreted 1-based.
- Reordered FEG node record `p` retains the original node's coordinates and other nodal tokens but writes record ID `p`.
- Each original FEG triangle node ID `o` is rewritten to `old_to_new[o]`; triangle order and local orientation are intended to remain unchanged.
- Runtime record `p` is copied from original runtime record `new_to_old[p]`; field 1 is rewritten to `p`, while fields 2–51 are intended to remain exact text.
- F2A-V raw matrix DOF index `q` maps to reordered node `p = floor((q+1)/2)`, component slot 1 for odd `q` and slot 2 for even `q`; the original node candidate is then `new_to_old[p]`.

The actual permutation JSON states the orientation above. Its first entries are `new_to_old=[179,178,177,176,175,174,173,172,...]`; `old_to_new` begins `[358,64437,177,176,175,174,173,172,...]`. As a content spot-check, reordered FEG record 1 has the same non-ID tokens as original FEG record 179, and reordered runtime record 1 has the same fields 2–51 as original runtime record 179. Spot-checks are illustrative, not exhaustive proof.

The F2A-V census indices are raw indices from this reordered assembled matrix. Until the exhaustive chain is attested, leave them as raw algebraic indices. Do not attach plate, geographic, or boundary semantics.

## 4. Required exhaustive provenance checks

The subsequent D1A offline attestation must record tool/version, source commit, exact inputs, outputs, and hashes, and establish all of the following from file contents:

1. **Identity and scope:** verify each original and derived file against its authoritative manifest; verify the F2A-V evidence membership/manifest and original run result; preserve the original blocked decision. Reject missing files, extra substituted staged inputs, unsafe paths, or any mismatch.
2. **Permutation:** parse both arrays as integers; require exactly 64,442 entries each, values exactly `1..64442` once each, and both inverse equations for every node. Bind the permutation arrays to their serialized-map digest and the permutation artifact SHA.
3. **FEG records:** parse header/counts and record boundaries; require node IDs exactly `1..64442` in derived order. For every `p`, compare its non-ID node fields against original record `new_to_old[p]`. For every triangle and every vertex, require the derived ID to equal `old_to_new[original_id]`. Verify triangle order/local orientation, fault framing and all non-node-indexed fields; invert the transform and require a byte-identical original FEG round trip or report precisely why byte identity is not applicable.
4. **Coordinates:** for every reordered node, compare all coordinate tokens against the original record selected by `new_to_old`; compare numeric parsed coordinates as an additional check without replacing exact-text preservation. Do not interpret ShellSet component velocities as east/north or infer longitude/latitude axes from this equality.
5. **Runtime package:** require identical header/schema, 64,442 records, 51 fields per record including node ID, derived ID `p`, and fields 2–51 exactly equal to original row `new_to_old[p]`. Recompute and reconcile branch/support summaries, including the reported 2,697 mixed-support rows. Reverse-map rows and require exact original package reconstruction where the format permits.
6. **Staging and run link:** require both staged copies to be byte-identical to their corresponding BW1 derived files and match all eight original F2A-V manifest entries. Tie the original F2A-V result, execution commit, stop marker and census files to that same manifest. Never use the recovery implementation HEAD as the historical execution source.
7. **Census linkage:** after checks 1–6 pass, translate each census DOF pair via `q → (p, component) → original node`. Keep the original census unchanged; create a separately hashed mapping companion if needed. Any missing, duplicate, non-integer, out-of-range or ambiguous index fails closed.

The existing BW1 source contains these intended checks: `validate_permutation`, `_remap_feg`, `_roundtrip_check`, runtime row remapping, and `validate_runtime_package`; its Fair preflight cross-checks FEG connectivity/coordinates and runtime fields. The stored BW1 report records `is_bijection`, `inverse_exact`, `repeat_invocation_identical`, `feg_roundtrip_byte_identical`, runtime-field preservation and zero canonical changes as true. D1 has inspected those implementations, report claims, real artifact structure and hashes, but has **not** rerun the exhaustive checks; the report is evidence to verify, not a substitute for the attestation.

## 5. Component basis is a separate authority question

ShellSet source uses `x=2*node-1` and `y=2*node` in continuum assembly. This proves the ordering of two algebraic component slots per node. It does not by itself prove how those slots map to a named geographic basis at every spherical location, especially near coordinate singularities/poles. A valid node/permutation mapping and a valid component/geographic-basis mapping are separate claims.

Required status fields in any companion result:

- `node_permutation_mapping`: `PASS` only after checks 1–7's node-related checks pass;
- `raw_dof_component_slot_mapping`: `PASS_SOURCE_ORDER_ONLY` for odd/even slot order, unless the exact basis is independently demonstrated;
- `component_geographic_basis_mapping`: `DOF_MAPPING_UNVERIFIED` until ShellSet's basis construction and orientation are connected to the exact staged coordinate records;
- `census_geographic_or_plate_attribution`: `PROHIBITED` while the preceding basis mapping is unknown.

No map or remapping may alter FEG connectivity, coordinates, runtime values, original evidence, or canonical WORLD_HISTORY as part of this design.

## 6. Fail-closed outcomes

Any hash/manifest mismatch, incomplete or non-bijective map, failed inverse, FEG/runtime record discrepancy, altered triangle ordering/orientation, staging mismatch, unverifiable historical run link, missing source file, or parser ambiguity yields `DOF_MAPPING_UNVERIFIED` and blocks census attribution. A node mapping pass with an unresolved local basis remains partial; it is not a complete physical/geographic DOF map.

The audit must never repair inputs, regenerate the permutation, replace the original evidence, normalize a census in place, alter a coefficient, add a gauge, or update canonical state. Any generated companion evidence must be separate, immutable, manifest-hashed, and explicitly linked to the original blocked F2A-V evidence.

## 7. Gate and next control

D1 design is complete because it defines the file chain, exact current identities, transformation semantics, exhaustive acceptance checks, and failure states without promoting unresolved meaning. **Next required control: F2B-D1A**, a separately authorized, read-only, exhaustive content verification/attestation of the identified permutation, complete FEG and runtime pair, and sealed F2A-V staging link. D1A's scope is the node/permutation/raw-component mapping and its evidence chain; geographic local-basis verification is a distinct follow-up question and must not be implied by D1A. Until the applicable checks pass, keep `DOF_MAPPING_UNVERIFIED`, do not geolocate the ten census pairs, and do not authorize Solver, Fair, MPI, factorization, gauge, mechanics, or canonical publication.

## 8. Source references

- `src/arcana_worldsim/r6/si1_bandwidth_bw1.py`: permutation construction/inverse validation (lines 51–78); FEG mapping and round-trip (142–174); runtime remap, report identities and output write (232–283).
- `scripts/r6_si1_bandwidth_bw1_fair_preflight.py`: artifact SHA checks and FEG/runtime content checks (350–392); recorded mapping and input indexing scope (418–443).
- `external/ShellSet-v1.1.0/src/MOD_Shells.f90`: component slot assignment in continuum matrix assembly (1493–1512); KSize uses node connectivity and fault records (5266–5368); FEM calls Solver after assembly and boundary conditions (3630–3735).
- `docs/arcana/SI1_BW1_F2AV_DIAGNOSTIC.md`: raw-index and mapping limitation (sections “DOF mapping” / “Mapping limits”).
- `contracts/R6_SI1_BW1_F2AV_DIAGNOSTIC_CONTRACT_V1.json`: mapping artifact links, fallback status, and prohibition on geographic/plate inference (`mapping_policy`).
- `docs/arcana/SI1_BW1_F2B_PREFLIGHT_DESIGN.md` is the current design reference, added by the verified fast-forward to `595ed74788c3fa06cb4371affef121aacefb6670`. It is design-only and keeps D1 attestation separate from geographic-basis adjudication; it does not report that D1 content checks have been executed.
