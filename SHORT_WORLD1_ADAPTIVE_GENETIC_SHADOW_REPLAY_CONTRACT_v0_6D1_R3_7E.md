# v0.6D1-R3.7E — Short World-1 Adaptive Genetic Shadow Replay & K-Envelope Sensitivity Gate

## Scope
R3.7E is the first World-1 replay that carries the reduced genetic state from R3.7–R3.7D alongside the authoritative R3.5 runtime. It remains observation-only and cannot write canonical state.

## Governed window
The full gate is 210→205 Ma: 5 Myr, 40 biological intervals at the sealed 125 kyr cadence. A 210→209 Ma diagnostic smoke is allowed only for implementation verification.

## Parent authority preserved
Trait response is produced by the existing R3.4/R3.5 selection operator. Gene-flow edges, current-species identity, RI and the 45% aggregate exchange cap remain unchanged. D3.3A `mu`, nonlinear homeostasis `b`, drift mapping and q ceiling remain unchanged. Fission, coalescence, extinction, speciation and paleogeographic remapping occur only when emitted by the parent runtime.

## Shadow state
Each variant carries `V_A,within`, ancestry/LD covariance, neutral segregation potential S, and adaptive coordinate h. Selection maps the already-authorized trait displacement into h using the R3.7D envelope K_LOW/K_CENTER/K_HIGH. Migration uses the exact parent exchange transition but the R3.7 segregation-aware variance partition. The D3.3A non-flow ODE is then applied to shadow `V_A`; only the D3.3A drift component is transferred into neutral S. Mutation does not invent deterministic allele-frequency displacement.

## Recombination
`r=0.5` is retained as the R3.7/NEMO reference architecture for the ancestry/LD shadow reservoir. It is not a World-1 production constant and cannot be promoted by this stage.

## Gate semantics
R3.7E may pass the short shadow gate only if the observation bindings preserve the parent canonical state exactly, all three variants remain mathematically valid, and no variant changes the existing qualitative q-ceiling/headroom decision. K-envelope spread is reported, not calibrated against a new arbitrary tolerance.

Passing R3.7E does not authorize a production runtime replacement.
