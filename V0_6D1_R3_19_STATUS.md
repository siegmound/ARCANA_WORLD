# v0.6D1-R3.19 status

Status: **CANDIDATE — ready for local checks and canonical 125 ka -> 0 H0 run**.

Parent: R3.18 SEALED (`172/172`).

Scientific parameter changes: NONE.
Biology cadence changes: NONE.
Transport cadence changes: NONE.
Deep biological coupling: OFF.

Promotion requirement: constant-forcing generalized transport path must be bit-exact to SEALED R3.8.


## R3.19-R2 endpoint-support repair

The phase-aware transport forcing remains time-integrated over two 62.5 kyr phases. Discrete `accessible` topology is now bound to the exact 0 ka provider endpoint. After phase 2, any population on cells that are accessible in the phase-average forcing but inaccessible at exactly 0 ka is conservatively reconciled with the existing SEALED `remap_to_land` operator. This is an operator-order/topology binding repair, not a parameter or cadence change. The constant-forcing case with identical endpoint support remains bit-exact to SEALED R3.8.
