# ARCANA WorldSim v0.6D1-R3.26 — H3 Quantitative-Genetics Bridge

## Scope

R3.26 is the single-stage H3 structural-potential bridge for the six H2-priority lineages sealed by R3.25.

It does **not** create the human lineage, does not replay culture, and does not modify H0, CHA-2, R3.23, R3.24 or R3.25.

## Canonical H3 algebra

`U_R = (Z_R - 0.35 Z_inf) / sqrt(1 - 0.35^2)`

`Z_H = sqrt(0.75) Z_inf + sqrt(0.15) U_R + sqrt(0.10) epsilon_mar`

`epsilon_mar` is persistent within an individual and is not redrawn per timestep.

The neutral reference generator uses independent standard-normal `Z_inf`, `U_R`, and `epsilon_mar`; `Z_R` is reconstructed so `corr(Z_inf,Z_R)=0.35`.

## Reproduction kernel

For the bridge-validation kernel, `Z_inf` and `U_R` are upstream additive breeding values. Under random mating the offspring value is

`B_child = 0.5(B_mother+B_father) + sqrt(0.5) * segregation_noise`.

This preserves unit stationary variance and gives parent-offspring correlation 0.5 for each breeding value. `epsilon_mar` is a fresh persistent individual residual for the offspring, not a CB label and not a timestep noise term.

No parental CB label is accepted by the reproduction API.

This neutral kernel is a bridge validation/reference model; mutation, selection, assortative mating, local differentiation and demographic history belong to the later macro-evolution replay and are not invented here.

## Hard ceiling

`J_hard` is continuous and primary. It is mapped from `Z_H` using the ratified monotone PCHIP in ln(J) with endpoint tangent tails. CB1–CB12 is assigned only afterward as a diagnostic label.

No candidate lineage receives a shifted or renormalized H3/CB distribution in R3.26.

## Candidate semantics

The six H2 lineages retain H2 biological-support diagnostics. These may indicate future realization feasibility, but **may not alter Z_H or J_hard in R3.26**.

Therefore R3.26 is allowed to conclude that all six are H3-bridge compatible. It must not eliminate a lineage because a manually tuned CB distribution looks inconvenient.

## Deep invariant

Deep biological coupling remains OFF. Source exposure or acquired realization may never directly write into inherited H3 state.

## Output boundary

R3.26 prepares the genetics needed for the next macro-evolution stage. It does not materialize `HUMAN_200KA`.
