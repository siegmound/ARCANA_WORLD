# ARCANA WORLD — PRE-B0 C0-F1 Data / Generated / Legacy Tree Audit

**Mode:** read-only inventory and dependency archaeology. No payload was
deleted, moved, regenerated, or edited. This report is the only file created.

## A. Baseline

| Measure | Observed |
|---|---:|
| Branch | `r6/pre-b0-data-consolidation` |
| HEAD | `0c15bf8de6a6002a49a64b85f3913a98024dffba` |
| Worktree before report creation | clean |
| Tracked files present | 49,327 |
| Logical bytes across tracked files | 3,132,541,630 (2.917 GiB) |
| Tracked root files | 754 |
| Root logical bytes | 506,439,847 |
| Missing tracked paths | 0 |
| R6 regression | prior governed baseline: 252 passed; not rerun in this read-only audit |

Logical bytes are current worktree file sizes, not Git pack size or reclaimable
filesystem space. Percentages below use 49,327 files and 3,132,541,630 bytes.

## B. Size map

### Top-level (disjoint) distribution

| Top-level path | Files | Bytes | Files % | Bytes % |
|---|---:|---:|---:|---:|
| `outputs/` | 44,556 | 2,011,374,808 | 90.33% | 64.21% |
| root files | 754 | 506,439,847 | 1.53% | 16.17% |
| `SIMULATION_RESULTS/` | 877 | 373,081,060 | 1.78% | 11.91% |
| `local_runs/` | 1,814 | 113,105,603 | 3.68% | 3.61% |
| `references/` | 47 | 63,739,295 | 0.10% | 2.03% |
| `external/` | 61 | 44,449,564 | 0.12% | 1.42% |
| `local_bindings/` | 9 | 11,182,011 | 0.02% | 0.36% |
| `src/` | 246 | 4,928,953 | 0.50% | 0.16% |
| `scripts/` | 439 | 1,660,914 | 0.89% | 0.05% |
| `tests/` | 196 | 938,830 | 0.40% | 0.03% |
| `repairs/` | 53 | 616,708 | 0.11% | 0.02% |
| `docs/` | 22 | 284,018 | 0.04% | 0.01% |
| `tools/` | 35 | 189,656 | 0.07% | <0.01% |
| `configs/` | 125 | 188,159 | 0.25% | <0.01% |
| `benchmarks/` | 43 | 153,652 | 0.09% | <0.01% |
| `reference_results/` | 5 | 106,602 | 0.01% | <0.01% |
| `contracts/` | 24 | 39,080 | 0.05% | <0.01% |
| `_r52_hotfix_payload/` | 3 | 26,255 | <0.01% | <0.01% |
| `patches/` | 1 | 15,503 | <0.01% | <0.01% |
| `schemas/` | 8 | 9,231 | 0.02% | <0.01% |
| `world_history_bindings/` | 5 | 6,753 | 0.01% | <0.01% |
| `authority/` | 4 | 5,128 | <0.01% | <0.01% |

### Top 20 directory prefixes by bytes

Nested rows are inclusive and overlap their parent directory rows.

| Directory prefix | Files | Bytes |
|---|---:|---:|
| `outputs` | 44,556 | 2,011,374,808 |
| `outputs/v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_20260902_080518` | 3,257 | 945,429,341 |
| `outputs/v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_20260902_080518/rangeshifter_work` | 3,248 | 945,124,678 |
| `SIMULATION_RESULTS` | 877 | 373,081,060 |
| `outputs/v0_6D1_R5_3` | 6,417 | 170,020,140 |
| `outputs/v0_6D1_R5_3/cdmetapop_work` | 6,408 | 169,533,486 |
| `outputs/v0_6D1_R5_2` | 3,266 | 149,282,742 |
| `outputs/v0_6D1_R5_2/rangeshifter_work` | 3,248 | 148,848,067 |
| `SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY` | 78 | 138,710,777 |
| `local_runs` | 1,814 | 113,105,603 |
| `outputs/v0_6D1_R4_55` | 9,265 | 101,199,191 |
| `outputs/v0_6D1_R4_55/jobs` | 9,260 | 100,837,828 |
| `outputs/v0_6D1_R4_22` | 4,263 | 85,971,488 |
| `outputs/v0_6D1_R4_22/jobs` | 4,242 | 85,910,170 |
| `SIMULATION_RESULTS/01_CORE_WORLD_HISTORY` | 22 | 79,698,324 |
| `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY` | 221 | 78,661,670 |
| `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs` | 216 | 78,392,685 |
| `outputs/v0_6D1_R4_9` | 3,336 | 64,417,707 |
| `outputs/v0_6D1_R4_9/jobs` | 3,331 | 64,393,724 |
| `outputs/v0_6D1_R4_9/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/runtime_work_additional_dynamic` | 1,664 | 31,672,778 |

### Top 20 directory prefixes by file count

| Directory prefix | Files | Bytes |
|---|---:|---:|
| `outputs` | 44,556 | 2,011,374,808 |
| `outputs/v0_6D1_R4_55` | 9,265 | 101,199,191 |
| `outputs/v0_6D1_R4_55/jobs` | 9,260 | 100,837,828 |
| `outputs/v0_6D1_R4_3` | 7,234 | 59,339,415 |
| `outputs/v0_6D1_R4_3/jobs` | 7,215 | 59,129,291 |
| `outputs/v0_6D1_R5_3` | 6,417 | 170,020,140 |
| `outputs/v0_6D1_R5_3/cdmetapop_work` | 6,408 | 169,533,486 |
| `outputs/v0_6D1_R4_22` | 4,263 | 85,971,488 |
| `outputs/v0_6D1_R4_22/jobs` | 4,242 | 85,910,170 |
| `outputs/v0_6D1_R4_9` | 3,336 | 64,417,707 |
| `outputs/v0_6D1_R4_9/jobs` | 3,331 | 64,393,724 |
| `outputs/v0_6D1_R4_9/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP` | 3,331 | 64,393,724 |
| `outputs/v0_6D1_R5_2` | 3,266 | 149,282,742 |
| `outputs/v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_20260902_080518` | 3,257 | 945,429,341 |
| `outputs/v0_6D1_R5_2/rangeshifter_work` | 3,248 | 148,848,067 |
| `outputs/v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_20260902_080518/rangeshifter_work` | 3,248 | 945,124,678 |
| `outputs/v0_6D1_R4_7` | 2,106 | 41,879,346 |
| `outputs/v0_6D1_R4_7/jobs` | 2,100 | 41,712,535 |
| `local_runs` | 1,814 | 113,105,603 |
| `outputs/v0_6D1_R4_9/jobs/R42_J09_H0_POST_CHA1_RECOVERY_CDMETAPOP/runtime_work_additional_dynamic` | 1,664 | 31,672,778 |

### Top 30 tracked files by logical size

| Bytes | Path |
|---:|---|
| 77,832,708 | `R6_PRE_ORBDATA_SHELLSET_RUNTIME_PACKAGE_V1.dat` |
| 60,425,351 | `R6_BOUNDARY_ZONE_GEOMETRIC_FEASIBILITY_MATRIX.json` |
| 60,425,347 | `R6_BOUNDARY_ZONE_WIDTH_CASE_DIAGNOSTICS.json` |
| 42,985,913 | `R6_PRE_ORBDATA_HEAT_FLOW_FEG_PROJECTION_V1.json` |
| 38,322,972 | `SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_36/R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz` |
| 38,322,972 | `outputs/v0_6D1_R3_36/R3_36_DOMESTICATION_SELECTION_ECOLOGY_REPLAY.npz` |
| 33,554,413 | `SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_35/R3_35_PRODUCER_DOMESTICATION_GENETIC_REPLAY.npz` |
| 33,554,413 | `outputs/v0_6D1_R3_35/R3_35_PRODUCER_DOMESTICATION_GENETIC_REPLAY.npz` |
| 30,229,934 | `R6_JUNCTION_PATCH_OPERATOR_VALIDATION.json` |
| 30,229,739 | `R6_FIRST_PHYSICAL_INTERVAL_READINESS_V19.json` |
| 30,229,516 | `R6_SPHERICAL_NETWORK_ARRANGEMENT_OPERATOR_VALIDATION.json` |
| 30,229,422 | `R6_REFERENCE_ARRANGEMENT_NUMERICAL_CONVERGENCE.json` |
| 30,229,418 | `R6_GLOBAL_REFERENCE_OWNERSHIP_VALIDATION.json` |
| 30,228,969 | `R6_CANONICAL_JUNCTION_MEMBERSHIP_TOPOLOGY_DIAGNOSTICS.json` |
| 29,961,575 | `external/ShellSet-v1.1.0/INPUT/age_1p5.grd` |
| 29,366,521 | `R6_CANONICAL_JUNCTION_DOMAIN_EXPANSION_CHECKPOINT.json` |
| 27,023,921 | `references/v0_6D1_R3_9/WORLD1_H0_66Ma_PRE_CHA1_CANONICAL_CHECKPOINT_v0_6D1_R3_9.npz` |
| 20,644,596 | `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs/v0_6D1_R4_51/R4_51_23_JOB_REVALIDATION_GAP_CENSUS.json` |
| 20,644,596 | `outputs/v0_6D1_R4_51/R4_51_23_JOB_REVALIDATION_GAP_CENSUS.json` |
| 19,425,703 | `SIMULATION_RESULTS/04_VALIDATION_AUXILIARY/outputs/v0_6D1_R4_51/R4_51_JOB_SPECIFIC_EVIDENCE_CANDIDATE_INDEX.json` |
| 19,425,703 | `outputs/v0_6D1_R4_51/R4_51_JOB_SPECIFIC_EVIDENCE_CANDIDATE_INDEX.json` |
| 17,450,885 | `SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz` |
| 17,450,885 | `outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz` |
| 15,828,755 | `SIMULATION_RESULTS/01_CORE_WORLD_HISTORY/local_runs/v0_6D1_R3_8/WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.npz` |
| 15,828,755 | `local_runs/v0_6D1_R3_8/WORLD1_150Ma_CANONICAL_CONTINUATION_CHECKPOINT_v0_6D1_R3_8.npz` |
| 13,738,083 | `SIMULATION_RESULTS/00_CORE_EARLY_SIMULATION/outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz` |
| 13,738,083 | `outputs/v0_6D1_R1/WORLD1_210Ma_REBASELINE_COMMON_STATE_v0_6D1_R1.npz` |
| 13,738,083 | `references/v0_6D1_R2/WORLD1_210Ma_REBASELINE_COMMON_STATE_PARENT_R1.npz` |
| 12,509,426 | `SIMULATION_RESULTS/02_SCIENTIFIC_REPLAY/outputs/v0_6D1_R3_34/R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz` |
| 12,509,426 | `outputs/v0_6D1_R3_34/R3_34_PLANT_COEVOLUTION_DOMESTICATION_TRAJECTORIES.npz` |

The root-level R6 FEG/runtime/diagnostic payloads are large governed candidates;
size alone is not evidence that they can be regenerated or removed.

## C. File-type distribution

Counts and bytes across result/evidence trees inspected (`outputs`,
`local_runs`, `SIMULATION_RESULTS`, `references`, `reference_results`,
`benchmarks`, `repairs`, and `external`). An extension is descriptive only.

| Type | Files | Bytes |
|---|---:|---:|
| `.npz` | 354 | 624,615,186 |
| `.npy` | 151 | 10,257,728 |
| `.json` | 3,385 | 267,022,818 |
| `.csv` | 33,657 | 530,460,993 |
| `.parquet` | 0 | 0 |
| `.pkl` | 0 | 0 |
| `.dat` | 3 | 110,344 |
| `.feg` | 1 | 2,520,639 |
| `.nc` | 0 | 0 |
| `.tif` / `.tiff` | 0 | 0 |
| `.zip` | 0 | 0 |
| `.log` | 7 | 16,639 |
| `.txt` | 2,006 | 782,752,641 |
| `.md` | 60 | 130,772 |
| `.py` | 88 | 1,643,766 |
| `.asc` | 5,682 | 184,522,950 |
| `.gz` | 192 | 137,327,220 |
| `.grd` | 4 | 34,483,567 |
| other extensions/types | 1,866 | 30,762,029 |

The four `.grd` files include large vendored ShellSet grids. The 5,682 ASCII
rasters, compressed resources, CSV engine outputs, text trajectories/logs, and
NPZ checkpoints have different semantics; no extension-based deletion rule is
valid.

## D. Exact duplicate analysis

SHA256 was computed for tracked files in `outputs/`, `local_runs/`,
`SIMULATION_RESULTS/`, `references/`, `reference_results/`, `benchmarks/`, and
`repairs/`. Same-size filtering was used before hashing; equality is exact
SHA256 content equality.

| Result | Value |
|---|---:|
| Unique duplicate SHA256 groups | 4,506 |
| Files participating in those groups | 34,296 |
| Logical bytes across all participating copies | 2,225,271,812 |
| Theoretical one-copy-per-hash savings | 1,279,310,304 bytes (1.191 GiB) |

Largest cross-tree relationships by theoretical savings:

| Relationship | Hash groups | Files | One-copy savings |
|---|---:|---:|---:|
| within `outputs/` | 3,418 | 31,029 | 857,203,291 bytes |
| `SIMULATION_RESULTS` ↔ `outputs` | 816 | 1,679 | 294,266,783 bytes |
| `SIMULATION_RESULTS` ↔ `local_runs` | 34 | 68 | 66,442,004 bytes |
| `SIMULATION_RESULTS` ↔ `local_runs` ↔ `references` | 6 | 18 | 27,858,034 bytes |
| `SIMULATION_RESULTS` ↔ `outputs` ↔ `references` | 1 | 3 | 27,476,166 bytes |
| within `local_runs/` | 192 | 724 | 5,342,729 bytes |
| `outputs/` ↔ `repairs/` | 25 | 50 | 277,147 bytes |

Other small groups occur across `local_runs/outputs`, `references`,
`reference_results`, and `benchmarks`.

These are byte duplicates, not proof of interchangeable scientific records.
The large within-`outputs` groups include repeated engine outputs under distinct
run/replicate identifiers; for example, RangeShiftR `Land1_Pop.txt` outputs in
the blocked R5.2 attempt have matching bytes under different simulation IDs.
Retain those identities and manifests until adjudication shows that collapsing
them preserves replicate/provenance meaning.

### Catalogued copy verification

`SIMULATION_RESULTS/MANIFEST.json` and `.csv` each contain 863 copy records:
821 from `outputs/`, 42 from `local_runs/`. All 863 recorded original paths and
consolidated paths exist, and all 863 source/copy pairs are byte-identical in
the current worktree. Current consolidated payload bytes total **372,078,719**
(355.0 MiB). Their manifest `CopyVerified` field is true for all 863.

The recorded historical SHA256 equals the current raw bytes for all 59 NPZs and
164 JSONs. For the other 639 JSONs and the one CSV, raw worktree bytes differ
from the recorded hash; converting current LF text to CRLF reproduces the
recorded hash. This is checkout line-ending normalization, not a source/copy
mismatch: source and catalogue copies remain byte-identical to each other.
The manifest's recorded `SizeBytes` is likewise historical for normalized
text. A future portable manifest verifier should state its text hash/EOL
policy explicitly.

The catalog copies are strong `DUPLICATE_COPY` candidates: the catalogue
records original relative path, consolidated path, size, SHA256 and copy status;
all originals remain present; targeted current R6 code/test search found no
direct `SIMULATION_RESULTS/` payload-path consumer. Preserve the catalogue
README, semantic catalog and manifests if a later migration removes copies.
Update/rebuild the generated execution index and adjudicate its R6 hash pins in
the same later wave. The catalog can therefore become primarily a
manifest/navigation surface, but this audit does not authorize the deletion.

## E. `SIMULATION_RESULTS/` consolidation audit

- `README.md` describes a consolidation committed at
  `0df810112f97619f8dc2025d0e99c20ecae1a0f6`: 863 copied files, originally
  SHA-verified, with original paths retained. The files are copies, not moved
  originals. No dedicated consolidation builder is present in current
  `scripts/` or `tools/`; the originals and the manifest make copy
  reconstruction possible, but the historical exact builder invocation is not
  established here.
- `MANIFEST.json` and `MANIFEST.csv` have 863 aligned rows and record bucket,
  source root/stage, filename/extension, byte size, SHA256, original relative
  path, consolidated path and copy-verification status. They also contain
  authority/semantic fields; 859 entries remain pending repository/content
  adjudication, while 4 have verified authority/schema states.
- Current source and catalogue pairs are present and identical, as measured in
  D. Original paths are still usable for navigation. The manifest does not
  itself reconstruct payload contents if both copies are removed.
- The checkout still has 877 tracked files in this tree: 863 catalogue payload
  copies plus catalogue/readme/index/semantic documents. The README's copy-time
  summary is a historical snapshot, not a complete semantic authority ruling.
- Targeted code/test search found no direct R6 payload consumer under
  `SIMULATION_RESULTS/`. `ARCANA_EXECUTION_REFERENCE_INDEX.json` does enumerate
  the catalogue paths; it is generated reference metadata, not a payload
  consumer. General documentation points to the catalogue as a discovery
  surface.

**Answer:** yes, the tree can be reduced to a useful catalogue plus preserved
original payload paths, provided the later wave preserves the manifests and
semantic catalogue, updates consumers/index pins, and confirms originals remain
retained. It cannot become a content-recovery mechanism from manifests alone.

## F. `outputs/` and `local_runs/` family classification

| Family | Observed role / producer | Inputs, consumer and reproducibility | Classification / later action |
|---|---|---|---|
| `outputs/v0_6D1_R1`–`R3_*` and `local_runs/v0_6D1_R3_8`–`R3_20` | WorldSim baseline, continuation checkpoints, replay states and stage evidence; associated run/build scripts and stage manifests remain in the repository. | Several payloads are named canonical checkpoints/hard anchors and recur as replay inputs. Inputs and builders are mixed: some remain, while exact historical runtime environments may not. | `KEEP_AUTHORITY` for sealed checkpoints/parent states; `KEEP_UNIQUE_EVIDENCE` for stage products. No blanket cleanup. |
| R3–R5 outputs copied into `SIMULATION_RESULTS` | Curated replay, derived-history and validation copies. | Exact source/copy pairs and original paths are recorded in the manifests. | Catalogue copies: `DUPLICATE_COPY` candidate; source paths and authority labels remain protected. |
| R4 job/runtime evidence (`R4_3`, `R4_9`, `R4_22`, `R4_55` among largest) | Engine runs, qualification, repairs, cohort outputs and per-job evidence. | Many nested job outputs and manifests; some input state and wrappers remain, but engine versions and external runtime availability vary. | `KEEP_UNIQUE_EVIDENCE` / `KEEP_REFERENCE`; adjudicate by stage/job, never delete the tree wholesale. |
| `outputs/v0_6D1_R5_2` | RangeShiftR execution and sensitivity work; 3,266 files / 149,282,742 bytes. | Stage plans/manifests and engine output files exist. Reproduction depends on exact inputs, executable/runtime and seeds. | `KEEP_UNIQUE_EVIDENCE` / `REVIEW_UNKNOWN` until stage authority and repeatability are reconciled. |
| `outputs/v0_6D1_R5_2_BLOCKED_PRE_R1_FREE_INIT_20260902_080518` | 3,257 files / 945,429,341 bytes, mostly RangeShiftR. Its rejection record says `REJECTED_R52_PRE_R1_FREE_INITIALISATION_EVIDENCE_PRESERVED`; reason: `SpDistFile source.asc` was supplied but `InitType=0` selected free rather than source-distribution initialization. Audit is `BLOCKED_R52_TARGETED_RANGESHIFTER_EVIDENCE` and says scientific use is forbidden/rerun required. | Raw manifest lists 100 files. This is evidence of a rejected execution and its failure mechanism, not an accepted scientific candidate. Full reproduction would require the original runtime/inputs. | `KEEP_UNIQUE_EVIDENCE` for rejection/provenance pending archive design; do not use as authority and do not classify the 945 MB as scratch merely because the run was rejected. |
| `outputs/v0_6D1_R5_3` | CDMetaPOP work plus stage outputs; 6,417 files / 170,020,140 bytes. | Stage manifests/plans exist, but no complete regeneration proof was performed. | `KEEP_REFERENCE` / `REVIEW_UNKNOWN`; stage-level source/runtime audit required. |
| `outputs/**/PREPATCH*` / `PREPATCH_SOURCE` | Captured pre-repair source and failed/pre-patch evidence; 804 files / 20,943,343 bytes. | 23 Python files occur in such snapshots; several differ from current source/test versions and preserve the state a repair applied to. | `KEEP_UNIQUE_EVIDENCE` / `ARCHIVE_PROVENANCE`, not source duplicates suitable for blind deletion. |
| `outputs/**/pytest_tmp` | Captured pytest temporary fixture trees; 182 files / 1,829,781 bytes. | Test functions using `tmp_path` recreate synthetic inputs; no current consumer of these stored test trees was found. | `SCRATCH_TEMPORARY` candidate, high-confidence small later cleanup after confirming no evidence role. |
| `outputs/**/attempt_*` | 584 files / 2,948,996 bytes across named attempts, including R5.3 attempts. | Distinct plans and input/output artifacts; not established to be disposable scratch. | `REVIEW_UNKNOWN`; inspect per attempt and retain failure evidence as needed. |
| `local_runs/` non-checkpoint engine/smoke/qualification families | 1,814 files / 113,105,603 bytes total; includes canonical checkpoint payloads and runtime evidence. | Some exact checkpoint copies occur in `SIMULATION_RESULTS` or `references`; other files have unique run identity. | Protect canonical anchors; consider only manifest-verified extra copies in later staged adjudication. |

## G. Protected authority / unique evidence

Protect from broad cleanup:

- All current root `R6_*` artifacts: 302 files / **486,721,504 bytes**. This
  includes the 77,832,708-byte ShellSet runtime package, 42,985,913-byte heat
  flow/FEG projection, current topology/materialization artifacts and large
  validation diagnostics. Source authority, derived replayability and
  diagnostic status must be adjudicated per artifact.
- Canonical R1–R3 replay parents and named R3.8–R3.20 checkpoints in
  `outputs/`, `local_runs/`, `references/` and the corresponding
  `SIMULATION_RESULTS` copies. Duplicate bytes can serve different sealed
  roles; retain one governed canonical path and its provenance at minimum.
- Unique engine execution evidence, particularly runtime identity, input
  binding, seed/cohort/replicate records, raw manifests, PREPATCH snapshots,
  and the rejected R5.2 pre-R1 initialization evidence.
- External-engine source/input artifacts and ShellSet integration. The
  29,961,575-byte `age_1p5.grd`, `ETOPO20.grd`, `Earth5R.feg`, docs and vendored
  ShellSet source are not R6 disposable result files.
- `references/` checkpoints and parent-state comparisons, even where their
  contents duplicate an output, until hard-anchor/canonical role is explicitly
  retired.

“Generated” and “reproducible” do not make a payload disposable if the exact
runtime/input/authority needed for replay is missing or if it is the only
retained evidence of a historical engine execution.

## H. Legacy source/test copies inside result trees

- Seven nested `test_*.py` files are tracked under `outputs/`; they form three
  module basenames also present in root `tests/`:
  `test_r437_geonomics_canonical_layer_binding_exact_state_injection_dry_run.py`
  (2 nested copies + root),
  `test_r439_geonomics_runtime_time_mapping_carrier_dynamics_dynamic_layers.py`
  (4 nested copies + root), and
  `test_r442_geonomics_multi_transition_bounded_replay_production_queue_authorization.py`
  (1 nested copy + root). One R439 snapshot is byte-identical to the current
  root test; the others are distinct pre-patch/revision snapshots.
- These live below `outputs/.../PREPATCH*` / `PREPATCH_SOURCE/tests/`, which
  default recursive pytest discovery may enter. With no tracked
  `pytest.ini`, `pyproject.toml`, `setup.cfg`, or `conftest.py` governing
  exclusions, same-basename imports can trigger pytest “import file mismatch”
  collection errors. This explains the reported duplicate-module collection
  failure; no broad pytest collection was rerun here.
- There are 23 Python files in PREPATCH/PREPATCH_SOURCE snapshot areas. Their
  contents represent historical source/test states; the copies are not all
  exact matches of current canonical files and may be unique repair evidence.
- Later remedy: retain these snapshots but move them to a deliberate
  non-discovery archive or configure `norecursedirs` for result evidence. Do
  not simply delete pre-patch source/test artifacts as “duplicates.” The root
  focused R6 test surface remains the intended regression surface; the stated
  baseline is 252 passed.

## I. Generated index analysis

`ARCANA_EXECUTION_REFERENCE_INDEX.json` is 2,169,190 bytes, contains 5,271
records, and records repository head
`cea5c6deee24f8af5c1b7062dfd9a0c44cdd18a4`, not current HEAD. Its builder is
`tools/build_arcana_execution_reference_index.py`; it enumerates tracked
reference surfaces and records the generation UTC timestamp, repository HEAD,
and current tracked-worktree content. It is therefore regenerable from current
tracked files but not byte-deterministic because timestamp and HEAD change.

Thirteen `scripts/r6_*.py` scripts pin Git blob OIDs for the JSON and Markdown
index. Expected JSON/Markdown OIDs in those scripts are
`551727fd6ea73dd39a4194bf3aa34dc2a2707836` and
`8a8052c5c2ec73f26c598df5aeb3ab50105da085`; current worktree blob OIDs are
`18ea5026b9dc22b9180fb34e28b25c9f3fcb5a9a` and
`f80b568c69f2884ae9ec548e648579fb3df41241`. Thus the index is stale relative
to the HEAD recorded inside it and its current R6 hash pins do not match the
current blobs. Those scripts also carry historical parent guards; execution
was not attempted.

| Artifact | Finding | Classification |
|---|---|---|
| `ARCANA_EXECUTION_REFERENCE_INDEX.json/.md` | Builder exists; generated navigation/evidence index, not scientific authority. It currently has explicit R6 blob-pin consumers and is stale. | `KEEP` now; `REGENERATE_LATER` only with coordinated R6 pin adjudication. |
| `SIMULATION_RESULTS/MANIFEST.json/.csv` | Compact 863-row map with original/consolidated paths and hashes. | `KEEP`; potentially retain without copied payloads after source-path and consumer gate. |
| Per-stage output/raw evidence manifests | Record run/artifact identity and status; many are the only compact provenance for result trees. | `KEEP` / `REVIEW_UNKNOWN` by stage; not generated clutter by default. |

A stale generated index alone does not establish that an output payload is
scientific authority. Conversely, its explicit R6 hash gates mean the index
cannot be silently removed or rebuilt during a payload-cleanup wave.

## J. External-engine payload map

Counts/bytes below count tracked files in result/evidence trees whose paths
match the engine name (including `outputs`, `local_runs`, `SIMULATION_RESULTS`,
references and evidence trees). They are discovery counts, not complete
producer attribution; generic-named files may be omitted.

| Engine | Matched files / bytes | Location and role | Reproducibility / authority disposition |
|---|---:|---|---|
| NEMO | 2,182 / 10,190,814 | Mainly R4/R5 execution plans, stream evidence, run evidence; small fraction in consolidated catalogue. | Inputs/wrappers partly retained, exact executable/environment unverified. `KEEP_REFERENCE` / `KEEP_UNIQUE_EVIDENCE`; not a current R6 input identified. |
| Geonomics | 377 / 23,498,928 | R4 native schema, parameter/model injection, spatial-layer and binding evidence; mostly JSON in `outputs` and its catalogue copy. | Historical qualification and repair evidence; snapshots may be unique. `KEEP_UNIQUE_EVIDENCE`. |
| CDMetaPOP | 23,757 / 510,171,618 | Large R4/R5 work trees: input matrices, `indSample` CSVs, replicate outputs, plans and validation. | Full replay depends on exact external runtime/config and input artifacts. `KEEP_UNIQUE_EVIDENCE` / `REVIEW_UNKNOWN`; not blanket cleanup. |
| SLiM | 199 / 7,885,828 | R5.6 `slim_work`, `.trees`, seeds, scenarios and validation copies. | Seed/scenario-specific outputs are distinct scientific/engine evidence; source/runtime reavailability not proven. `KEEP_UNIQUE_EVIDENCE`. |
| RangeShiftR | 6,885 / 1,097,280,609 | Dominated by R5.2 run outputs, including the explicitly rejected 945 MB pre-R1 initialization attempt. | Invalid candidate ≠ disposable execution evidence. Inputs/executable replay not fully established. `KEEP_UNIQUE_EVIDENCE` / `REVIEW_UNKNOWN`. |
| Madingley | 10,391 / 28,348,511 | R4 runtime work snapshots and outputs, including repeated timestamped `input/C.csv` files. | Engine inputs and scenario/run identity need review; exact-byte duplicates may be replicate inputs. `REVIEW_UNKNOWN`. |
| BIOME4 | 0 name-matched result files | No tracked result-tree paths identified by BIOME4 name. | Absence of name-matched files is not proof that no generic/renamed legacy output exists. `REVIEW_UNKNOWN` if another index identifies payloads. |
| ShellSet | 61 / 44,449,564 | Vendored `external/ShellSet-v1.1.0`; includes large grids and source/docs, not a result-family tally. R6 runtime package is a separate root artifact. | Current R6 integration/tool source; protect. ShellSet mechanics authority is not inferred from file presence. |
| pyGPlates | 0 name-matched result files in audited data trees | Feasibility artifacts/code are elsewhere in repository; no name-matched historical payload family found in these trees. | Do not infer absence of R6 diagnostics; preserve current R6 artifacts. |

For WORLD_HISTORY, provenance and selected governed summaries may be enough for
some engine-validation families; unique hard anchors, replay inputs, raw
replicate evidence, and accepted stage payloads require content-level authority
decisions. Do not reduce engine families to summaries before that decision.

## K. Cleanup savings estimate (not an authorization)

| Confidence band | Candidate | Files | Bytes | GiB | Conditions |
|---|---|---:|---:|---:|---|
| `SAFE_HIGH_CONFIDENCE` | The 863 manifest-listed `SIMULATION_RESULTS` payload copies | 863 | 372,078,719 | 0.347 | Each corresponding original exists and is currently byte-identical; keep originals, both manifests, README/semantic catalogue; resolve stale index and R6 pins in same later wave. |
| `SAFE_HIGH_CONFIDENCE` | Nested pytest temp trees | 182 | 1,829,781 | 0.002 | Regenerable `tmp_path` fixtures, no consumer found; confirm they contain no retained non-test evidence before F2 removal. |
| `MEDIUM_CONFIDENCE` | Remaining theoretical one-copy savings from exact-hash groups after the catalog-copy candidate | up to 33,433 other participating paths / 907,231,585 | 0.845 | Hash equality can collapse distinct run/replicate IDs or evidence snapshots; family-by-family authority and consumer review required. |
| `DO_NOT_TOUCH / PROTECTED HOLD` | All remaining tracked files under a conservative hold | 48,282 | 2,758,633,130 | 2.570 | Includes unique evidence, current authority, hard anchors and the medium-confidence duplicate paths until individually adjudicated. |

The 33,433 other-participant and 907,231,585-byte values are an arithmetic residual from the global
one-copy theoretical ceiling after the catalog-copy candidate; groups overlap
trees and this is not a promised savings total. The conservative protected-hold
row excludes only the two high-confidence candidate families and is not a
semantic classification of every remaining file. Reported savings are logical
checkout bytes; Git object-store/repository disk savings were not measured.

The high-confidence figures are proposals for C0-F2, not deletion actions.
Catalog copies are convenient stable paths, so consumers, index regeneration,
and catalog navigation must be handled before removing those copies.

## L. Review unknown

- Most `SIMULATION_RESULTS` records (859/863) still have pending authority and
  semantic statuses. Copy integrity does not settle their scientific role.
- The 945 MB rejected RangeShiftR R5.2 attempt preserves a known initialization
  failure and raw engine evidence; its long-term archive/compression policy is
  open.
- R4/R5 job-level engine work trees contain repeated inputs and outputs whose
  repeat/replicate semantics are not inferred from equal bytes.
- PREPATCH snapshots preserve historical source state; exact retention policy
  and test-discovery exclusion have not been decided.
- `local_runs` includes sealed hard anchors and non-anchor run material; no
  complete semantic census of all 1,814 files was attempted.
- BIOME4 and pyGPlates have no name-matched files in the inspected result trees;
  generic filenames cannot be reliably attributed by this search.
- The execution reference index is stale, and 13 R6 scripts pin older index
  blobs. Its regeneration must be coordinated with those one-off source gates.
- Current broad docs/reference citations and stale index entries are navigation
  metadata, not by themselves runtime consumers; per-payload consumer checks
  remain needed for F2.

## M. Proposed C0-F2 waves

1. **Authority and path freeze:** enumerate hard anchors, accepted replay
   payloads, root R6 inputs, external inputs, and current direct consumers.
   Preserve manifests and SHA/EOL policies.
2. **Catalogue-only simulation results candidate:** choose the original paths
   as canonical for each of the 863 verified pairs, keep the catalog/semantic
   manifests, rewrite navigation as needed, regenerate the reference index,
   adjudicate all 13 R6 index pins, and verify tests/reference links before any
   payload copy is removed.
3. **Test-discovery boundary:** preserve PREPATCH snapshots as evidence, but
   exclude them from default pytest discovery or place them in a deliberate
   archive namespace; verify collection without reducing root regression
   coverage.
4. **Small generated residue:** separately verify and remove the 182 pytest
   temporary fixture files only after confirming every fixture is recreated by
   current tests and no run evidence is mixed in.
5. **Repeated engine outputs:** adjudicate duplicate groups by stage, seed,
   replicate, job ID and manifest. Keep all run identities unless the authority
   contract explicitly allows one-copy retention.
6. **Large historical/blocked trees:** evaluate R5.2 blocked and R5.3/R4
   external-engine work only after recording their failure/acceptance status,
   input availability and any unique evidence. This is the highest-risk wave.

No cleanup wave was executed by this audit.
