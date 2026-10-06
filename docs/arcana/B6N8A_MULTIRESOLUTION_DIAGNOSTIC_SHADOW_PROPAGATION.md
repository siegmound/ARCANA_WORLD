# B6N8-A Multi-Resolution Diagnostic Shadow Propagation

## Development qualification

Branch `r6/b6n8a-multiresolution-diagnostic-shadow-propagation`; source
baseline `54ea550ecc623760ee5115a9033b38cb963a4584`. The implementation is
uncommitted development work. It remains a diagnostic experiment, not
physical-history authority.

## P0 conclusion and repaired canonical preflight

P0 established that `arcana_canonical_store.json` is the immutable B6M0
genesis descriptor. Its `canonical_temporal_state_count = 1` and
`latest_age_ma = 210.0` describe initialized T0, not the live published view.
The B6N8-A contract does not encode that interpretation and was left
unchanged.

The gate now checks the configured root and `CURRENT.json`, verifies that its
view is readable by the existing `HistoryStore`, and uses
`HistoryQueryService` against a byte-identical temporary copy. The canonical
tree is hashed before and after; the canonical `HistoryStore` itself is never
opened for writing/recovery. The copied reader validated view
`view_e1eb239931826b01c1cb55b97bf9a9ee4fcf867c11ab15e624679d2b8f421044`,
21 visible states, two temporal records, and exactly two tectonic-geometry
ages: 210 Ma and 209.97287659484368 Ma. The `210Ma` versus `210.0Ma` spelling
in other domains is not counted as another geometry epoch.

PRE_EVENT and POST_EVENT selectors resolved their exact governed IDs at the
same event age. The unselected same-time query returned `CONFLICT` with
`AMBIGUOUS_CAUSAL_STATE`; history ordering was PRE_EVENT then POST_EVENT.
Both states refer to payload SHA256
`9527429db651bac60606b257dcff7abfff601fc66df053ce278822a3a8a8a46a`. There
were zero pending publication transactions. The old descriptor count of one
is retained only as informational genesis provenance. Preflight:
`PASS_CANONICAL_LIVE_VIEW_PREFLIGHT`.

## Experiment and observations

The diagnostic used the governed B6N2 plate-pair 1:3 Euler vectors and 72
identified nodes on 71 interface segments. Each level restarted from the
same B6K POST_EVENT coordinates. The window was 2053.5129772777655 years
(one quarter of the 8214.051909111062-year B6N3-A model-scope bound), with
RK4 step counts 4, 8, 16, and 32 and internal steps 513.3782443194414,
256.6891221597207, 128.34456107986034, and 64.17228053993017 years. These
internal steps are not persistent intervals or dt2.

There were 2880 temporary three-component coordinate samples across four
levels, five common times, 72 nodes, and two plate-side representations.
Coordinate arrays stayed in memory; no trajectory files or WORLD_HISTORY
records were written. The retained JSON is 58,053 bytes and contains sample
metrics and per-level hashes rather than coordinate arrays.

Cross-resolution maximum differences to the 32-step level were approximately
8.07e-9 m (4 steps), 8.61e-9 m (8), and 9.31e-9 m (16); maximum relative
differences were approximately 4.68e-11, 4.68e-11, and 4.86e-11. The
comparison curves and endpoint values are recorded in the external result.
Pair-side geometric mismatch increased monotonically from 5012.18 m to
5391.66 m in the sampled window. This is a geometry proxy, not rift opening
or accommodation. No numerical tolerance is governed, so these magnitudes
are reported without an acceptance claim. Numerical resolution uncertainty
and the missing physical model/authority remain distinct; the experiment
does not establish a physical convergence criterion or transition.

The deterministic local refinement probe selected the last quarter
(1540.134732958324 to 2053.5129772777655 years), at node 38119 / plate 1.
Refining that temporary interval from one coarse step to 32 local steps did
not decrease its exact-rotation error (0 to 9.934e-9 m at reported
precision). It created no event or transition. Further refinement cannot
resolve the absent rift-transition state/predicate, support-remapping
authority, or physical uncertainty bounds.

Sparse reconstruction errors ranged from 1.061e-9 m (4-step) to
8.096e-9 m (32-step). Tolerance authority is absent; no production
compression acceptance is claimed. The 5-entry observable registry records
semantics, units, derivation, authority, scope, adaptive-dt usefulness, and
state-extraction usefulness. Geometric values are derived diagnostics,
support identity is invariant, and physical transition outputs remain
UNAVAILABLE/UNKNOWN.

## B6N7 Tier-2 mapping

- Process-state evolution law: `NO_SIGNAL; MODEL_REQUIRED`.
- Forcing: direct existing signal, limited to the restricted pair Euler
  vectors.
- Interface response: `PARTIAL_DIAGNOSTIC_ONLY`; physical response unknown.
- Transition predicates/topology coverage: `NO_SIGNAL; AUTHORITY_REQUIRED`.
- Support validity/remapping: input identity only; authority absent.
- Physical uncertainty and bounds: unknown; no acceptance thresholds.

Sample significance remains diagnostic-only: the POST_EVENT point is an
existing causal boundary; intermediate samples are insignificant numerical
samples for this experiment; the largest discrepancy is only a reconstruction
checkpoint candidate; no governed event candidate exists; uncertainty
boundary is UNKNOWN; the model-authority boundary was not reached.

## Validation, evidence, and gates

Focused B6N8-A plus canonical-reader/B6N1/B6N5/B6N6/B6N7 regression:
68 passed. Full active R6 suite: 557 passed. `py_compile`, `compileall`, JSON
parsing, `git diff --check`, and authored-file whitespace checks passed. The
actual canonical tree remained 46 files / 1,275,143 bytes with tree SHA256
`c7f2fd6b0fc4585aaeeb91582a81940c9b33064cd501fae297c055c9dfee5b5e`; the
committed view, PRE_EVENT/POST_EVENT IDs, payload reference, and two-epoch
visibility were unchanged.

Generated result and its manifest are outside the repository under
`ARCANA_WORLD_QUALIFICATION_EVIDENCE/B6N8A/54ea550ecc623760ee5115a9033b38cb963a4584/validated-final-run/`.
Evidence manifest SHA256:
`e38ae74e2a67a5b0874a503b4dfce4cfa78c396af841396e14b400da7ea1d27c`.
Final decision:
`PASS_B6N8A_DIAGNOSTIC_SHADOW_PROPAGATION_INFORMATIVE`.

Authorization remains unchanged: `SECOND_DT_SELECTED = false`,
`dt2_years = null`, `T2_CREATED = false`, `B6O_authorized = false`,
`physical_rift_model_selected = false`, `mechanics_executed = false`,
`canonical_forward_propagation_executed = false`,
`topology_transition_executed = false`, and WORLD_HISTORY unchanged.
