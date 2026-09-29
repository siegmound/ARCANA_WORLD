# R6 PRE_ORBDATA ShellSet successor patch provenance

The historical patch remains unchanged at `patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch` (SHA-256 `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`). It is a baseline/oracle only; its FAIR qualification does not qualify a successor.

The requested qualified parent is `62fd474f229b2676fd9d39c5def45137d22d2481`. That object and its source tree are absent from the current repository. The exact `OrbData5.f90`, `MOD_Data.f90`, `MOD_ShellSet.f90`, and `ShellSetMain.f90` files therefore cannot be used to construct and verify an applicable patch against that commit. No successor patch artifact has been fabricated.

The successor contract is now ready. Each FEG node carries a numerical owner cell chosen by `LEXICOGRAPHIC_FIRST_INCIDENT_CELL`; for mixed support the sidecar preserves all incident physical domain IDs and marks the support mixed. This owner is numerical derived support, not a canonical physical node domain.

The exact same owner must bind heat flow, runtime domain/branch, thermal profile, lithosphere geometry, and material configuration. The successor must consume the owner sidecar explicitly or prove identical ownership across every quantity. ShellSet must not independently reclassify from latitude/longitude. This requirement does not constitute a ShellSet source patch: the pinned source is absent. Patch construction/review plus Ubuntu FAIR qualification and stock regression remain required when that exact source is available.

The full provenance record is in [R6_PRE_ORBDATA_SHELLSET_SUCCESSOR_PATCH_PROVENANCE.json](R6_PRE_ORBDATA_SHELLSET_SUCCESSOR_PATCH_PROVENANCE.json).
