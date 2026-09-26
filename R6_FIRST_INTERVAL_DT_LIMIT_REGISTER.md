# R6 first-interval dt limit register

No positive first `dt` is certified. The 27,123.405-year rift horizon is conditional on fixed t0 Euler rates and is only an upper bound. The binding limiter is `TOPOLOGY_CONTACT_GUARD_UNBOUND`; angular and displacement policies cannot cure missing boundary/contact semantics.

| Candidate limit | Value | State |
|---|---:|---|
| Rift event guard | 27,123.405 years | Conditional upper bound |
| Motion segment validity | — | First step only; no numerical duration |
| Maximum angular rotation | — | No exact-rotation ODE stability limit; topology limit unbound |
| Maximum linear displacement | — | Unbound |
| Topology/contact guard | — | **Blocked; no positive partition-validity horizon** |
| Event localization | — | Production tolerance unbound |
| Output/checkpoint | — | Not an integration limit |

`dt_first`, active numerical limiter value, steps/Myr, and constant-dt 210 Myr count remain null. No round timestep or unsupported geometric fraction was selected.
