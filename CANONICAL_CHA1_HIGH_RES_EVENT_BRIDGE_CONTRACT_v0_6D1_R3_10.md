# ARCANA WorldSim — v0.6D1-R3.10
## Canonical CHA-1 High-Resolution Rebased Event Bridge Contract

**Stage:** `v0.6D1-R3.10`  
**Parent:** `v0.6D1-R3.9` exact `66.0 Ma PRE_IMPACT_66P0_MINUS` checkpoint  
**Branch:** World 1 H0, Deep biological coupling OFF

## 1. Scope

R3.10 is the dedicated event operator that is allowed to cross CHA-1. Ordinary
125 kyr biology is forbidden from crossing 66 Ma.

The governed transition is:

```text
R3.9 66.0 Ma PRE_IMPACT
    -> exact CHA-1 event at t=0
    -> high-resolution physical/ecological/hazard bridge
    -> +500 kyr
    -> 65.5 Ma POST_CHA1 restart checkpoint
```

## 2. Historical authority and limitation

The historical `v0.6.3D2.2 CHA-1 High-Resolution Replay` remains authority for
event semantics and surviving RAW quantitative evidence:

- event-relative window `-100 kyr .. +500 kyr`;
- 917 materialized reporting checkpoints;
- 12 km impactor, 20 km/s, `5.428672105e23 J`;
- dust/sulfate/soot -> PAR collapse -> impact winter -> NPP collapse;
- dynamic food-web collapse/recovery;
- persistent cumulative extinction hazard;
- fixed keyed exponential threshold per lineage;
- no per-step Bernoulli;
- no forced guild survivor;
- no historical survivor-list lookup;
- frozen 66 Ma tectonics during the 0.5 Myr bridge;
- impact-distance mortality disabled because exact paleocoordinates remain provisional.

The original D2.2 executable source/state bytes are not present in the rebased
package. R3.10 therefore **does not claim bit-identical historical solver reuse**.
It is a new governed implementation anchored to recovered D2.2 RAW values and
aggregate event evidence.

## 3. Physical forcing transfer

Recovered RAW anchor rows are represented exactly by monotone PCHIP interpolation.
PCHIP is chosen specifically because it preserves anchor values and shape without
inventing polynomial overshoot.

The impact anchor is exact:

```text
PAR fraction              0.0030275547453758
Temperature anomaly      -16.0 C
NPP multiplier             0.0055720068149199
Extinction-pressure index  0.9812281358795112
Atmospheric CO2          862.2641509433962 ppm
```

The long physical tail remains active to +500 kyr. Direct extinction hazard,
however, is restricted to the independently recovered acute-collapse interval
`0..20 yr`; this is broader than the historical last D2.2 extinction at 14.41 yr
and is not a survivor realization lookup.

## 4. Food-web transfer

The reduced chain remains:

```text
NPP -> plant -> herbivore -> mesopredator -> apex
```

Because the historical source equations are unrecovered, four reduced-order
relaxation times are calibrated only against the independently recovered D2.2
minimum states:

```text
plant          0.395
herbivore      0.433
mesopredator   0.782
apex           0.974
```

This calibration is independent of R3.9 and cannot use the R3.10 survivor outcome.

## 5. Rebased species hazard

R3.9 supplies 305 extant species at impact. Historical 31 survivor identities are
not portable and are forbidden as lookup/protection data.

For each current species, R3.10 derives vulnerability from the current state:

- body size;
- reproduction;
- spatial occupancy;
- plate-range entropy;
- wetland refuge;
- diet entropy;
- deterministic keyed frailty.

Within each guild, modifiers are centered to geometric mean 1. Therefore they
change lineage identity risk but cannot silently alter guild-level event severity.

The transferred D2.2 guild cumulative hazard is derived before the rebased run:

```math
C_g = -\ln(s_g)
```

where `s_g` is the historical D2.2 survival fraction for that guild.

Each current species gets a deterministic exponential threshold:

```math
H_i^* = -\ln U_i
```

with `U_i` generated from the canonical keyed seed and current species ID.
Extinction occurs at the first continuous cumulative-hazard crossing.

## 6. No target tuning

Forbidden:

- choosing a seed to obtain a preferred richness;
- changing hazard after observing the R3.10 outcome;
- protecting named species or guilds;
- importing the old 31 survivor IDs;
- modifying `mu`, `b`, q ceiling, K reference, migration, RI/speciation, or paleogeography;
- enabling Deep biological coupling.

The canonical risk amplitude (`0.25`) and guild hazard scale (`1.0`) are fixed
before outcome generation. Sensitivity runs are diagnostic only and may not be
used to select the canonical branch.

## 7. Lifecycle semantics inside event

The event bridge is not ordinary evolutionary time stepping:

- no 125 kyr step crosses 66 Ma;
- ordinary speciation OFF;
- adaptive radiation OFF;
- no gene-flow/migration operator is invoked;
- surviving trait/VA/reduced genetic coordinates are preserved exactly;
- species-level CHA-1 extinction removes all components of an extinct species;
- active pair/component lifecycle registries are pruned to live components;
- ordinary reproductive lifecycle timers are frozen during the special event;
- elapsed physical time advances by 500 kyr.

At +500 kyr survivor populations refill only pre-impact guild/cell capacity and
never exceed that event carrying proxy.

## 8. Acceptance gates

R3.10 is accepted only if:

1. exact R3.9 checkpoint hashes pass;
2. input is 305 species at exactly 66.0 Ma pre-impact;
3. 917 reporting checkpoints exist over `-100 kyr .. +500 kyr`;
4. recovered forcing anchors close at machine precision;
5. D2.2 food-web minimum-state oracle closes;
6. no per-step Bernoulli / forced survivor / old survivor lookup exists;
7. hazard is deterministic under repeat execution;
8. all direct extinctions occur within the declared acute 20-y support;
9. no ordinary speciation/radiation/Deep coupling occurs;
10. no negative population or inaccessible-cell population exists;
11. segregation-potential symmetry/diagonal/nonnegativity hold;
12. `q <= 0.08` without parameter changes;
13. save/reload identity is exact;
14. output is exactly `65.5 Ma POST_CHA1_500KY`.

## 9. Current deterministic candidate result

Canonical predeclared branch:

```text
pre-impact species       305
CHA-1 direct extinctions 212
survivors                 93
extinction fraction       69.5081967%
post-event components    207
post-event q_max           0.04575032753015043
```

The value 93 is an emergent regression result, not an input target.
