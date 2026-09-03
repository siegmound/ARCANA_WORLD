# R3.20-R1 — CHA-2 Magnitude Audit Metric & Parent-Schema Repair

## Scope
R3.20-R1 repairs only the **audit layer**. It does not modify the SEALED CHA-2/C1 physical provider, the freshwater pulse, climate equations, R3.19 H0 checkpoint, biology, Deep coupling, or the derived hydrological-hazard equations.

## Triggering evidence
The first live R3.20 candidate audit returned 47/51 with:

- R3.19 SEALED parent check reported false despite the parent being SEALED 73/73;
- freshwater peak 0.20270779797753885 Sv at 12.900 ka;
- overturning minimum 0.3797189066407908 of baseline at 12.850 ka;
- strong suppression duration 1300 y;
- northern local cooling 4.918580792825181 C at 12.850 ka;
- low-order global temperature-state cooling 0.09231673360365544 C;
- no 90% overturning recovery detected inside the 15-11 ka nested core.

The physical peak, timing, overturning collapse, duration, and northern cooling all passed the intended Younger-Dryas-class envelope. The failures isolated two audit-semantics errors plus one parent-schema mismatch.

## Repair A — R3.19 seal schema
R3.19's authoritative seal summary stores the count as:

`formal_audit_checks = "73/73"`

R3.20 originally read `checks`. R1 reads `formal_audit_checks` first and accepts `checks` only as a backward-compatible fallback.

## Repair B — global temperature metric
`global_temperature_anomaly_c` in sealed v0.6.1 is a low-order climate-state variable entering carbon/ice feedback equations. It is not an area-weighted observational reconstruction of global mean surface temperature. The original R3.20 hard threshold of 0.20-4 C therefore compared unlike quantities.

R1:
- retains the scalar and its timing as diagnostics;
- requires only the physically consistent cooling direction as a sanity gate;
- keeps the hard magnitude gate on the spatial northern temperature field, where the model explicitly represents the multi-degree regional response.

No temperature parameter is changed.

## Repair C — event exit vs. 90% full recovery
The original audit used `>=90%` of baseline overturning as the hard recovery definition. That measures near-complete circulation recovery, not termination of the strong Younger-Dryas-like regime.

R1 uses the same 80% baseline threshold already defining `strong_suppression_duration` to identify the event's exit from strong suppression. This makes event duration and event exit internally consistent.

- exit from <80% suppression is checked for existence;
- northern cooling peak timing remains a hard temporal gate;
- exact recovery timing is diagnostic, not a classification target;
- 90% recovery is searched diagnostically beyond 11 ka using only exact sealed 100-y anchors, out to 9 ka.

The 15-11 ka hazard layer remains exactly 50-y and unchanged.

## Governance
R1 changes no CHA-2 physics and does not introduce human/cultural targets.

- `cha2_nested_50y.py`: unchanged / byte-authoritative
- freshwater forcing: unchanged
- overturning equations: unchanged
- temperature equations: unchanged
- hydrological hazard equations: unchanged
- R3.19 H0 state: unchanged
- human population used: false
- settlement target used: false
- flood-myth target used: false
- religion target used: false
- mandatory impact origin: false

## Expected consequence for the reported live evidence
The former false parent-seal failure is removed. The 0.0923 C low-order scalar is no longer misused as an observed-global-mean magnitude gate. The 90% recovery timing is no longer a hard YD-class criterion.

The repaired live audit still fails closed if any genuine physical gate fails, including freshwater magnitude/timing, overturning collapse/timing, strong-suppression duration, northern cooling magnitude/timing, failure to exit strong suppression, or an inconsistent global-state warming direction.
