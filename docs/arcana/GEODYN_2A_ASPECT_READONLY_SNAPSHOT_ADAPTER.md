# GEODYN-2A — ASPECT read-only snapshot adapter

Date: 2026-10-27
Repository branch: `r6/multiphysics-integration-20261026`
Implementation baseline: `af3f526a46d1638247f9cfa004be3e49dc82770b`
Verdict: `GEODYN_2A_ASPECT_READONLY_ADAPTER_LOCAL_TESTS_PASS__FAIR_VALIDATION_PENDING`

## Scope and result

Added `src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py` and focused synthetic tests in `tests/test_r6_aspect_snapshot_reader.py`. The standard-library reader accepts a PVD collection referencing VTU or PVTU snapshots, but only one PVD part/rank, one Piece per VTU, and one PVTU Piece source. It supports inline ASCII and inline Base64 binary arrays, with or without VTK zlib block compression. It rejects appended data, unsupported compression/layouts, unsafe paths, missing files, malformed dimensions/connectivity and non-finite values.

Decoded coordinates, connectivity, offsets, cell types and point/cell arrays are returned only by the explicit `read_snapshot()` API. `metadata()` and `audit()` expose temporal/provenance metadata, point/cell counts, numeric coordinate bounds and VTK cell-type counts without array values. The parser computes streaming SHA256 hashes of the source files and a canonical numeric mesh fingerprint, then reports mesh/schema stability, invariant/dynamic arrays, zero-valued invariant fields and numerically identical fields. These labels are descriptive checks only; they do not assign physical meaning. The audit adds an explicit field annotation when `point:T` is detected as a zero-valued invariant, while leaving the initial-expression discrepancy unexplained.

All records are fixed to `SYNTHETIC_ENGINEERING_ONLY` and are separate dataclasses, not `DomainStateEnvelope`. Units and timestamps are retained as declared; no conversion or ARCANA support remapping occurs. The reader does not mutate inputs or write to canonical storage. Caller-supplied run/build provenance is retained as an unauthenticated claim. Rank count must be explicitly declared as one; VTK bytes cannot independently authenticate MPI execution provenance.

Reader limits bound file size, snapshot count, points/cells, individual and aggregate decoded array bytes, value count, and an estimated Python materialization size. These are parser guardrails, not OS memory quotas. The audit reads one snapshot at a time and retains only metadata across the series.

The supported inline ASCII/binary/appended distinctions follow the VTK XML writer format modes ([official VTK writer reference](https://vtk.org/doc/nightly/html/classvtkXMLWriterBase.html)); the adapter intentionally implements only the modes listed above.

## FAIR reference evidence and authority

The following is the operator-reported reference, not data independently imported or rehashed on Windows:

- FAIR rigid-shear output: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2_RIGID_SHEAR/20261026T234423Z_transient_rank1`.
- Numeric audit: `/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2C_NUMERIC_AUDIT/20261027T000139Z_numeric_audit`.
- Reported ASPECT version/source: `3.2.0-pre`, commit `30eb77ee5da186137d436dbad35c6cb3cab64b69`.
- Reported 11 snapshots span 0 to 1.0142299266 s; solver completion is 1.098612289 s. No final snapshot at solver completion was reported. The adapter accepts solver completion as metadata and never fabricates an additional field snapshot.
- Reported mesh: 1152 points, 512 quadrilaterals, X=[0,2], Y=[0,1], Z=0; nine Float32 point fields with stable schema. `velocity`, `p`, `gravity`, `density_comp` were reported dynamic; `density` was byte-identical to `density_comp` in each source snapshot. `T`, `specific_heat`, `thermal_expansivity` were reported constant at zero and `viscosity` constant at one.

The audit output annotates a zero-valued invariant `point:T` as observed constant zero and explicitly records that the discrepancy from the initial expression remains unexplained. This is a data observation, not a physical explanation. No FAIR validation of this adapter has been performed.

## Local verification

Windows Python 3.12.10:

- `python -m py_compile src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py tests/test_r6_aspect_snapshot_reader.py` — PASS.
- `python -m pytest -q --basetemp=outputs/_pytest_aspect_snapshot_reader_20261027_10 tests/test_r6_aspect_snapshot_reader.py` — 21 passed, 1 skipped. The skip is the external-symlink test because symlink creation is unavailable in this Windows environment. Path traversal is covered; the symlink escape branch remains pending an environment that permits the fixture.
- `git diff --check` — PASS.
- Both new source files decode as UTF-8 and use LF line endings.

The fixtures cover ASCII, inline binary, zlib, byte order, geometry/fields, timestamp ordering, malformed/non-finite arrays, duplicates/invariants/dynamics, mesh/schema changes, path traversal, PVTU restrictions, memory bounds, missing/corrupt payloads, no input mutation, caller-claimed provenance and CLI JSON without array embedding. Tests do not require ASPECT or NumPy.

## FAIR read-only handoff (not executed)

After the exact source commit is published and available in the FAIR Git object database, use the following read-only handoff. It does not switch or update the existing FAIR worktree: source/tests are extracted from the exact commit into a fresh evidence directory. It fails on an evidence-directory collision or unless exactly one top-level PVD is found.

```bash
set -euo pipefail
GEODYN_2A_COMMIT="<full-local-commit-sha>"
FAIR_RIGID_SHEAR_DIR="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2_RIGID_SHEAR/20261026T234423Z_transient_rank1"
NUMERIC_AUDIT="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2C_NUMERIC_AUDIT/20261027T000139Z_numeric_audit/NUMERIC_AUDIT.json"
EVIDENCE_ROOT="/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/GEODYN_2A_READONLY_ADAPTER"
EVIDENCE_DIR="$EVIDENCE_ROOT/${GEODYN_2A_COMMIT}_$(date -u +%Y%m%dT%H%M%SZ)"
test ! -e "$EVIDENCE_DIR"
test -f "$NUMERIC_AUDIT"
mkdir -p "$EVIDENCE_DIR/source"
git cat-file -e "$GEODYN_2A_COMMIT^{commit}"
git archive "$GEODYN_2A_COMMIT" src/arcana_worldsim tests/test_r6_aspect_snapshot_reader.py | tar -x -C "$EVIDENCE_DIR/source"
cp -- "$NUMERIC_AUDIT" "$EVIDENCE_DIR/NUMERIC_AUDIT.input.json"
printf 'source_commit=%s\nrun_dir=%s\nnumeric_audit=%s\n' \
  "$GEODYN_2A_COMMIT" "$FAIR_RIGID_SHEAR_DIR" "$NUMERIC_AUDIT" \
  > "$EVIDENCE_DIR/RUN_METADATA.txt"
python --version > "$EVIDENCE_DIR/runtime.txt" 2>&1
python -m pytest --version >> "$EVIDENCE_DIR/runtime.txt" 2>&1
mapfile -t PVD_FILES < <(find "$FAIR_RIGID_SHEAR_DIR" -maxdepth 1 -type f -name '*.pvd' -print | sort)
printf 'pvd_count=%s\n' "${#PVD_FILES[@]}" >> "$EVIDENCE_DIR/RUN_METADATA.txt"
test "${#PVD_FILES[@]}" -eq 1
find "$FAIR_RIGID_SHEAR_DIR" -maxdepth 2 -type f \
  \( -name '*.pvd' -o -name '*.pvtu' -o -name '*.vtu' \) -print0 | sort -z | xargs -0 -r sha256sum \
  > "$EVIDENCE_DIR/VTK_BEFORE.sha256"
if python -m pytest -q --basetemp="$EVIDENCE_DIR/pytest-tmp" \
  "$EVIDENCE_DIR/source/tests/test_r6_aspect_snapshot_reader.py" \
  > "$EVIDENCE_DIR/pytest.log" 2>&1; then PYTEST_EXIT=0; else PYTEST_EXIT=$?; fi
printf 'pytest_exit=%s\n' "$PYTEST_EXIT" >> "$EVIDENCE_DIR/RUN_METADATA.txt"
if [ "$PYTEST_EXIT" -ne 0 ]; then
  sha256sum "$EVIDENCE_DIR/pytest.log" "$EVIDENCE_DIR/NUMERIC_AUDIT.input.json" \
    > "$EVIDENCE_DIR/SHA256SUMS"
  exit "$PYTEST_EXIT"
fi
if python "$EVIDENCE_DIR/source/src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py" \
  "${PVD_FILES[0]}" \
  --run-id GEODYN_2_RIGID_SHEAR_20261026T234423Z \
  --mpi-rank-count 1 \
  --time-unit s \
  --time-unit-source "operator-reported PVD/solver audit; verify against source files" \
  --solver-completed-time 1.098612289 \
  --provenance aspect_version=3.2.0-pre \
  --provenance aspect_commit=30eb77ee5da186137d436dbad35c6cb3cab64b69 \
  --provenance provenance_authority=operator-reported \
  > "$EVIDENCE_DIR/ADAPTER_AUDIT.json"; then CLI_EXIT=0; else CLI_EXIT=$?; fi
printf 'adapter_cli_exit=%s\n' "$CLI_EXIT" >> "$EVIDENCE_DIR/RUN_METADATA.txt"
if [ "$CLI_EXIT" -ne 0 ]; then
  sha256sum "$EVIDENCE_DIR/pytest.log" "$EVIDENCE_DIR/NUMERIC_AUDIT.input.json" \
    "$EVIDENCE_DIR/ADAPTER_AUDIT.json" > "$EVIDENCE_DIR/SHA256SUMS"
  exit "$CLI_EXIT"
fi
python - "$EVIDENCE_DIR/ADAPTER_AUDIT.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as stream:
    result = json.load(stream)
assert result["classification"] == "SYNTHETIC_ENGINEERING_ONLY"
assert result["snapshot_count"] == 11
assert result["snapshots"][0]["time_value"] == 0.0
assert result["snapshots"][-1]["time_value"] == 1.0142299266
assert result["solver_completed_time"] == 1.098612289
assert result["final_snapshot_at_solver_completion"] is False
assert result["mesh_stable"] is True and result["schema_stable"] is True
assert all(item["point_count"] == 1152 and item["cell_count"] == 512 for item in result["snapshots"])
assert all(item["cell_type_counts"] == {"9": 512} for item in result["snapshots"])
assert all(item["coordinate_bounds"] == [[0.0, 2.0], [0.0, 1.0], [0.0, 0.0]] for item in result["snapshots"])
point_names = {field["name"] for field in result["snapshots"][0]["field_metadata"] if field["association"] == "point"}
assert len(point_names) == 9
assert {"velocity", "p", "gravity", "density", "density_comp"} <= point_names
assert {"T", "specific_heat", "thermal_expansivity", "viscosity"} <= point_names
assert {"point:velocity", "point:p", "point:gravity", "point:density", "point:density_comp"} <= set(result["dynamic_fields"])
assert {"point:T", "point:specific_heat", "point:thermal_expansivity", "point:viscosity"} <= set(result["invariant_fields"])
assert {"point:T", "point:specific_heat", "point:thermal_expansivity"} <= set(result["zero_valued_invariant_fields"])
assert ("point:density", "point:density_comp") in [tuple(pair) for pair in result["numerically_duplicate_fields"]]
print("reported-summary numeric assertions: PASS")
PY
find "$FAIR_RIGID_SHEAR_DIR" -maxdepth 2 -type f \
  \( -name '*.pvd' -o -name '*.pvtu' -o -name '*.vtu' \) -print0 | sort -z | xargs -0 -r sha256sum \
  > "$EVIDENCE_DIR/VTK_AFTER.sha256"
cmp "$EVIDENCE_DIR/VTK_BEFORE.sha256" "$EVIDENCE_DIR/VTK_AFTER.sha256"
sha256sum "$EVIDENCE_DIR/source/src/arcana_worldsim/r6/adapters/aspect_snapshot_reader.py" \
  "$EVIDENCE_DIR/source/tests/test_r6_aspect_snapshot_reader.py" \
  "$EVIDENCE_DIR/NUMERIC_AUDIT.input.json" "$EVIDENCE_DIR/ADAPTER_AUDIT.json" \
  "$EVIDENCE_DIR/pytest.log" "$EVIDENCE_DIR/VTK_BEFORE.sha256" \
  "$EVIDENCE_DIR/VTK_AFTER.sha256" > "$EVIDENCE_DIR/SHA256SUMS"
```

The new command preserves and hashes `NUMERIC_AUDIT.json`, while the adapter emits machine-readable numeric mesh/time/schema summaries. A field-by-field comparator cannot safely be committed yet: the referenced audit JSON is not present in this Windows worktree, so its schema and numeric payload representation cannot be verified. On FAIR, inspect that schema and add/use a strict semantic comparator before claiming audit agreement; do not substitute matching file hashes or fingerprints for numeric equality. Compare numeric values and summaries (11 snapshots, endpoint times, mesh counts/type/bounds, field schema and classes, and density/density_comp values or explicit numeric-equality result). Do not treat differently serialized hashes as equal and do not claim an independent match if the audit contains only incompatible fingerprints. If the audit exposes only hashes and no comparable numeric values, report that gap and keep qualification pending. The extracted test suite should have no symlink SKIP on Linux; any failure or skip is preserved and blocks PASS. All output is confined to this new evidence directory; the original bundle is read-only and ASPECT is not invoked.

## Remaining limits

FAIR file compatibility, exact source/solver provenance, original PVD units, and equivalence with the operator-reported numeric audit remain pending until the original evidence is read on FAIR. The reader intentionally does not support multi-rank/multipiece datasets, appended VTK data, arbitrary codecs, remapping, physical interpretation, checkpoint/restart, or canonical state creation. No solver, MPI, Fair, provider, or numerical evolution ran in this task. All scientific, F2AV/Solver, mechanics, resource and WORLD_HISTORY gates remain unchanged; `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
