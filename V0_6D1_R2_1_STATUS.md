# ARCANA WorldSim — v0.6D1-R2.1 Status

**Stage:** `v0.6D1-R2.1 — Governed Speciation/Extinction Actuator & Internal Cadence Closure`  
**Verdict:** `PASS_GOVERNED_SPECIATION_EXTINCTION_AND_INTERNAL_CADENCE_CLOSURE_CANDIDATE`  
**Qualification:** `BIRTH_AND_ORDINARY_EXTINCTION_AUTHORIZED; PERSISTENT_VICARIANCE_FISSION_IMPLEMENTED_BUT_PRODUCTION_DISABLED_PENDING_RESOLVED_DEEP_TIME_BARRIER_HISTORY; MICRO_RASTER_NOT_AUTHORIAL_SEAL_TARGET`

## Core result

R2.1 upgrades the rebased H0 runtime without introducing a random speciation/extinction rate and without changing the already validated R1 common state. The exact SEALED D3.0C structural-gate implementation is retained byte-for-byte and combined with the D3.2B founder-lineage viability semantics and D3.2D persistent deterministic ordinary-extinction semantics.

### Production H0 pilot, 210→180 Ma

- Initial species richness: **120**.
- Final species richness: **120**.
- Initial common state: the R1 210 Ma rebaseline.
- Final total population: **1842.9707320459243** WorldSim units.
- A1 180 Ma reference: **1843.1648681163788**.
- Relative global error: **1.05327566628877e-4** (~0.01053%).
- Final demographic components: **133**.
- Speciation births: **0**.
- Ordinary extinctions: **0**.
- Production demographic fissions: **0**.
- `HSG_025` is not present/forced.
- Reproductively disconnected species at endpoint: **0**.
- Structurally speciation-ready species at endpoint: **0**.
- Gene-flow first-moment closure max abs: **1.1368683772161603e-13**.
- Gene-flow second-moment closure max abs: **1.1641532182693481e-10**.

## Library reuse decision

R2.1 is explicitly reuse-first:

- `scipy.ndimage.label` for raster connected components;
- `scipy.sparse.csgraph.connected_components` for reproductive graph partition;
- `scipy.spatial.cKDTree` inherited from R2 for conservative nearest-land remapping.

No NetworkX dependency was added because SciPy already provides the required graph primitive. A matrix-exponential transport approach was evaluated but rejected because ARCANA transition weights depend on changing ecological state; fixed internal subcycling preserves the existing model semantics.

## Exact D3 authority preservation

The copied SEALED D3.0C source has SHA-256:

`1927744f10e39c8c2af39b6e72799bef8b7b8466bea123d1aa28d38c812af028`

The parent R2 runtime source remains unmodified with SHA-256:

`2a56552a0121c9a66d42357887bc8ecf18bf90f0063a7e9face002a21b205cb0`

## Speciation actuator

A new daughter species can be materialized only after all of the following are true:

1. real reproductive fragmentation exists;
2. every cross-component pair passes the D3.0C biological-time, intrinsic-RI, trait-distance and effective-exchange gates;
3. the candidate persists continuously for at least **1 Myr**;
4. founder and complement populations pass life-history-scaled viability;
5. founder effective size, normalized additive variance, occupied-cell support and non-collapse gates pass.

Synthetic validation demonstrated that a ready lineage does **not** speciate at isolation onset or at 0.5 Myr; it produces exactly one daughter only at the 1 Myr persistence boundary, with exact population conservation.

## Ordinary extinction actuator

Ordinary extinction remains deterministic and persistence-based. There is no global extinction rate. Low population by itself is insufficient; continuous nonviability and continued decline are required for the D3-style persistence window.

## Demographic fission qualification

The persistent-vicariance actuator is implemented and tested, but its production default is **OFF** in R2.1. With only the self-contained 210/180 Ma paleogeographic support keyframes, turning it on in a 210→205 Ma sensitivity produces **47** demographic fissions and expands components **133→180** while richness stays 120. This is treated as evidence of under-resolved barrier history, not as authority to promote those events.

R3 must bind a resolved deep-time barrier-history provider before production fission can be enabled.

## Internal cadence closure

Production candidate cadence:

- external macrostep/checkpoint grouping: **500 kyr**;
- biology cadence: **125 kyr**;
- transport cadence: **62.5 kyr**;
- speciation/extinction/fission gate evaluation: **500 kyr**;
- output snapshot cadence: **1 Myr**.

External 250 kyr vs 500 kyr chunking is **bit-exact** for population, trait, VA, RI, isolation clock, IDs and events when internal cadence is unchanged.

Refinement on 210→209 Ma:

- transport 125→62.5 kyr: species-total abundance-weighted L1 = **5.8575e-5**;
- biology 125→62.5 kyr (with transport 62.5→31.25 kyr): species-total abundance-weighted L1 = **5.1817e-4**.

Cell-level micro-raster distributions converge more slowly and remain outside the authorial seal target for this deep-time stage.

## Verification

- R2.1 formal audit: **30/30 PASS**.
- Complete included test suite: **63/63 PASS**.
- Synthetic speciation/fission/extinction audit: **PASS**.
- External-macrostep bit-exact closure: **PASS**.
- Full H0 210→180 Ma production-candidate pilot: **PASS**.

## Scope lock

Deep biological coupling is **OFF**. R2.1 is an H0 Natural-Control runtime closure. It does not authorize HX, full 210→0 Ma production history, or fission under unresolved paleogeographic barrier history.
