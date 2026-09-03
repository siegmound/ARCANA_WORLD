# Dynamic Ceiling Sensitivity Protocol — v0.6D1-R3.5

## Why this stage exists
The full R3.4 210→150 Ma run contacted `q=0.08` in 28/1374 reservoirs at the endpoint, while a frozen-endpoint relaxation fell back to `q≈0.07359`. Therefore endpoint/frozen diagnostics are insufficient: the safety ceiling must be evaluated over the **time-resolved dynamic path**.

## Primary paired replay
Run from the same R1 common state:

- `H0.08`: ceiling `q=0.08`
- `H0.10`: ceiling `q=0.10`

Everything else is identical, including seed, biology cadence, transport cadence, paleogeography, migration, gene flow, homeostasis, fission, coalescence, speciation, and extinction.

## Telemetry per 125 kyr biology step
R3.5 records:
1. `q` before gene flow;
2. `q` after gene flow;
3. diagnostic unclipped `q` after Riccati homeostasis;
4. actual `q` after homeostasis;
5. clipping count/fraction;
6. fraction ≥99% of cap;
7. per-axis maxima;
8. root lineages/axes near or above the cap;
9. events occurring in the same biology step.

For 210→150 Ma this yields 480 records per replay.

## Interpretation gates
### Gate A — Is q=0.10 dynamically non-binding?
Required for a headroom candidate:
- `steps_with_homeostasis_clipping == 0`
- `steps_with_ge_99pct_ceiling_after_homeostasis == 0`

If q=0.10 clips repeatedly, stop: do not keep raising the ceiling. Reopen the admixture/homeostasis model.

### Gate B — What causes q=0.08 contact?
Inspect whether clipping/near-cap steps coincide with:
- barrier transitions;
- fission bursts;
- coalescence/recontact;
- speciation;
- or gene-flow spikes without a demographic event.

This distinguishes transient event-driven headroom demand from a persistent homeostatic imbalance.

### Gate C — Macrohistory response
Compare:
- species identities and richness;
- speciation event identity/timing;
- fission/coalescence counts and timing;
- final population and A1 envelope;
- micro-deme tail;
- gene-flow moment closure.

Differences between 0.08 and 0.10 are expected if 0.08 is genuinely binding. They are evidence to inspect, not an automatic failure.

### Optional confirmation
If q=0.10 is non-binding but the macrohistory differs materially from q=0.08, one optional q=0.12 confirmation can establish that 0.10 itself is already outside the dynamics. q=0.12 is **not** automatically promoted.

## Promotion rule
A production safety ceiling may be promoted only if it is non-binding over the full dynamic replay. 150 Ma may then be promoted only if the resulting Natural-Control endpoint also passes the ordinary demographic, moment-conservation, fragmentation and speciation audits.
