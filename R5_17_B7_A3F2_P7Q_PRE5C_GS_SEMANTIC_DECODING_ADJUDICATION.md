# R5.17-B7-A3F2-P7Q-PRE5C-GS

Official GUM v1.0 semantics were recovered from Börker et al. 2018, DOI `10.1002/2017GC007273`, Appendix A2/Table A1, and dataset DOI `10.1594/PANGAEA.884822`. The code is `XXYYZZAADD`; `XX` is sediment type and `nn` means missing information.

The real DBF field is `XX` (C, width 254), non-null in all 911,551 records. All 41 official codes occur in the DBF; the cached raster has 39 classes and omits `Or` and `Wr`. Source semantics are separated from ARCANA mapping: mixed classes remain unresolved, ice/water are non-material, `Us` is unknown, and marine/coastal classes remain land-state gated.

The repaired mapping accounts for all 41 codes exactly once: 20 exact (including `Ea → TRANSPORTED_AEOLIAN`), 2 conditional, 7 mixed/unresolved, 4 non-material, 1 unknown, and 7 land-state gated.

YY/ZZ/AA/DD are source metadata only. No texture, mineral fractions, temporal trajectory, physical depth, profile, land-state binding or parent-material state was generated. PRE5C-GA geometry is unchanged.

Decision: `AUTHORIZE_P7Q_PRE5C_LAND_STATE_BINDING_GATE_WITH_GUM_SEMANTIC_REGISTRY`.

Verdict: `PASS_P7Q_PRE5C_GUM_CLASS_SEMANTIC_DECODING_ADJUDICATED`.
