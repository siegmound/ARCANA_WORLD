# R6 PRE_ORBDATA FEG Runtime Compatibility Closure

Decision: `PASS_R6_PRE_ORBDATA_FEG_RUNTIME_COMPATIBILITY_AND_MATERIALIZATION`

This materializes a production ShellSet FEG from governed T0/runtime inputs. It does not run ShellSet, OrbData, mechanics, or forward evolution.

## Evidence

- `node_count`: `64442`
- `triangle_count`: `128880`
- `fault_count`: `0`
- `canonical_mesh_sha256`: `"6f7804ca22130a183c0abf317dce300bcdcf3328cfe6469ba0540386f98cd5ad"`
- `runtime_coordinate_frame_id`: `"ARCANA_SHELLSET_RUNTIME_RX_PLUS_0P5_DEG_V1"`
- `max_absolute_runtime_latitude_deg`: `89.50000000000013`
- `raw_feg_sha256`: `"34b81c0df350d3b9a4c7df526c9171c89fe2d44d7e17b8662f5a92a9ee4c40b6"`
- `normalized_feg_sha256`: `"403fae9cbac71d62863788dbd2d9376497550677d8ce1d20ab1aef613c59d16c"`
- `runtime_package_sha256`: `"2dc83a759d4cdd4851ad57a37fc725841da24f0f2ca4312391283348703d3584"`
- `surface_package_sha256`: `"31cf4fb77e6fc12df1716805eeb4b46059ca35bbcd7b3bc305efa2e8afef3534"`
- `heat_flow_projection_replay_sha256`: `"3e9a9b86048f65d657e3afa2ccc5054d2bcd96ce5c8d5d7eba55a797e4025e8b"`
- `frame_proof`: `{"all_checks_pass": true, "determinant": 1.0, "frame_id": "ARCANA_SHELLSET_RUNTIME_RX_PLUS_0P5_DEG_V1", "max_edge_angular_difference_rad": 1.3322676295501878e-14, "max_inverse_roundtrip_error": 1.1043249648068354e-14, "max_orthonormal_error": 4.777107916652558e-19, "max_spherical_triangle_area_difference_sr": 6.638027801042501e-17, "max_transform_error": 1.1046719095020308e-14, "max_unit_vector_error": 2.220446049250313e-16, "maximum_absolute_runtime_latitude_deg": 89.50000000000013, "minimum_runtime_spherical_triangle_area_sr": 2.658086063829549e-06, "no_nan_inf": true, "orthonormal": true, "triangle_count": 128880, "unique_mesh_edge_count": 193320, "zero_area_triangles": 0}`
- `physical_field_equality`: `{"crust_thickness_exact_to_runtime_package": true, "heat_flow_exact_to_runtime_package": true, "mantle_lithosphere_thickness_exact_to_runtime_package": true}`
- `source_hashes_unchanged`: `true`
- `gates`: `{"canonical_state_changed": false, "dt_selected": false, "forward_evolution_authorized": false, "mechanics_authorized": false, "runtime_authorized": false, "t1_created": false}`

## Preserved gates

- `runtime_authorized`: `false
- `mechanics_authorized`: `false
- `forward_evolution_authorized`: `false
- `dt_selected`: `false
- `t1_created`: `false
- `canonical_state_changed`: `false

No runtime or mechanics qualification is claimed.
