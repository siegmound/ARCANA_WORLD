# v0.6D1-R3.6A — Governed Scientific Engine Integration Contract

## Status
`CANDIDATE / NON-INVASIVE FOUNDATION`

Parent: `v0.6D1-R3.5`.

R3.6A does **not** modify the R3.5 scientific runtime, D3 coefficients, species registry, paleogeography, fission/coalescence, speciation gate, extinction logic, or the 150 Ma continuation gate.

## Core authority rule

`ARCANA WorldSim` is the sole owner of canonical world state and simulation time.

External scientific engines may only produce:

1. independent reference evidence;
2. calibrated provider candidates;
3. regional/specialist backend candidate results;
4. explicit calibration candidates requiring ARCANA review.

They may **never** write canonical state directly and may **never** auto-promote a parameter or event.

## Engine roles

- **NEMO 2.4.2** — primary quantitative-genetics/metapopulation reference oracle for R3.6.
- **Madingley** — ecosystem/energy/trophic-opportunity provider candidate; it does not own ARCANA species identity.
- **Geonomics 1.4.9** — regional, spatially explicit individual/genomic backend candidate, especially for later high-resolution windows.
- **CDMetaPOP 3.08** — secondary spatial demogenetic/multispecies oracle.
- **RangeShifter 3.0** — specialist dispersal/range-dynamics backend/oracle candidate.

## Common Scientific Exchange Contract

Every engine receives an immutable `ScientificExperiment` containing:

- experiment id and ARCANA source stage;
- exact source-state SHA-256;
- age/time context;
- exact engine name/version/role;
- random seed and replicate id;
- explicit assumptions and requested outputs;
- immutable numerical arrays copied from ARCANA state.

Every engine returns a `ScientificEvidenceBundle` containing:

- source experiment hash;
- engine identity/version;
- run id and status;
- metrics/output arrays;
- assumptions and unsupported mappings;
- stdout/stderr hashes when executed.

Evidence may be transformed only into a `CalibrationCandidate` with status `REVIEW_REQUIRED`.

## State isolation

Exported NumPy arrays are copied and marked read-only. The adapter layer has no canonical-state mutation API. A direct-write request raises `CanonicalWriteDenied`.

This isolation is deliberate: external libraries are scientific engines, not alternate canon owners.

## NEMO bridge policy

NEMO is run as an external executable/sidecar rather than linked into the ARCANA runtime.

Reasons:

- independent implementation is scientifically useful for cross-validation;
- NEMO uses genetically explicit individuals/QTL whereas ARCANA R3 uses moments;
- the GPL-3.0-or-later program remains operationally isolated;
- Windows production use can be handled through WSL2 or another pinned environment.

R3.6A materializes neutral bridge files:

- `arcana_patches.tsv`;
- `arcana_quantitative_traits.tsv`;
- `arcana_exchange_matrix.tsv`;
- `arcana_nemo_bridge.json`.

R3.6A deliberately **does not guess NEMO parameter names or a QTL architecture**. An executable `Nemo2_ARCANA.ini` is generated only from a NEMO-2.4.2-validated template supplied to the adapter.

The moment state `(mean, V_A)` does not uniquely determine a genotype realization. R3.6B therefore must construct a governed ensemble of NEMO genetic realizations matching the ARCANA moments in expectation; comparison is distributional, not bit-exact.

## Required R3.6 comparison

The target comparison remains:

`ARCANA current 125 kyr` ↔ `ARCANA 5 × 25 kyr D3.3A` ↔ `NEMO 2.4.2 genetically explicit reference`.

No change to `mu`, `b`, `q*=0.045`, gene-flow semantics, or variance ceiling is authorized by R3.6A.

## Integration sequence beyond NEMO

Madingley, Geonomics, CDMetaPOP and RangeShifter are exposed through isolated sidecar adapters in this stage. Their scientific state mappings remain intentionally unpromoted until dedicated validation stages establish unit mappings, invariants, uncertainty propagation and round-trip behavior.

## Promotion gate

R3.6A is successful when:

- all parent tests and audits remain PASS;
- scientific engine bridge tests PASS;
- external outputs cannot mutate canonical state;
- experiment/evidence hashes are deterministic;
- engine versions and assumptions are provenance-visible;
- NEMO bridge refuses to invent a missing exchange matrix or unvalidated executable template.

Passing R3.6A authorizes **R3.6B reference construction**, not 150→90 Ma continuation.
