# ARCANA WorldSim v0.6D1-R4.54-R2

## NEMO result-capture + SLiM divergence API repair

R4.54-R1 fixed the PowerShell `artifact_hashes` materialization defect.
The subsequent real disposable dry-run reached all five engines:

- Madingley PASS
- RangeShifter PASS
- CDMetaPOP PASS
- NEMO FAIL
- SLiM FAIL

R4.54 remained correctly BLOCKED and no historical scientific stream was
authorized.

### NEMO

The R4.54 host bridge received no standard NEMO result JSON, which caused the
generic fallback object and erased useful engine-specific diagnostics.

R4.54-R2 makes every NEMO failure path JSON-complete and preserves stdout,
stderr, runtime file listing, and collector traceback.

It also strengthens seed verification:

- isolated INI must contain the requested frozen seed;
- native NEMO stdout must independently report
  `setting random seed from input value: <same seed>`.

The scientific metrics are unchanged:

- `NEMO_ALLELE_FREQUENCY_TRAJECTORY`
- `NEMO_REALIZED_FREQUENCY_CHANGE_SUMMARY`

### SLiM

The SLiM runtime reached the collector, but the new ancestry/gene-flow readout
failed before metric materialization.

The metric remains the same `between_population_divergence`. The repair only
changes the tskit API call from an indexed multi-output form to the documented
single-pair form:

```python
ts.divergence(sample_sets=[a, b])
```

The result is then explicitly normalized to one scalar.

SLiM seed binding is also strengthened by parsing its native stdout:

```text
// Initial random seed:
<seed>
```

The scientific metrics remain unchanged:

- `SLIM_TREE_SEQUENCE_STRUCTURAL_SUMMARY`
- `SLIM_ANCESTRY_GENE_FLOW_SUMMARY`

### Governance

This repair:

- preserves the blocked R4.54/R1 evidence;
- preserves the three prior PASS dry-run results;
- performs no historical scientific execution;
- changes no authorized metric ID;
- adds no threshold;
- performs no canonical write;
- does not weaken any gate.

Pre/post source hashes:

```text
run_nemo_r454.sh
19aecd524d8eb504a1852cec54bdd293ad5b7cc393b00b9ad57901886bd0936f
→ 6b4cadda339c7c253a3bbde42fa45ad7a59173cb3284309c3691e2dbf7b3930c

nemo_collect_r454.py
d943f79905cbb08c12373275966a4fe6ee2e22cfe834be5c8873229d0da24a0e
→ 4e588c5ac9be22ef6a7de11f3f8611bd750d4d7f2a86c416ac9a73f7730c7ffb

slim_collect_r454.py
2a8640b0fb28fb597b971411486e2dcb193bbfe5d7499b531f61b3d2f40ded43
→ 91dd0851b709664ed51dffdce2c65ae34ff7a0418ead57aca16cef33adb41c6e
```

Run:

```powershell
.un_v0_6D1_R4_54_R2_nemo_slim_repair_and_reseal.ps1
```

Do not proceed to R4.55 unless R4.54 is SEALED and the R2 postrepair audit
passes.
