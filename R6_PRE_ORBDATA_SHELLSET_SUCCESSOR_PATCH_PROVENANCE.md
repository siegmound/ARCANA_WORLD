# R6 PRE_ORBDATA ShellSet successor patch provenance

The historical patch remains unchanged at `patches/shellset/R6_ORBDATA_ARCANA_EXPLICIT_INPUTS.patch` (SHA-256 `e844d78462442a7580469969da8641de9a0992c2a2ee7df0d2f36d6193d3eeb2`). It is a baseline/oracle only; its FAIR qualification does not qualify a successor.

The requested qualified parent is `62fd474f229b2676fd9d39c5def45137d22d2481`. That object and its source tree are absent from the current repository. The exact `OrbData5.f90`, `MOD_Data.f90`, `MOD_ShellSet.f90`, and `ShellSetMain.f90` files therefore cannot be used to construct and verify an applicable patch against that commit. No successor patch artifact has been fabricated.

The successor must preserve ARCANA heat flow and authored geometry, bypass GDH1 and qLim1 mutations for complete ARCANA input only, consume the conservative transient thermal state, enforce Moho T/flux conservation, fail closed on invalid profiles, and leave the legacy path unchanged. A new Ubuntu FAIR qualification and stock regression are required after the exact source is supplied. The full provenance record is in [R6_PRE_ORBDATA_SHELLSET_SUCCESSOR_PATCH_PROVENANCE.json](</D:/corsi/Arcana/ARCANA_WORLD/R6_PRE_ORBDATA_SHELLSET_SUCCESSOR_PATCH_PROVENANCE.json>).
