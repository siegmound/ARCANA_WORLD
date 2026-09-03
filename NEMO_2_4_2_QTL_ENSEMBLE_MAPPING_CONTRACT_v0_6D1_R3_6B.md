# NEMO 2.4.2 QTL-Ensemble Mapping Contract — R3.6B

## Why an ensemble is mandatory
An ARCANA deme stores trait first/second moments, not a unique diploid genome. Therefore `(mean, V_A)` cannot be inverted to a unique QTL population without introducing arbitrary genetic information.

R3.6B maps each target state to a reproducible ensemble of compatible genetic realizations.

## Reference QTL model
For each trait, each locus is diploid and diallelic. Let genotype count `g` be 0, 1 or 2 and additive effect be `a`.

`A_l = a (g - 1)`

For allele-1 frequency `p`:

`E[A_l] = a (2p - 1)`

`Var[A_l] = 2 a^2 p(1-p)`

Across loci, linkage-equilibrium expected moments are sums of the locus moments.

Effects are shared across patches. Patch-specific allele frequencies carry inherited between-deme mean differences.

## Governed fitter
R3.6B uses `scipy.optimize.least_squares` to fit a two-parameter smooth allele-frequency profile per patch and trait. The low-dimensional profile prevents arbitrary overfitting of every locus independently.

The expected genetic mean and expected additive variance must reproduce the target moments to numerical tolerance before a realization is accepted.

## Sampled genotypes
A deterministic seeded balanced diploid sampler produces an explicit finite-population realization for audit. Its NPZ is ARCANA evidence only; it is NOT falsely labelled as a native NEMO import format.

Executable NEMO binding requires a version-validated NEMO 2.4.2 input template/source mapping.
