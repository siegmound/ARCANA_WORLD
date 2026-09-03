# R3.10 Full CHA-1 High-Resolution Rebased Event Evidence Audit

## Seal verdict

`PASS_R310_CANONICAL_CHA1_HIGH_RES_REBASED_EVENT_BRIDGE__65P5MA_POST_CHA1_RESTART_BOUNDARY_SEALED`

R3.10 starts from the exact sealed R3.9 state at `66.0 Ma PRE_IMPACT`, applies CHA-1 through the dedicated high-resolution event provider, and terminates at the restartable `65.5 Ma POST_CHA1_500KY` boundary. Ordinary 125 kyr biology does not cross the discontinuity.

## Canonical emergent outcome

- pre-impact species: **305**
- direct CHA-1 extinctions: **212**
- survivor species: **93**
- extinction fraction: **0.695081967213**
- surviving components: **207**
- extinction-time range: `0.00528972410529` to `19.8777470052` years
- median extinction time: `3.00931429817` years
- all direct extinctions within acute 20-y window: **True**
- endpoint age: **65.5 Ma**
- event side: **POST_CHA1_500KY**

The old D2.2 31-survivor identity set is not used. The 93 survivors are produced by the rebased 305-species state under the predeclared R3.10 hazard transfer.

## D2.2 provenance and event authority

Historical D2.2 remains the authority for recovered CHA-1 event semantics and quantitative anchors. Its original executable solver bytes were not recovered, so R3.10 explicitly does **not** claim source/bit identity with the historical solver. R3.10 uses `D2_2_RAW_ANCHORED_REBASED_EVENT_PROVIDER` semantics.

- historical D2.2 archive SHA-256: `42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8`
- event window: `-100 kyr -> +500 kyr`
- materialized reporting checkpoints: **917**
- historical survivor-ID lookup: **forbidden / unused**
- per-step Bernoulli mortality: **unused**
- forced guild survivor: **unused**
- exact-site distance mortality: **disabled**, because exact impact paleocoordinates remain provisional

Recovered physical anchors close to machine precision. Maximum relative anchor error is `9.289e-16`.

## Food-web reduced-order closure

Recovered D2.2 minima are reproduced independently of the R3.9 survivor outcome:

- plant minimum: `0.39500002038368903` (oracle 0.395)
- herbivore minimum: `0.43301538929487277` (oracle 0.433)
- mesopredator minimum: `0.7819996593328783` (oracle 0.782)
- apex minimum: `0.9740000223988694` (oracle 0.974)

All four reduced food-web coordinates recover to `1.0` at the +500 kyr endpoint.

## Genetic / restart integrity

- serialization identity: **PASS, exact**
- deterministic hazard repeat identity: **PASS**
- post-event q max: `0.04575032753015043`
- sealed q ceiling: `0.08`
- q headroom: `0.03424967246984957`
- survivor trait/VA/adaptive-coordinate state is inherited, not reset
- `S` remains finite, non-negative within tolerance, symmetric and zero-diagonal
- population remains finite/non-negative
- population on inaccessible cells is exactly zero
- total population closure is exact within floating arithmetic

No mutation-supply parameter, Riccati coefficient, q ceiling, K semantics, migration/speciation authority, or Deep coupling setting is changed by R3.10.

## Predeclared sensitivity audit

The sensitivity grid was not used to choose the canonical branch. The canonical `species_risk_amplitude=0.25` and `guild_hazard_scale=1.0` were fixed before the rebased outcome was generated.

- survivor range across the predeclared grid: **75–111**
- canonical survivors: **93**
- within every fixed risk-amplitude branch, increasing hazard scale monotonically does not increase survivor count
- historical survivor IDs are unused throughout the ensemble

## Formal and regression closure

- formal seal audit: **67/67 PASS**
- full inherited regression suite: **271/271 PASS**
- immediate R3.10 + R3.9 + R3.8 + R3.7I regression: **34/34 PASS**

The full suite was executed in deterministic segments because a single aggregated pytest process exceeded the environment command timeout. No test was removed, weakened, xfailed, or skipped to obtain the result.

## Canonical hashes

- R3.10 summary: `622ef056887e28e1aaa98894f5de241cb6e34e4db671050163187da6a453037f`
- R3.10 sensitivity: `996494c7fe223c6760ea287694d05b7eefff91e0e9f6f8e38e1552668988f1cd`
- R3.10 physical-anchor audit: `ac9c393cb3fa6c5ea54403972089fb60f7580040df82143b00b1bafe4f6b21be`
- post-CHA1 checkpoint JSON: `5ea3f6cad09e2b6e09a6ff795a89dbd370ca0ca049f20c04e8d53fbeb8dd6469`
- post-CHA1 checkpoint NPZ: `d31ae5aaeb53422809e173c20308e69af334ef8d2d535484ae51141b9dff58a8`
- R3.10 runtime source: `4380436e520a74b2aace8189bcb90ec7662f136054e6a368c6cd586efb0bd804`
- formal audit: `f6060f16094175750f269d56906a60b485497c1054e7686b2c6ab703eb0dd9fc`
- 271-test regression evidence: `0d8edb4fc5754410693002bc9f0c7db5c51f5274b400d13d0b6f790a92f93d4f`

## Authority after seal

The canonical H0 continuation boundary is now `65.5 Ma POST_CHA1_500KY`. CHA-1 is already applied and must never be applied again downstream. R3.11 may resume ordinary production-sealed ecology/genetics/speciation from this checkpoint, with Deep biological coupling still OFF and without inserting narratively desired species.
