# R5.17-B7-A3F2-P7Q-PRE5C-LS

The authenticated ARCANA shoreline payload (`shoreline_state_I.npz`, SHA256 `f99e40c4…`) provides the governed `effective_land_mask`; `ocean_mask` is complementary. Its grid is 720×1440 at 0.25° with ascending latitude and longitude centers. The GUM grid is 347×720 at 0.5° and is bound independently from the PRE5C-GA GUM→GLiM crosswalk.

Exact geographic footprint overlap, with bottom-based row geometry and no resampling, yields 64,025 fully-land, 180,659 fully-ocean, 4,809 mixed and 347 outside-coverage GUM cells. Overlap conservation error is at most 1.11e-16 against tolerance 1e-12. No majority threshold is used; fully-ocean cells are not terrestrial-material eligible and mixed cells are not whole-cell materialized.

The cross-tabs are diagnostic only: Mu and coastal classes retain their source semantics and land-state conditions; Du/Wu/Wl/Wr remain non-material; Us remains unknown; Ea remains exact TRANSPORTED_AEOLIAN at source-semantic level. No parent material, soil, texture, profile, depth or temporal state was created. P7Q remains suspended and the Scientific Authority Register is unchanged.

Decision: `AUTHORIZE_P7Q_PRE5C_STATIC_SOURCE_BINDING_REBUILD_WITH_ARCANA_LAND_STATE_CONTRACT`.

Verdict: `PASS_P7Q_PRE5C_ARCANA_LAND_STATE_BINDING_ADJUDICATED`.
