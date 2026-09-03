# ARCANA WorldSim — v0.6C Status

**Stage:** `v0.6C — Deep-Coupled Production Runtime Adapter, Physiological Macrostep Closure & Historical Initialization Gate`

**Verdict:** `PASS_DEEP_RUNTIME_PHYSIOLOGY_CHECKPOINT_AND_EVENT_INHERITANCE_CANDIDATE__HISTORICAL_D1_D2_BINDING_PENDING`

## Closed in this stage

- v0.6A local energy/depletion and v0.6B heritable selection are integrated around the production D3 runtime.
- D3 source is not edited; the runtime demography wrapper is temporary and restored after every governed call.
- Background Deep and 5% additive E/th photo-Deep are separate provenance reservoirs.
- Geological restore consumes only a finite Deep source buffer.
- Photo restore is recorded as external stellar pump energy.
- v0.4 acclimatization/remodeling/recoverable-load/injury equations are integrated by a macrostep-stable analytic fixed-point solver.
- Deep runtime state is checkpointable/resumable with exact source-fingerprint enforcement.
- D3-authorized fission daughters inherit Deep first/second moments and physiology; unknown births fail closed.
- Deep-OFF production execution is an exact D3 bypass.
- Historical initialization rejects proxies and non-210 Ma objects.

## Verification

- v0.6C unit tests: **9/9 PASS**.
- parent v0.6A regression: **14/14 PASS**.
- parent v0.6B regression: **13/13 PASS**.
- selected parent D3 release regression: **23/23 PASS**.
- parent Deep v0.4+v0.5 regression: **31/31 PASS**.
- Deep-OFF production wrapper parity: **bit-exact** on all compared D3 biological fields over 4×25 kyr.
- Deep-ON real-world smoke: **PASS** on a real 30 Ma D3 checkpoint for one 25 kyr step.
- Deep-ON checkpoint/resume: **bit-exact** after serialization/restore.
- Real D3 fission inheritance: **PASS** on `RPT_009_P002 → RPT_009_P002_F01` at +61.5 Myr.

## Real Deep-ON 25 kyr smoke

Using a true SEALED-D3 long-horizon checkpoint at relative year 36 Myr / physical age 30 Ma:

- demes: 104 → 104;
- population: 1305.0044546043418 → 1304.1126255503718 WorldSim units;
- max |Deep latent mean|: `3.646551381487207e-06`;
- median Deep VA: `0.04206293705750444`;
- mean remodeling: `1.1940838539430703e-05`;
- max injury: `0`;
- background surface Deep energy: `9.405177282831038e14 J`;
- photo-Deep energy: `1.881035680350554e13 J`;
- finite geological source buffer: `3.198029901516289e15 J`;
- cumulative net biological sink: `1.508023540895728e11 J`;
- cumulative stellar pump: `3.9748110532081146e9 J`;
- maximum energy closure residual: `0.0026779 J` against ~1e15 J reservoirs;
- gene-flow first-moment closure: ~`8.7e-19`;
- gene-flow second-moment closure: ~`2.1e-14`.

This is a runtime smoke, **not historical HX**.

## Real D3 birth/fission authority check

From a real 61.0 Myr runtime checkpoint, the wrapper was advanced to 61.5 Myr with Deep OFF.

D3 independently generated exactly one persistent-vicariance deme fission:

`RPT_009_P002 → RPT_009_P002_F01 @ +61.5 Myr`.

The D3 event explicitly remains `PERSISTENT_VICARIANCE_DEMOGRAPHIC_FRAGMENT_NOT_SPECIES`.

v0.6C only copied the parent's Deep sidecar state after D3 authorized that daughter. Deme IDs matched exactly after the event.

## Important historical architecture correction

The historical chain already established in the project is:

- D1 = 120-species ancestral initialization at **210 Ma**;
- D2 = pre-CHA1 deep-time lineage replay from that initialization;
- D2.2 = preferred high-resolution CHA-1 survivor authority;
- D3 = **post-CHA1** adaptive radiation / later macroevolution.

Therefore the full 210→0 Ma HX must not be implemented by inventing a synthetic 210 Ma D3 checkpoint or by running the post-CHA1 D3 representation backwards.

The correct integration architecture is:

`D1 + Deep → D2 + Deep → D2.2 CHA-1 + Deep → survivor-sidecar bridge → D3 + Deep → 0 Ma`.

## Remaining blocker

A production-historical Deep adapter for the D1/D2/D2.2 pre- and intra-CHA1 representations has not yet been built in this package, and the actual D1/D2 state package is not mounted in the current runtime.

Therefore:

`FULL_210_TO_0_MA_HX_AUTHORIZED = false`.

No structural proxy may be relabeled historical HX.
