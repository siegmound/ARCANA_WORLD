# R6 T0 initial-motion generative-prior contract

Status: **precommitted before the canonical draw**. This is a t0-only, model-derived initialization for the synthetic ARCANA planet—not an empirical reconstruction of Earth at 210 Ma.

## Selected model family

Use a boundary-length-weighted graph-correlated Euler prior over the 12 already-governed synthetic plates. For weighted adjacency `A`, degree matrix `D`, normalized adjacency `W = D^-1/2 A D^-1/2`, and `L = I - W`, define `C = (I + L)^-1`. Three seeded, independent standard-normal component vectors are transformed by the deterministic Cholesky factor of `C`. This creates joint correlation through the actual plate adjacency graph; it does not claim empirical covariance or a force law.

The generated global surface-area-weighted RMS speed is drawn from `Uniform(2, 10) cm/year` and applied as a common scale after gauge removal. This range is an explicit ARCANA synthetic-model choice informed only by broad Earth-like speed context. It is not an observed global distribution, confidence interval, or measured 210 Ma value. The exact seed stream and single-draw rule are fixed in the JSON contract; no resampling or future-outcome selection is allowed.

The gauge removes the common rigid spin by area-weighted least-squares fit to surface velocities. It is purely kinematic—not a mantle reference frame, hotspot frame, torque balance, or mantle coupling.

## Alternatives adjudicated

- **Smooth global tangential field then rigid fit:** not selected because it needs a further correlation length/spectrum and residual policy not bound by R6.
- **Reduced force/torque model:** not selected because slab/subduction, ridge, drag, resistance, rheology, and force geometry are unbound; using it would imply unsupported causal physics.

Earth reconstruction literature reports context-dependent plate speeds and correlations with plate composition/boundary setting. It supports a broad plausibility check, not synthetic per-plate values or an R6 covariance. Rifting literature describes transient competition among forcing, resistance, and weakening. It does not supply a universal positive event delay for this synthetic system.

## Initial rift state and first interval

At exact t0, the synthetic initial condition is `RIFT_QUIESCENT_AT_EXACT_T0`: there is no active topology-changing rift at the instant the model starts. This says nothing about Earth at 210 Ma, and does not prohibit future rifting. Inherited weakness and susceptibility remain `UNKNOWN`; province/suture labels are not promoted to mechanical weakness.

Quiescence at one instant does not establish a positive post-t0 lead time. Eligibility remains tri-state, and no rift-initiation or split law supplies a first-event lower bound. Therefore the event guard blocks first-interval execution. No dt or first-interval execution contract is authorized. P03 remains unbound for renewal/change beyond a conditional initial constant-motion segment.

The 2–10 cm/year global RMS range and graph covariance are explicit model assumptions; sensitivity/ensemble treatment is future work and is not materialized here. Future canonicalization may not choose a realization based on its downstream geography, climate, resources, biology, or resemblance to Earth/A1.
