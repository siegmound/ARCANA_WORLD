# NEMO 2.4.2 selection-source binding audit — R3.7C-R1

Verified against the NEMO 2.4.2 source surface used during this repair:

- standalone `viability_selection` acts on offspring;
- `breed_disperse` performs `doAgingInWFpop()` internally when Wright-Fisher is enabled;
- `breed_selection_disperse` combines breeding, dispersal and selection and performs the WF generation transition after the composite operation;
- `breed_selection_disperse` inherits the dispersal machinery and uses the `breed_disperse_*` parameter family;
- Gaussian selection computes `exp(-0.5 * (z-optimum)^2 / selection_variance)` in the univariate case;
- `selection_fitness_model absolute` is explicitly supported.

Therefore R3.7C-R1 binds the selected branch to `breed_selection_disperse` and keeps the matched neutral branch on `breed_disperse`.
