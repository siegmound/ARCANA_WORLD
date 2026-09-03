# NEMO dispersal semantics audit — R3.6B

## Finding
ARCANA R3.6A stores an explicit effective-exchange matrix where off-diagonal entries are exchanged fractions and row sums may be `< 1`.

NEMO forward dispersal matrices are probability matrices: rows must sum to one, with `d_ij` interpreted as movement from source patch `i` to destination patch `j` under the forward `disperse` life-cycle event.

## Governed conversion
R3.6B does not rescale ARCANA migration. It preserves every off-diagonal entry and derives only the stay-home probability:

`D_NEMO[i,j] = G_ARCANA[i,j]` for `i != j`

`D_NEMO[i,i] = 1 - sum_{j != i} G_ARCANA[i,j]`

Thus each NEMO row is exactly stochastic while ARCANA exchange semantics remain unchanged.

## Guard
Non-zero diagonal ARCANA exchange input is rejected so self-retention cannot be double-counted.

## Upstream evidence checked 2026-08-28
- NEMO 2.4.2 official site/manual and code documentation.
- NEMO user-list clarification of forward dispersal: matrix rows are source patches and rows sum to one.
