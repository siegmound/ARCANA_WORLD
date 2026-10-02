# R6 B4 plate-kinematics qualification evidence

This package records a read-only binding of the governed 210 Ma T0 plate-rate realization to WORLD_HISTORY forcing/provenance records. It does not perform temporal evolution, select dt, move geometry, create T1, or run ShellSet/OrbData.

Run from the repository root:

```powershell
python scripts/r6_plate_kinematics_b4_qualification.py
```

The runner verifies the current B4 branch/HEAD and source identities, reads the externally stored T0 and face-partition payloads by manifest path, writes a temporary WORLD_HISTORY store outside this evidence directory, reopens and queries it, then removes that temporary store. External payloads are not copied into this package. The default output directory may be overridden with `--output-dir`; `--work-root` can be supplied when a retained temporary store is specifically needed for debugging.

`B4_RESULT.json` is the machine decision. `B4_ARTIFACT_MANIFEST.json` hashes each retained package/report artifact and excludes itself. `B4_TEST_RESULTS.json` records the focused and active R6 regression run. Hashes are portable; platform, timing, and source mtimes are operational evidence only.
