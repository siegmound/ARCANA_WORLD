# v0.6D1-R3.6B status

**Stage:** NEMO 2.4.2 Governed QTL-Ensemble Reference Benchmark  
**Parent:** v0.6D1-R3.6A  
**Scientific state mutation:** NONE  
**Canonical promotion:** NONE

## Implemented status
`PASS_QTL_ENSEMBLE_REFERENCE_IMPLEMENTATION`

R3.6B now contains the independent genetic realization layer needed to avoid calibrating ARCANA only against its own moment model.

## External execution status
`NEMO_2_4_2_ENGINE_RUN_PENDING`

This is an external evidence gate, not a code blocker. The package deliberately does not guess NEMO parameter-file semantics. A NEMO-2.4.2-validated template/source binding must be supplied before engine execution.

## Consequence
Do not modify `mu`, `b`, `q*=0.045`, gene-flow moment mixing or ceiling yet.
