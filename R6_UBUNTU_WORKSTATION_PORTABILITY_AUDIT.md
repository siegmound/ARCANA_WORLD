# R6 Ubuntu workstation portability audit

## Scope and result

This audit applies only to `ARCANA_WORLD_R6_UBUNTU_PORT`, branch
`r6/ubuntu-workstation`, based on `592b1651b405363373590092e133bd25569d99a5`.
The original dirty worktree was read-only reference material. No simulation,
forward evolution, provider acquisition, push, or canonical t0 mutation was
performed.

## Portability changes

- R6 runtime code now obtains repository identity through
  `src/arcana_worldsim/r6/repository_context.py`. It records actual branch/ref,
  detached status, HEAD and requested refs; branch names are not scientific
  authority. An optional base-commit ancestry gate remains available.
- R6 payload readers resolve both logical paths and historical Windows paths
  through `ARCANA_EXTERNAL_ROOT` (default: sibling `_ARCANA_EXTERNAL_SOURCES`).
  Future vector-partition materialization records a logical path rather than a
  workstation absolute path. Historical manifests are not rewritten.
- Protected-index checks now verify the recorded blob only if that file has a
  staged replacement. A normal clean checkout is not required to contain
  workstation-specific staged state.
- `.venv-r6-port/`, `.pytest-r6-temp/` and `.pytest-r6-port-temp/` are ignored.
  `environment-r6-linux.yml` defines Python 3.12.14, NumPy, pytest and optional
  candidate `pygplates=1.0.0`; pyGPlates is not made part of R6 scientific canon.

The runtime branch hard-coding was repaired in the R6 binding, validation and
initial-world materialization code. Historical JSON records that say
`"branch": "main"`, the semantic `canonical-mainline` branch role, and
Windows paths retained as historical provenance were left unchanged.

## D2C1 / D3 line-ending diagnosis

The two reported raw-hash differences are solely checkout EOL normalization.
`git check-attr` reports no applicable attribute, `core.autocrlf=input` comes
from the user Git config, and `core.eol` is unset. Git records both files with
LF; the original working copy has CRLF while this migration checkout has LF.
`git hash-object` and `git show HEAD:<path>` confirm the normalized Git blob is
the same. Their historical raw SHA256 values remain unchanged in the bootstrap
identity. The portable test canonicalizes strict UTF-8 text to LF and checks
the separately registered canonical hashes; it does not replace the historic
evidence hashes.

## Dependency closure and external payloads

All 22 declared bootstrap dependencies are present. The six specified files
recovered from the source worktree were checked against their exact expected
SHA256 values; the bootstrap identity remains
`27bdaa065146981d425088db06c7f989c1099e64e4b30d920b04c979d01331bf`.

See [R6_UBUNTU_EXTERNAL_PAYLOAD_MANIFEST.md](R6_UBUNTU_EXTERNAL_PAYLOAD_MANIFEST.md)
for byte counts, logical Ubuntu paths, roles and authority status. The vector
partition (5,681,184 bytes), R3.28 clock source (975,043 bytes), and A1
reference-only trajectory (2,928,319 bytes) were rehashed successfully. The
canonical initial-world payload's registered size (1,169,900 bytes) and hash
are preserved, but rehashing was denied by filesystem ACL; no permissions were
changed. R3.28 remains a clock source, not parent-material state authority;
A1 remains reference-only.

## Validation

Using `.venv-r6-port/Scripts/python.exe`, `PYTHONNOUSERSITE=1`, repository
`src` as `PYTHONPATH`, and repository-local pytest basetemp:

- R6 source `compileall`: PASS.
- All R6 scripts `py_compile`: PASS.
- R6-only regression: **121 passed, 0 failed, 0 errors**. The previous expected
  suite had 118 tests (108 passed, 10 failed); three portability tests were
  added, so the final suite contains 121.
- JSON parsing: PASS (104 R6/copy/audit JSON files parsed).
- Authored-path `git diff --check`: PASS. The full staged check reports only
  inherited whitespace in 13 verbatim R6 source artifacts; those files were
  preserved unchanged and are excluded from the authored-path check.
- Isolated candidate replay: PASS (temporary detached checkout at the required
  baseline with the staged candidate patch applied; 121 passed). This validates
  the staged snapshot without creating a commit.
- Commit and push were not performed.
