# R6 PRE_ORBDATA A0.7 implementation report

**Decision:** `R6_PRE_ORBDATA_IMPLEMENTATION_PARTIAL__UBUNTU_FAIR_QUALIFICATION_AND_PINNED_ARTIFACTS_REQUIRED`

The two machine-readable V1 configurations bind to the adjudicated A0.6 authority reports and the T0 field package. The deterministic producer now yields 14,258 continental references, 108 governed ridge values, and 50,434 positive-age HWR-2 values. Static checks reproduce the published nominal HWR fluxes, ridge effective thermal index, ocean columns, and continental columns. The 1,072 previously disputed cells use the authorized positive-age HWR-2 branch.

The transient solver and categorical projection logic are implemented. The full 64,800-cell derived heat-flow product was materialized with separate branch and applicability arrays. The required 64,442-node projection could not be materialized because the canonical parent partition NPZ is absent from the configured external-source path. The implementation did not invent a replacement mesh.

The successor ShellSet patch was not fabricated. The required parent commit `62fd474f229b2676fd9d39c5def45137d22d2481` is absent from the local Git object database, and the pinned Fortran source tree is not in this workspace. The historical patch remains unchanged and is baseline evidence only.

New focused tests were added, but pytest could not run because pytest is not installed in the available Windows Python. `py_compile` and direct numerical checks passed. OrbData/SHELLS were not run. No scientific blockers remain; implementation blockers and Ubuntu FAIR actions are listed in the machine-readable report.

The gates remain closed: `PRE_ORBDATA_ready=false`, `OrbData_authorized=false`, no runtime execution or qualification, and no canonical T0 promotion. No commit, push, or staging change was made.
