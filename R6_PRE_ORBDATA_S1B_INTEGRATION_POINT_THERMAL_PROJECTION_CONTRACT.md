# R6 PRE_ORBDATA S1B — Integration-Point Thermal Projection

## Rule

The selected numerical rule is `EVALUATE_THEN_INTERPOLATE_FEM_THERMAL_FIELD`.
For each requested physical depth, evaluate each of an element's three nodal
piecewise columns independently: layer 1 above that node's Moho, layer 2 from
Moho through LAB, and the LAB-anchored adiabat below LAB:

`T(z) = T_LAB exp(alpha_mantle * 9.82 * (z-LAB) / Cp_mantle)`.

The integration-point temperature is the sum of the three nodal temperatures
weighted by the existing FEM shape functions. Continuous material properties
follow the same evaluate-at-node-then-interpolate order, after selecting each
node's active phase. Discrete material/phase identifiers remain nodal
diagnostics and are never interpolated. Every integration-point property is a
`NUMERICAL_RUNTIME_EFFECTIVE_PROPERTY`; this creates no canonical IP material.
This is a numerical projection contract only; it grants no physical or
canonical geological authority.

## Required invariants

- One-hot weights reproduce that node's evaluated temperature.
- Both piecewise polynomial joins and the LAB-to-adiabat join are continuous.
- Homogeneous elements reproduce their homogeneous nodal profile; mixed
  elements remain finite and within their nodal support bounds.
- ARCANA values bypass legacy `geothC/geothM` fitting and `temLim` clipping.
- `chemical_delta_rho` remains zero and the stock path remains unchanged.
- Missing or malformed package data fails closed.

The canonical topology diagnostic reports 1,816 mixed crust-material elements
and 325 mixed ridge/ocean elements. These counts describe numerical support;
they do not define new physical materials.

## Implementation status

The shared nodal and FEM evaluator is implemented in
`external/ShellSet-v1.1.0/src/MOD_ArcanaRuntime.f90`. S1B-I provides the
marker+package lifecycle. S1B-II wires FillIn, ARCANA Squeez, OneBar, and the
`iConve=5` temperature predicate to that evaluator. The ARCANA path bypasses
legacy geotherm reconstruction and temLim; the 200 K OneBar floor is a
fail-closed bound check, never a temperature clamp. A temporary ARCANA barrier
runs after FillIn and before Fixed/Pure, so remaining S1B-III consumers cannot
execute in ARCANA mode. Stock paths remain in their legacy branches. Complete
Shells mechanics remains **disabled** pending S1B-III. No FAIR runtime/build
result is claimed; Windows validation is source-level only and has not run
OrbData or SHELLS.

The Python numerical reference tests exercise only the closed projection
equations; they do not execute or qualify the Fortran evaluator.

All authorization gates remain false: `PRE_ORBDATA_ready`,
`t0_orbdata_executed`, `shellset_mechanics_authorized`, `dt_selected`,
`t1_created`, and `forward_evolution_authorized`.
