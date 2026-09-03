# ARCANA WorldSim — Deep Production Runtime Contract v0.6C

**Stage:** `v0.6C — Deep-Coupled Production Runtime Adapter, Physiological Macrostep Closure & Historical Initialization Gate`

## 1. Scope

v0.6C integrates the already-validated v0.6A passive-energy ledger and v0.6B heritable Deep sidecar around the SEALED D3 production runtime without changing D3 source authority.

It closes the **post-CHA1 D3 production-runtime mechanics**. It does **not** authorize a historical 210→0 Ma HX replay by itself.

## 2. Governance invariants

- D3 SEALED remains the sole authority for fission, speciation, RI, extinction and functional-role events.
- No direct Deep speciation operator exists.
- No Deep latent axis is inserted into ecological/genomic/intrinsic RI.
- Mutation remains zero-mean; selection supplies directional change.
- D3 population-unit→effective-size calibration remains genetics-only and never enters the energy ledger.
- `reference_population` remains an environmental abundance/opportunity anchor, not K and not physical N.
- Deep-OFF is an exact production bypass.
- A structural proxy may never be labeled historical HX.

## 3. Runtime state

Each production checkpoint persists:

- D3 deme IDs and D3 runtime continuation state;
- Deep latent means `Z_X` and additive variance `V_A^X`;
- acclimatization, remodeling, recoverable load and injury;
- finite geological surface background energy;
- geological equilibrium target;
- photo-Deep energy and photo equilibrium target;
- finite geological source buffer;
- cumulative gross uptake, return flow, net sink and stellar pump ledgers.

Checkpoint restore is fail-closed if source fingerprints differ.

## 4. Separate energy provenance

Background Deep and stellar photo-Deep are distinct runtime reservoirs.

Geological background restore may draw only from the finite Deep source buffer.

Photo-Deep restore is an explicit external stellar input and therefore records:

`cumulative_stellar_pump_j`.

The current World 1 candidate remains additive 5% on E/th only. p/I/N receive zero stellar pump in v0.6C.

This avoids paying stellar input from the geological reservoir or silently creating energy.

## 5. Macrostep-stable physiology

The v0.4 equations are preserved, but their numerical integration is changed from unsafe long-step Euler to analytic frozen-coefficient solutions with a Picard fixed-point closure.

The state variables are:

- reversible acclimatization;
- persistent remodeling;
- recoverable load;
- injury.

No biological coefficient from v0.4 is changed by this numerical closure.

Long D3 macrosteps therefore cannot overshoot simply because physiology has sub-year to decadal timescales.

## 6. Deep→D3 demographic integration

For Deep ON:

1. update local Deep energy/depletion;
2. integrate physiology;
3. compute population-weighted viability and local selection gradient;
4. temporarily wrap only D3 demography so its ordinary species target is multiplied by Deep viability;
5. execute the governed D3 step;
6. restore the original D3 function immediately;
7. inherit Deep state only for D3-authorized new demes;
8. apply the existing D3 gene-flow exchange graph to Deep first/second moments;
9. update Deep standing variance using v0.6B/D3.3A homeostasis.

No Deep code can authorize a taxonomic birth.

## 7. Fission/speciation inheritance

A new Deep sidecar row may appear only when D3 reports a fission event containing a valid parent/daughter relationship.

The daughter inherits the parent's latent first/second moments and physiological state.

An unknown new deme without D3 provenance fails closed.

A taxonomic speciation event does not automatically create an additional Deep birth; the existing founder deme retains its inherited sidecar state.

## 8. Deep-OFF parity

With `deep_enabled=false`:

- no Deep energy step executes;
- no physiology executes;
- no Deep selection executes;
- no demographic patch executes;
- D3 executes through its ordinary production path.

The sidecar is reconciled only after a D3-authorized fission so that a control run can continue. This reconciliation cannot affect D3 state.

## 9. Historical initialization gate

`bind_historical_210ma()` accepts only a real 210 Ma biological state carrying true demographic population rasters and species/deme identity. An A1 reference raster or fixed structural proxy is rejected.

More importantly, historical project provenance shows the correct 210→0 architecture is not one monolithic D3 replay:

`D1 210 Ma initialization → D2 pre-CHA1 deep-time lineage replay → D2.2 high-resolution CHA-1 → D3 post-CHA1 radiation/runtime`.

Therefore v0.6C validates the D3-side runtime but deliberately does not manufacture a 210 Ma D3 checkpoint.

## 10. Release condition

v0.6C may pass as a production-runtime candidate while `historical_HX_authorized=false`.

The next stage must bind Deep to the historical D1/D2/D2.2 chain and prove survivor/sidecar continuity before a full HX runpack is authorized.
