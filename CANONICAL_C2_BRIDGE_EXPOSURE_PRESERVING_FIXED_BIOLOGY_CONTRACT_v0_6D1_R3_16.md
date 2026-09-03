# ARCANA WorldSim v0.6D1-R3.16
## C2 Bridge Exposure-Preserving Fixed-Biology Coupling Contract

### Scope
R3.16 starts from the R3.15 SEALED **250 ka** H0 biological checkpoint.  Its
canonical biological endpoint is **125 ka**, exactly one inherited 125 kyr
biology macrostep later.

R3.16 is the first stage allowed to cross the C2 environmental bridge start at
200 ka. It does **not** promote the R3.14 adaptive environmental clock to a
biology clock.

### Authorized multirate semantics
The inherited R3.7I/R3.8 biological operators remain one macrostep of 125 kyr.
Gene-flow exchange remains once per inherited biology step; lifecycle gates
remain on their inherited absolute cadence.

Environmental forcing for that macrostep is not the 125 ka endpoint state.
Instead R3.16 constructs a time-weighted effective D3 substrate by trapezoidal
integration over the R3.14 adaptive-clock partition between 250 and 125 ka.
This consumes all **150 governed 500-year C2 intervals from 200 to 125 ka** as
environmental exposure information without converting them to biology steps.

The remaining **10 x 500-year intervals from 125 to 120 ka** are recorded but
not consumed by biology. Therefore R3.16 does not claim an exact 120 ka
biological restart state.

### Hard prohibitions
- No 500-year gene-flow iterations.
- No 500-year speciation/extinction/fission/coalescence checks.
- No change to the 125 kyr biology cadence.
- No change to R3.7I/R3.8 scientific parameters.
- No Deep biological coupling.
- No richness, guild, hominin, sapience, or narrative target.
- No claim that C2 200-120 ka is sealed historical glacial chronology.

### Diagnostics, not authority
R3.16 also computes:
1. one-level quadrature refinement, used only to measure numerical exposure
   convergence;
2. an endpoint-only shadow branch, used only to quantify the information that
   would be lost by sampling the 125 ka environment for the entire macrostep.

Neither diagnostic can replace the canonical exposure-preserving branch.

### Canonical boundary
A PASS produces a restartable H0 checkpoint at **125 ka** with event-side:
`C2_BRIDGE_EXPOSURE_PRESERVED__125KA_FIXED_BIOLOGY_BOUNDARY__PRE_120KA_RESTART`.

The next stage must close the remaining 125->120 ka synchronization explicitly;
it may not silently relabel the 125 ka biological state as 120 ka.
