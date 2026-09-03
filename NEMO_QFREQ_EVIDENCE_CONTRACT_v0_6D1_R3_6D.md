# NEMO qfreq evidence contract — v0.6D1-R3.6D

R3.6D parses NEMO quantitative-allele-frequency (`.qfreq`) output rather than inferring variance from log prose.

Expected header:

`pop trait locus allele g...`

One ARCANA trait is executed per NEMO job. The parser therefore requires `trait == 1` and exact locus coverage.

For each recorded generation and patch, using the original ARCANA full locus effect `a_l` and NEMO's increasing-allele frequency `p_l`:

`mean = sum_l a_l (2 p_l - 1)`

`V_A = sum_l 2 a_l^2 p_l (1-p_l)`.

The parser stores:

- generation IDs;
- patch IDs;
- allele-frequency tensor;
- reconstructed trait mean;
- reconstructed additive variance.

Every evidence bundle carries experiment SHA, engine run ID, stdout/stderr hashes and qfreq hash.

A successful executable return without qfreq is **not** treated as successful quantitative-genetics evidence.

## R2 final-generation persistence repair
Real NEMO 2.4.2 smoke evidence established that a successful engine run does not persist `.qfreq` unless `TTQFreqExtractor` is invoked at the final generation. R3.6D R2 therefore schedules the primary final-only observation with `quanti_freq_logtime = generations` and rejects custom logtimes that miss the final generation. This changes evidence scheduling only, not the biological experiment.
