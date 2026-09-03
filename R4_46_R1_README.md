# ARCANA WorldSim v0.6D1-R4.46-R1
## Evidence Manifest Metric-ID Canonical Order Repair & Reseal

The first live R4.46 scientific cohort execution completed all scientific
streams and all expected evidence transport:

- 12/12 replicate streams
- 12,456/12,456 metric records
- 6,540/6,540 integrity records
- 5,916/5,916 descriptive records
- zero forbidden metric IDs
- zero numeric thresholds
- zero automatic scientific PASS/FAIL

R4.46 was nevertheless BLOCKED by exactly one manifest gate.

### Root cause

`_evidence_manifest()` first computed:

`metric_ids = sorted(actual_metric_ids)`

but then compared that sorted list against a hard-coded list whose first two
items were in non-sorted order:

- `GNX_CARRIER_NATIVE_CELL_READBACK_IJ`
- `GNX_CARRIER_COORDINATE_READBACK_XY`

Lexicographic order is instead:

- `GNX_CARRIER_COORDINATE_READBACK_XY`
- `GNX_CARRIER_NATIVE_CELL_READBACK_IJ`

No metric was missing or unexpected. This was only an order-sensitive manifest
comparison bug.

### Repair

R4.46-R1 compares the already-sorted actual IDs against the sorted exact set of
the same five pre-authorized R4.43 metric IDs.

Prepatch module SHA256:
`846b1c7d621bb4aa5c48787441b831e4303c2ee166d2f64e5a192249a5c4b423`

Postpatch module SHA256:
`5b17d1ee8ef3cb18741764557d8534e72045983edf0109790876a5b9f7f3ecdb`

### Critical governance behavior

R4.46-R1 **does not rerun Geonomics**.

It preserves the failed R4.46 evidence, loads the existing J14/J18/J21
scientific evidence files, rebuilds only the evidence manifest and integrated
audit, and then runs the existing final seal.

It does not:
- change any metric record;
- change any scientific value;
- add/remove a metric ID;
- add a threshold;
- adjudicate descriptive values;
- rewrite canonical state.

Run:

```powershell
.un_v0_6D1_R4_46_R1_evidence_manifest_order_repair_and_reseal.ps1
```
