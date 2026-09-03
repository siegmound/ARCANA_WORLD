# ARCANA WorldSim v0.6D1-R4.54-R1

## PowerShell Artifact-Hash Property Materialization Repair & R4.54 Reseal

Observed R4.54 failure:

```text
Exception setting "artifact_hashes":
"The property 'artifact_hashes' cannot be found on this object."
```

This happened in the host PowerShell bridge after the Madingley disposable
dry-run returned JSON.

Root cause:

- `ConvertFrom-Json` returns a `PSCustomObject`;
- the Madingley and RangeShifter result JSONs do not contain an
  `artifact_hashes` property;
- direct assignment `$r.artifact_hashes = ...` cannot create a new property on
  that object;
- the same latent defect existed in the NEMO bridge assignment.

This is a bridge/materialization defect, not a Madingley scientific/runtime
failure.

### Exact source binding

Pre-repair bridge SHA256:

`46251558cc7d373aff56707dc783b4cacc32b2fcbcf8a6a735ee998b88fe1067`

Post-repair bridge SHA256:

`9f8e09c2122b41cab224412b478adfd1e1e816122a2b2652a3c8668246feeaf8`

R4.54-R1 fails closed unless the active bridge is exactly one of those two
authorized states.

### Narrow repair

R4.54-R1:

1. makes the fallback result an explicit `PSCustomObject`;
2. adds one helper:

```powershell
Set-ArtifactHashes
```

implemented with:

```powershell
Add-Member -NotePropertyName artifact_hashes -Force
```

3. routes Madingley, RangeShifter, and both NEMO hash cases through that helper.

No seed, metric, readout, engine, threshold, or authorization semantics change.

### Preservation

Before patching, R4.54-R1 preserves any available:

- R4.54 runtime identity evidence;
- partial host dry-run evidence;
- Madingley result JSON;
- Madingley runtime work directory;
- exact prepatch bridge source.

The failed attempt had not reached historical scientific execution. R4.54 dry
runs are explicitly non-scientific, so rerunning them after this bridge repair
does not discard or overwrite scientific evidence.

## Run

Extract the overlay into the project root, then:

```powershell
.un_v0_6D1_R4_54_R1_artifact_hash_property_repair_and_reseal.ps1
```

Do not proceed to R4.55 unless the postrepair verification passes and R4.54
itself is SEALED.
