# R6 PRE_ORBDATA A0.7 implementation report

**FEG numerical-support decision:** `R6_PRE_ORBDATA_FEG_NUMERICAL_SUPPORT_COMPLETE__SHELLSET_SUCCESSOR_PATCH_READY`

The canonical mesh materialization now covers all **64,442** nodes. All **64,442** have valid nonzero heat-flow support; **0** are UNKNOWN. Exactly **2,697** nodes have mixed incident physical-domain support. Each uses the lexicographically first incident canonical cell, sorted by `(row, column)`, as a `NUMERICAL_DERIVED_SUPPORT` owner. Its heat-flow value is copied exactly. No averaging, interpolation, or smoothing occurs, and the selected owner is not a canonical physical node domain.

Each mixed-node lineage record preserves all incident physical domain IDs, its mixed-support flag, owner cell/domain, and owner-bound runtime fields. The same owner cell is explicitly bound for heat flow, runtime branch/domain, derived thermal profile, lithosphere geometry, and material configuration. `lineage` is the per-node list; `source_lineage` is the separate global provenance dictionary. ShellSet must consume that owner sidecar or prove identical ownership and must not reclassify nodes from latitude/longitude.

The materializer and replay identity use `CANONICAL_UTF8_TEXT_LF_SHA256` for text inputs. Config V1 records this hash policy and contains canonical hashes for its textual source authorities. The downstream replay and implementation report identities have been regenerated. Two consecutive canonical materializations produced identical artifact bytes.

The focused regression suite passed: **18 passed** with `python -m pytest -q tests/test_r6_pre_orbdata_implementation.py`. It covers the governed HWR error code, source-authority canonical hashes, mixed-node owner selection, lineage separation, owner-consistent runtime bindings, and authoritative projection counts.

The owner-aware ShellSet successor **contract** is ready. The exact qualified ShellSet source tree is absent from this checkout, so no source patch was constructed. Ubuntu FAIR qualification and stock regression remain mandatory. This does not set `PRE_ORBDATA_ready`, authorize OrbData/SHELLS, or promote canonical T0.

No OrbData/SHELLS was run, no scientific architecture or values were changed, and no commit, push, or staging operation was performed.
