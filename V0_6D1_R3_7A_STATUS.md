# ARCANA WorldSim v0.6D1-R3.7A status

**Stage:** Segregation-Potential Initialization, Evolution & Deme-Lifecycle Calibration

**Verdict:** `PASS_LIFECYCLE_ANALYTIC_AND_PARENT_NEMO_DRIFT_CLOSURE__NEMO_B2_CHAIN_CALIBRATION_PENDING`

Closed analytically/in code:
- minimum-information 210 Ma initialization;
- same-species reproductive authority mask;
- directional-selection latent-coordinate mapping with explicit `K_eff`;
- exact reuse of D3.3A drift loss as expected neutral `S` divergence;
- zero invented deterministic mutation displacement;
- migration/reconnection transformation of the reduced Euclidean state;
- exact fission clone semantics;
- population-weighted coalescence/barycenter semantics;
- speciation identity-only transition;
- remap invariance and deme removal;
- B2 NEMO 2.4.2 executable phase binding.

Independent parent evidence already supporting the lifecycle:
- NEMO B0 drift median observed/predicted ≈ 1.1044;
- maximum deviation ≈ 24.46% with finite-N and only two replicates;
- 64-QTL `K_eff` reference range ≈ 46.65–63.50.

Pending:
- execute B2 NEMO chain on WSL2;
- use B2 isolation/reconnection evidence to review `K_eff` and lifecycle closure;
- production runtime binding remains forbidden until that review;
- short World-1 replay and 210→150 Ma rerun remain blocked.

Governance:
- canonical write: NO
- automatic NEMO calibration: NO
- production `K_eff`: NOT AUTHORIZED
- production runtime binding: NO
- `mu`/`b`/`q*` change: NO
- ceiling change: NO
