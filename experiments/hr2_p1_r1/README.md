# R1-I0 version0.1 — isolated initial implementation

Manufactured-only scalar-volume FV; no imports from V1. Explicit staged launcher
scripts/r6_hr2_p1_r1_i0.py, tests outside default discovery in hr2_p1_r1_checks.
Geometry integrates15 quartic log-chart moments and covariant face derivatives,
SVD reconstructs common sparse face weights. Shared physical flux rejects any
uncertified packet. The conservative limiter uses exact fractions of represented
binary64 transfers for donor/receiver budgets and one final simultaneous gather.

The independent certificate currently uses conservative analytic interval ranges,
not a validated high-order quadrature remainder rule. It may fail the sealed
moment/face widths even when two Gauss orders agree. Such a failure must BLOCK
before sphere state flux/evolution. A uniform derivative-bound certificate is
also not yet implemented; no path here can silently promote rank to accuracy.
The limiter is executable in independent rational fixtures; spherical qualification
and native/B0 are unestablished. No clipping, mass normalization, harmonic-specific
coefficient, automatic patch enlargement, retry, new dataset or default dispatch.

All tests start CREATED_NOT_RUN; consult actual external I0 receipts for executed
scope. Only16x8/32x16 are authorized by the current driver; no64x32..256x128 or
3Y/10Y temporal/native campaign is performed under I0. A coefficient NPZ is a
provisional geometry packet, not a qualified native numerical checkpoint.
