# ARCANA WorldSim — v0.6D1-R3.11
## Post-CHA1 H0 Recovery & Adaptive-Radiation Restart Contract

**Stage:** `v0.6D1-R3.11`  
**Parent:** `v0.6D1-R3.10 SEALED`  
**Branch:** World 1 H0 — Deep biological coupling OFF

## 1. Canonical temporal window

R3.11 begins from the exact R3.10 restart boundary:

```text
65.5 Ma = +0.5 Myr after CHA-1
```

and ends at:

```text
61.0 Ma = +5.0 Myr after CHA-1
```

This reproduces the *temporal scope* historically used for the first post-CHA1
adaptive-radiation phase, but **does not reactivate the old D3.1 50-kyr solver**.
The current production authority is R3.7I/R3.8 with a 125-kyr biology cadence.

Canonical ordinary biology steps:

```text
(65.5 - 61.0) Myr / 0.125 Myr = 36 steps
```

## 2. Exact parent authority

R3.11 must load the R3.10 checkpoint directly.

```text
JSON SHA-256  5ea3f6cad09e2b6e09a6ff795a89dbd370ca0ca049f20c04e8d53fbeb8dd6469
NPZ  SHA-256  d31ae5aaeb53422809e173c20308e69af334ef8d2d535484ae51141b9dff58a8
```

Canonical parent state:

- 93 survivor species;
- 207 survivor components;
- CHA-1 already applied exactly once;
- endpoint `65.5 Ma POST_CHA1_500KY`;
- survivor trait, VA, S, ancestry/LD and adaptive-coordinate state preserved;
- Deep biological coupling OFF.

R3.11 may not rerun 210→66 Ma and may not reapply CHA-1.

## 3. Ordinary production machinery re-enabled

R3.11 re-enables the already-sealed ordinary H0 lifecycle:

- demography;
- migration/transport;
- trait selection;
- segregation-aware gene flow;
- D3.3A additive-variance dynamics;
- RI/contact/isolation clocks;
- persistent reconnection coalescence;
- persistent vicariance fission;
- deterministic ordinary background extinction;
- D3.0C structural speciation gate;
- D3.2B founder viability/persistence;
- R3.7I closed-loop reduced genetic state.

No new post-impact operator is introduced to create radiation.

## 4. No adaptive-radiation multiplier

The term **adaptive-radiation restart** means that ordinary mechanisms capable
of producing radiation are allowed to operate again after the special CHA-1
bridge. It does **not** mean:

- increased mutation supply;
- increased VA ceiling;
- boosted trait response;
- accelerated RI;
- increased fission rate;
- lowered founder thresholds;
- inserted species;
- protected winners;
- a global speciation-rate target;
- tuning toward an Earth-like species count.

Any post-CHA1 diversification must emerge from the existing rules.

## 5. Frozen-lifecycle thaw adapter

R3.10 advanced physical time by 500 kyr while ordinary founder, vicariance,
reconnection and background-extinction lifecycle updates were disabled.
Some lifecycle records store absolute `last_seen_elapsed_year` or episode-start
timestamps.

If these timestamps were resumed unchanged, the first ordinary 500-kyr check
could incorrectly credit the frozen CHA-1 interval as ordinary persistence.

R3.11 therefore applies a one-time temporal thaw adapter at 65.5 Ma:

- scientific arrays are unchanged;
- RI and isolation clocks are unchanged;
- accumulated persistence values are unchanged;
- `first_seen_elapsed_year` is unchanged;
- active `last_seen_elapsed_year` values are moved to the 65.5-Ma thaw point;
- an active ordinary-extinction episode, if present, has only its episode-time
  origin shifted by the frozen 500 kyr.

Canonical parent affected records:

```text
founder       3
vicariance  207
reconnection  2
ordinary extinction 0
```

This is a restart-clock correction, not a biological calibration.

## 6. Radiation-provenance guard

A speciation after CHA-1 is not automatically evidence that CHA-1 caused that
speciation.

The runner therefore records whether a new speciation exactly matches one of
the founder candidates already active at the R3.10 parent boundary.

Classification:

```text
MATCHED_PRE_CHA1_FOUNDER_CARRYOVER
NOT_MATCHED_TO_INITIAL_PRE_CHA1_FOUNDER_STATE
```

The second class is compatible with post-CHA1 initiation but is **not by itself
proof of empty-niche causation**. Causal attribution remains a later
counterfactual/comparative question.

## 7. Scientific constants remain fixed

R3.11 does not change:

- `mu = 0.002 / Myr`;
- `b = 0.9876543209876544`;
- `q ceiling = 0.08`;
- K_CENTER operational semantics;
- migration constants;
- 125-kyr biology cadence;
- 500-kyr speciation/extinction/fission/reconnection checks;
- 1-Myr founder persistence;
- 2-Myr vicariance persistence;
- 2-Myr reconnection persistence;
- D3.0C structural speciation thresholds;
- paleogeography.

## 8. Acceptance gates

The canonical 65.5→61.0 run is accepted only if:

1. exact R3.10 checkpoint hashes pass;
2. parent = 93 species / 207 components at 65.5 Ma;
3. lifecycle thaw is applied exactly once;
4. exactly 36 ordinary biology steps execute;
5. final age is exactly 61.0 Ma;
6. no new `CHA1_species_extinction` occurs;
7. no second CHA-1 bridge-complete event occurs;
8. Deep biological coupling remains OFF;
9. ordinary lifecycle is fully re-enabled;
10. no post-impact radiation multiplier or old D3.1 solver is used;
11. population remains non-negative;
12. population on inaccessible cells remains zero;
13. S remains symmetric, non-negative, zero-diagonal;
14. `q <= 0.08`;
15. recorded unclipped telemetry has zero ceiling contacts;
16. checkpoint save/reload identity is exact;
17. all diversification/extinction counts are recorded as outcomes, not targets.

## 9. Diagnostic smoke result

The validated 65.5→65.0 Ma smoke executes 4 ordinary biology steps and returns:

```text
species        94
components    206
population    1606.4745439563944
remap            2
coalescence      1
fission          0
speciation       1
ordinary extinction 0
peak q         0.045762434061137815
clipping steps   0
serialization identity PASS
```

The single speciation is `RPT_004 -> RPT_004_D04` and is classified as
`MATCHED_PRE_CHA1_FOUNDER_CARRYOVER`: the founder candidate already existed
before CHA-1 and only reached the 1-Myr founder-persistence gate after another
0.5 Myr of *ordinary* post-event time. The frozen 500 kyr was not credited.

## 10. Production execution policy

The 36-step canonical run is intended for local execution. ChatGPT validates
short smokes, restart semantics and audits; the user machine executes the
multi-Myr production replay.
