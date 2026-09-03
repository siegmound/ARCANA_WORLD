from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import hashlib
import json
import math

import numpy as np

from arcana_worldsim.state_query import r53_demography as r53

STAGE = "v0.6D1-R5.4"
OUT_REL = Path("outputs/v0_6D1_R5_4")
R53_OUT_REL = Path("outputs/v0_6D1_R5_3")
R53_AUDIT_REL = R53_OUT_REL / "R5_3_INTEGRATED_AUDIT.json"
R53_PLAN_REL = R53_OUT_REL / "R5_3_CDMETAPOP_EXECUTION_PLAN.json"
R53_SENSITIVITY_REL = R53_OUT_REL / "R5_3_DEMOGRAPHIC_PERSISTENCE_SENSITIVITY.json"
R53_STREAM_REL = R53_OUT_REL / "R5_3_CDMETAPOP_STREAM_EVIDENCE.json"
R53_OUTPUT_MANIFEST_REL = R53_OUT_REL / "R5_3_OUTPUT_MANIFEST.json"
R53_SOURCE_REL = Path("src/arcana_worldsim/state_query/r53_demography.py")
R41_NEMO_INI_REL = Path("benchmarks/r41/Nemo2_R41_B1.ini")
NEMO242_SOURCE_REL = Path("src/arcana_worldsim/scientific_engines/nemo242.py")
NEMO242_R36D_SOURCE_REL = Path("src/arcana_worldsim/scientific_engines/nemo242_r36d.py")
SOURCE_MANIFEST_REL = Path("SOURCE_AUTHORITY_MANIFEST_v0_6D1_R5_4.json")

EXPECTED_R53_PLAN_SHA256 = "3110e7ac031d12bb2e878b19df75edc5684b27aed2633224e7f889028f4a29c9"
EXPECTED_R53_SOURCE_SHA256 = "6b72a20edff18a7f73d37717b2d40af77986fa708ffc9f048025f6d11a65452b"
EXPECTED_R41_NEMO_INI_SHA256 = "d336b2ae11b547f860f83654681c734b8e8ca03a6dbe75cc61914e792996a75b"
EXPECTED_NEMO242_SOURCE_SHA256 = "6e4cea2620cfcd475328682c5458a4a54771c36bda8488da828cb9d7004202f5"
EXPECTED_NEMO242_R36D_SOURCE_SHA256 = "6015b2cb9975a68199cb441016c0f96deea6282f08c31fadaa5955231fd379ae"
EXPECTED_NEMO_VERSION = "2.4.2"
EXPECTED_NEMO_EXECUTABLE = "nemo2.4.2"
EXPECTED_R53_STREAM_COUNT = 72
EXPECTED_R53_SENSITIVITY_COUNT = 36
EXPECTED_FAMILY_COUNT = 12

# R5.4 does not fit NEMO to CDMetaPOP. It repeats the same standardized census
# challenge family on ARCANA-defined family networks and adds a matched no-flow
# control, allowing a genetically explicit second engine to isolate drift/gene
# flow effects. Values are diagnostics, never literal historical population size.
STRESS_PROFILES = dict(r53.DEMOGRAPHIC_STRESS_PROFILES)
SEEDS = (540401, 540402)
VARIANTS = ("FLOW", "MATCHED_NO_FLOW")
LOCI = 16
TRANSITIONS = 40
NEMO_GENERATIONS = TRANSITIONS + 1  # generation 1 is initialization in NEMO
TOTAL_FLOW_MASS = 0.05  # inherited standardized NEMO reference challenge, not ARCANA truth
DISTANCE_SCALE_CELLS = 2.0
MIN_RELATIVE_LOG_AFFINITY = -60.0  # fixed numerical regularization; not result-selected
INITIAL_FREQ_LOW = 0.25
INITIAL_FREQ_HIGH = 0.75
ALLELE_EFFECT = 0.05


class R54Error(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def semantic_sha256(obj: Any) -> str:
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: Path, obj: Any) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def _verify_manifest(root: Path, rel: Path) -> bool:
    p = Path(root) / rel
    if not p.is_file():
        return False
    try:
        doc = load_json(p)
        files = dict(doc.get("files") or {})
        if not files:
            return False
        base = p.parent
        for name, meta in files.items():
            fp = base / name
            if not fp.is_file():
                return False
            if fp.stat().st_size != int(meta.get("bytes", -1)):
                return False
            if sha256_file(fp) != meta.get("sha256"):
                return False
        return True
    except Exception:
        return False


def validate_parent_authority(root: Path, allow_non_scientific_dev: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    strict = not allow_non_scientific_dev
    checks: dict[str, bool] = {
        "present::r53_audit": (root / R53_AUDIT_REL).is_file(),
        "present::r53_plan": (root / R53_PLAN_REL).is_file(),
        "present::r53_sensitivity": (root / R53_SENSITIVITY_REL).is_file(),
        "present::r53_stream": (root / R53_STREAM_REL).is_file(),
        "present::r53_output_manifest": (root / R53_OUTPUT_MANIFEST_REL).is_file(),
        "present::r53_source": (root / R53_SOURCE_REL).is_file(),
        "present::nemo242_source": (root / NEMO242_SOURCE_REL).is_file(),
        "present::nemo242_r36d_source": (root / NEMO242_R36D_SOURCE_REL).is_file(),
        "present::r41_nemo_reference_ini": (root / R41_NEMO_INI_REL).is_file(),
    }
    try:
        audit = load_json(root / R53_AUDIT_REL)
        s = audit.get("summary") or {}
        checks["r53_candidate_semantics"] = (
            audit.get("status") == "PASS_R53_CORRIDOR_CONDITIONED_DEMOGRAPHIC_PERSISTENCE_AND_BOTTLENECK_EVIDENCE_CANDIDATE"
            and audit.get("scientific_candidate_eligible") is True
            and int(s.get("robust_family_count", -1)) == EXPECTED_FAMILY_COUNT
            and int(s.get("group_count", -1)) == EXPECTED_R53_SENSITIVITY_COUNT
            and int(s.get("scientific_stream_count", -1)) == EXPECTED_R53_STREAM_COUNT
            and int(s.get("sensitivity_record_count", -1)) == EXPECTED_R53_SENSITIVITY_COUNT
            and s.get("external_engine") == "CDMetaPOP"
            and s.get("external_engine_version") == r53.EXPECTED_CDMETAPOP_VERSION
            and s.get("external_engine_commit") == r53.EXPECTED_CDMETAPOP_COMMIT
            and s.get("numeric_demographic_truth_claimed") is False
            and s.get("r52_corridor_geometry_promoted_to_input_authority") is False
            and s.get("external_engine_defines_arcana_target") is False
            and s.get("majority_vote") is False
            and s.get("canonical_state_changed") is False
            and s.get("derived_refinement_promoted_to_canon") is False
            and s.get("deep_biological_coupling") is False
        )
    except Exception:
        checks["r53_candidate_semantics"] = False
    try:
        plan = load_json(root / R53_PLAN_REL)
        checks["r53_plan_semantics"] = (
            plan.get("status") == "PASS_R53_CDMETAPOP_DEMOGRAPHIC_CHALLENGE_PLAN_PREPARED"
            and int(plan.get("robust_family_count", -1)) == EXPECTED_FAMILY_COUNT
            and int(plan.get("group_count", -1)) == EXPECTED_R53_SENSITIVITY_COUNT
            and int(plan.get("planned_stream_count", -1)) == EXPECTED_R53_STREAM_COUNT
            and (plan.get("standardized_diagnostic_semantics") or {}).get("r52_range_geometry_used_as_cdmetapop_input") is False
            and (plan.get("selection_rules") or {}).get("majority_vote") is False
            and (plan.get("selection_rules") or {}).get("single_demographic_history_winner_selected") is False
            and (plan.get("selection_rules") or {}).get("external_engine_defines_arcana_target") is False
        )
        checks["r53_plan_exact_hash"] = (sha256_file(root / R53_PLAN_REL) == EXPECTED_R53_PLAN_SHA256) if strict else True
    except Exception:
        checks["r53_plan_semantics"] = checks["r53_plan_exact_hash"] = False
    try:
        sens = load_json(root / R53_SENSITIVITY_REL)
        checks["r53_sensitivity_semantics"] = (
            sens.get("status") == "R53_FIXED_DEMOGRAPHIC_STRESS_SENSITIVITY_SUMMARY"
            and sens.get("selection_semantics") == "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL"
            and len(sens.get("records") or []) == EXPECTED_R53_SENSITIVITY_COUNT
        )
    except Exception:
        checks["r53_sensitivity_semantics"] = False
    checks["r53_output_manifest_integrity"] = _verify_manifest(root, R53_OUTPUT_MANIFEST_REL)
    checks["r53_source_exact_hash"] = (sha256_file(root / R53_SOURCE_REL) == EXPECTED_R53_SOURCE_SHA256) if strict and (root / R53_SOURCE_REL).is_file() else (root / R53_SOURCE_REL).is_file()
    checks["nemo242_source_exact_hash"] = (sha256_file(root / NEMO242_SOURCE_REL) == EXPECTED_NEMO242_SOURCE_SHA256) if strict and (root / NEMO242_SOURCE_REL).is_file() else (root / NEMO242_SOURCE_REL).is_file()
    checks["nemo242_r36d_source_exact_hash"] = (sha256_file(root / NEMO242_R36D_SOURCE_REL) == EXPECTED_NEMO242_R36D_SOURCE_SHA256) if strict and (root / NEMO242_R36D_SOURCE_REL).is_file() else (root / NEMO242_R36D_SOURCE_REL).is_file()
    checks["r41_nemo_reference_ini_exact_hash"] = (sha256_file(root / R41_NEMO_INI_REL) == EXPECTED_R41_NEMO_INI_SHA256) if strict and (root / R41_NEMO_INI_REL).is_file() else (root / R41_NEMO_INI_REL).is_file()
    try:
        source_text = (root / NEMO242_R36D_SOURCE_REL).read_text(encoding="utf-8", errors="replace")
        checks["nemo242_reference_semantics_present"] = (
            "NEMO generation 1 is the initialized generation" in source_text
            and "quanti_freq_logtime" in source_text
            and "matched no-flow control" in source_text.lower()
        )
    except Exception:
        checks["nemo242_reference_semantics_present"] = False

    inherited = r53.validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev)
    checks["r53_inherited_r52_chain_pass"] = not inherited.get("failed")
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    return {
        "stage": STAGE,
        "status": "PASS_R54_IMMUTABLE_R53_PARENT_AUTHORITY" if not failed else "BLOCKED_R54_PARENT_AUTHORITY",
        "scientific_parent_mode": strict,
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "checks": checks,
        "r53_inherited_parent_authority": inherited,
    }


def _row_logsumexp(values: np.ndarray) -> np.ndarray:
    """Stable row-wise log(sum(exp(.))) for finite-support affinity rows."""
    a = np.asarray(values, dtype=float)
    maxima = np.max(a, axis=1)
    if np.any(~np.isfinite(maxima)):
        raise R54Error("R5.4 NEMO affinity contains a row without finite support")
    return maxima + np.log(np.sum(np.exp(a - maxima[:, None]), axis=1))


def _sinkhorn_symmetric_affinity(cells: list[int], nr: int, nc: int) -> np.ndarray:
    """Return the standardized symmetric, doubly-stochastic FLOW challenge.

    The previous implementation alternated row/column normalization and then
    symmetrized the result.  On highly heterogeneous geographic affinities the
    alternating matrix could still be measurably asymmetric at the iteration
    limit, so the final symmetrization moved row sums outside the strict
    stochastic tolerance.

    Here symmetry is imposed by construction.  We solve for a single diagonal
    scaling D such that B = D W D has unit row sums.  The solve is performed in
    log space (so very long-distance affinities do not underflow before
    balancing), with damped fixed-point preconditioning followed by a small
    Newton solve.  This changes only the numerical balancing method: the
    distance kernel, fixed TOTAL_FLOW_MASS, ARCANA network cells, and FLOW vs
    matched-no-flow semantics are unchanged.
    """
    n = len(cells)
    if n < 2:
        raise R54Error("R5.4 NEMO network requires at least two patches")

    log_w = np.full((n, n), -np.inf, dtype=float)
    for i, a in enumerate(cells):
        ar, ac = divmod(int(a), nc)
        for j in range(i + 1, n):
            bcell = cells[j]
            br, bc = divmod(int(bcell), nc)
            dr = float(ar - br)
            dc0 = abs(ac - bc)
            dc = float(min(dc0, nc - dc0))
            dist = math.sqrt(dr * dr + dc * dc)
            log_affinity = -dist / DISTANCE_SCALE_CELLS
            log_w[i, j] = log_w[j, i] = log_affinity

    # Every pair receives a finite log-affinity before exponentiation, so this
    # check detects only a genuine construction/support failure, not underflow.
    if np.any(~np.isfinite(np.max(log_w, axis=1))):
        raise R54Error("R5.4 NEMO affinity contains disconnected singleton patch")

    # Fixed, predeclared numerical regularization.  Extremely remote pairs can
    # differ by thousands of log units; exact symmetric matrix balancing then
    # becomes ill-conditioned even though those affinities are already far
    # below any practical contribution.  Clipping only this numerical dynamic
    # range is deterministic and result-independent; no ARCANA cell/edge is
    # selected, dropped, or tuned from NEMO output.
    offdiag = np.isfinite(log_w)
    max_log_affinity = float(np.max(log_w[offdiag]))
    min_log_affinity = max_log_affinity + MIN_RELATIVE_LOG_AFFINITY
    log_w[offdiag] = np.maximum(log_w[offdiag], min_log_affinity)

    if n == 2:
        # exp(y0 + log_w01 + y1) == 1.  The symmetric gauge gives y0 == y1.
        y = np.full(2, -0.5 * float(log_w[0, 1]), dtype=float)
    else:
        y = np.zeros(n, dtype=float)

        # Symmetry-preserving fixed-point damping provides a robust starting
        # point for the Newton solve without ever materializing tiny affinities.
        for _ in range(24):
            lse = _row_logsumexp(log_w + y[None, :])
            y = 0.5 * (y - lse)

        converged = False
        for _ in range(256):
            z = log_w + y[None, :]
            lse = _row_logsumexp(z)
            residual = y + lse  # log row sums of D W D
            row_error = float(np.max(np.abs(np.expm1(residual))))
            if row_error < 5e-13:
                converged = True
                break

            # Jacobian of residual_i wrt y_j is I + P, where P is the
            # row-normalized affinity under the current log scaling.
            p = np.exp(z - lse[:, None])
            jac = np.eye(n, dtype=float) + p
            try:
                delta = np.linalg.solve(jac, -residual)
            except np.linalg.LinAlgError:
                delta = np.linalg.lstsq(jac, -residual, rcond=None)[0]

            # Fail-safe line search: accept only a strict residual decrease.
            base = float(np.max(np.abs(residual)))
            step = 1.0
            accepted = False
            for _ in range(32):
                trial = y + step * delta
                trial_residual = trial + _row_logsumexp(log_w + trial[None, :])
                if float(np.max(np.abs(trial_residual))) < base:
                    y = trial
                    accepted = True
                    break
                step *= 0.5
            if not accepted:
                # Preserve symmetry and continue with a conservative fixed-point
                # step rather than selecting/perturbing any geographic edge.
                y = 0.5 * (y - lse)

        if not converged:
            final_residual = y + _row_logsumexp(log_w + y[None, :])
            if float(np.max(np.abs(np.expm1(final_residual)))) >= 2e-10:
                raise R54Error("symmetric log-domain Sinkhorn scaling did not converge")

    log_b = y[:, None] + log_w + y[None, :]
    b = np.zeros((n, n), dtype=float)
    finite = np.isfinite(log_b)
    b[finite] = np.exp(log_b[finite])
    np.fill_diagonal(b, 0.0)

    if not np.allclose(b.sum(axis=1), 1.0, atol=2e-10, rtol=0.0):
        raise R54Error("symmetric log-domain Sinkhorn matrix not row-stochastic")
    if not np.allclose(b.sum(axis=0), 1.0, atol=2e-10, rtol=0.0):
        raise R54Error("symmetric log-domain Sinkhorn matrix not column-stochastic")
    if not np.allclose(b, b.T, atol=1e-12, rtol=0.0):
        raise R54Error("symmetric log-domain Sinkhorn matrix lost symmetry")

    flow = (1.0 - TOTAL_FLOW_MASS) * np.eye(n, dtype=float) + TOTAL_FLOW_MASS * b
    if not np.allclose(flow, flow.T, atol=1e-12, rtol=0.0):
        raise R54Error("NEMO flow matrix not symmetric")
    if not np.allclose(flow.sum(axis=1), 1.0, atol=2e-10, rtol=0.0) or not np.allclose(flow.sum(axis=0), 1.0, atol=2e-10, rtol=0.0):
        raise R54Error("NEMO flow matrix not doubly stochastic")
    return flow


def standardized_initial_frequencies(patch_count: int) -> np.ndarray:
    if patch_count < 1:
        raise R54Error("patch_count must be positive")
    base = np.asarray([INITIAL_FREQ_LOW if i % 2 == 0 else INITIAL_FREQ_HIGH for i in range(LOCI)], dtype=float)
    return np.tile(base[None, :], (patch_count, 1))


def _nemo_vector(vals: Iterable[float | int]) -> str:
    return "{{" + ", ".join(format(float(v), ".17g") for v in vals) + "}}"


def _nemo_matrix(mat: np.ndarray) -> str:
    a = np.asarray(mat, dtype=float)
    rows = ["{" + ", ".join(format(float(v), ".17g") for v in row) + "}" for row in a]
    return "{" + "\n                         ".join(rows) + "}"


def build_nemo_ini(*, path: Path, group: dict[str, Any], variant: str, seed: int, cells: list[int], nr: int, nc: int) -> dict[str, Any]:
    if variant not in VARIANTS:
        raise R54Error(f"unsupported R5.4 NEMO variant: {variant}")
    stress_name = str(group["demographic_stress_profile"])
    stress = STRESS_PROFILES[stress_name]
    n = len(cells)
    census = int(stress["source_n0"])
    pop = np.full(n, census, dtype=int)
    init_freq = standardized_initial_frequencies(n)
    flow = _sinkhorn_symmetric_affinity(cells, nr, nc)
    matrix = flow if variant == "FLOW" else np.eye(n, dtype=float)
    effects = np.full(LOCI, ALLELE_EFFECT, dtype=float)
    filename = f"r54_{group['group_numeric_id']:03d}_{variant.lower()}_s{int(seed)}"
    text = f"""## ARCANA WorldSim v0.6D1-R5.4 -- governed NEMO 2.4.2 genetic robustness challenge
## Standardized fixed-N metapopulation genetics; not literal ARCANA demography.
logfile                 r54_nemo242.log
run_mode                overwrite
random_seed             {int(seed)}
root_dir                .
filename                {filename}
replicates              1
generations             {NEMO_GENERATIONS}

patch_number            {n}
patch_nbfem             {_nemo_vector(pop.tolist())}
patch_nbmal             0

quanti_init             1
breed_disperse          2
save_stats              3
save_files              4
mating_system           6
mating_isWrightFisher
breed_disperse_matrix   {_nemo_matrix(matrix)}

quanti_traits           1
quanti_loci             {LOCI}
quanti_allele_model     diallelic
quanti_diallele_datatype byte
quanti_allele_value     {_nemo_vector(effects.tolist())}
quanti_init_freq        {_nemo_matrix(init_freq)}
quanti_mutation_rate    0
quanti_recombination_rate 0.5

stat                    adlt.demography adlt.quanti
stat_log_time           {NEMO_GENERATIONS}
quanti_freq_output      1
quanti_freq_logtime     {NEMO_GENERATIONS}
quanti_dir              .
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    np.savetxt(path.parent / "nemo_initial_allele_frequencies.tsv", init_freq, delimiter="\t", fmt="%.17g")
    np.savetxt(path.parent / "nemo_dispersal_matrix.tsv", matrix, delimiter="\t", fmt="%.17g")
    return {
        "ini_sha256": sha256_file(path),
        "initial_frequency_sha256": sha256_file(path.parent / "nemo_initial_allele_frequencies.tsv"),
        "dispersal_matrix_sha256": sha256_file(path.parent / "nemo_dispersal_matrix.tsv"),
        "patch_count": n,
        "standardized_patch_census": census,
        "total_flow_mass": TOTAL_FLOW_MASS if variant == "FLOW" else 0.0,
        "matrix_symmetric": bool(np.allclose(matrix, matrix.T, atol=1e-12, rtol=0.0)),
        "matrix_row_stochastic": bool(np.allclose(matrix.sum(axis=1), 1.0, atol=2e-10, rtol=0.0)),
        "matrix_column_stochastic": bool(np.allclose(matrix.sum(axis=0), 1.0, atol=2e-10, rtol=0.0)),
    }


def _r53_reporting_by_key(root: Path) -> dict[tuple[str, str, str], dict[str, Any]]:
    sens = load_json(Path(root) / R53_SENSITIVITY_REL)
    out: dict[tuple[str, str, str], dict[str, Any]] = {}
    for rec in sens.get("records") or []:
        key = (str(rec["candidate_id"]), str(rec["family_id"]), str(rec["demographic_stress_profile"]))
        out[key] = {
            "cdmetapop_extinction_seed_count": int(rec.get("extinction_seed_count", 0)),
            "cdmetapop_He_retention_ratio_minmax": rec.get("He_retention_ratio_minmax"),
            "cdmetapop_alleles_retention_ratio_minmax": rec.get("alleles_retention_ratio_minmax"),
            "used_to_set_nemo_numeric_parameters": False,
            "used_as_arcana_target_authority": False,
        }
    return out


def prepare_genetic_challenges(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R54Error(f"R5.4 parent authority failed: {auth['failed']}")
    out = root / OUT_REL
    work = out / "nemo_work"
    work.mkdir(parents=True, exist_ok=True)

    fams, cores, lat, lon = r53.r52.reconstruct_robust_family_cores(root)
    ages, ids, spatial = r53._load_j14(root)
    nr, nc = len(lat), len(lon)
    r53_reporting = _r53_reporting_by_key(root)

    groups: list[dict[str, Any]] = []
    streams: list[dict[str, Any]] = []
    gnum = 0
    for fam in fams:
        fid = str(fam["family_id"])
        cells = r53._select_network_cells_for_family(fam, cores[fid], ages, ids, spatial, nr, nc)
        for stress_name, stress in STRESS_PROFILES.items():
            gnum += 1
            gid = f"R54_G{gnum:03d}_{fid}_{stress_name.split('_')[0]}"
            key = (str(fam["candidate_id"]), fid, stress_name)
            group = {
                "group_id": gid,
                "group_numeric_id": gnum,
                "candidate_id": str(fam["candidate_id"]),
                "family_id": fid,
                "origin_age_ma": float(fam["oldest_supported_age_ma"]),
                "demographic_stress_profile": stress_name,
                "standardized_patch_census": int(stress["source_n0"]),
                "stress_values_are_literal_arcana_population": False,
                "patch_count": len(cells),
                "network_cells": list(map(int, cells)),
                "network_authority": "ARCANA_R51_Q99_CORE_PLUS_J14_OCCUPANCY_SUPPORT_RECONSTRUCTED_INDEPENDENTLY_OF_R53_NUMERIC_OUTPUT",
                "r53_cdmetapop_reporting": r53_reporting.get(key),
                "r53_numeric_output_used_to_set_nemo_parameters": False,
                "neutral_marker_proxy": {"loci": LOCI, "initial_frequency_pattern": "ALTERNATING_0P25_0P75", "selection": False, "mutation": 0.0, "recombination_rate": 0.5},
                "nemo_transitions": TRANSITIONS,
                "nemo_generations_parameter": NEMO_GENERATIONS,
                "nemo_generation_is_literal_arcana_time": False,
                "variants": list(VARIANTS),
                "seeds": list(SEEDS),
                "expected_stream_count": len(VARIANTS) * len(SEEDS),
            }
            for variant in VARIANTS:
                for seed in SEEDS:
                    sdir = work / gid / variant / f"seed_{seed}"
                    ini = sdir / "Nemo2_ARCANA_R54.ini"
                    meta = build_nemo_ini(path=ini, group=group, variant=variant, seed=seed, cells=cells, nr=nr, nc=nc)
                    stream = {
                        "group_id": gid,
                        "group_numeric_id": gnum,
                        "candidate_id": group["candidate_id"],
                        "family_id": fid,
                        "demographic_stress_profile": stress_name,
                        "variant": variant,
                        "seed": int(seed),
                        "work_dir": sdir.relative_to(root).as_posix(),
                        "ini_rel": ini.relative_to(root).as_posix(),
                        **meta,
                    }
                    write_json(sdir / "STREAM_CONFIG.json", stream)
                    streams.append(stream)
            groups.append(group)

    plan = {
        "stage": STAGE,
        "status": "PASS_R54_NEMO_GENETIC_ROBUSTNESS_CHALLENGE_PLAN_PREPARED",
        "scientific_parent_mode": not allow_non_scientific_dev_parent,
        "objective": "FIXED_N_METAPOPULATION_NEUTRAL_GENETIC_ROBUSTNESS_WITH_MATCHED_NO_FLOW_CONTROL",
        "primary_governed_engine": "NEMO",
        "required_engine_version": EXPECTED_NEMO_VERSION,
        "required_engine_executable": EXPECTED_NEMO_EXECUTABLE,
        "family_count": len(fams),
        "group_count": len(groups),
        "variant_count": len(VARIANTS),
        "seeds": list(SEEDS),
        "planned_stream_count": len(streams),
        "stress_profiles": STRESS_PROFILES,
        "flow_mass": TOTAL_FLOW_MASS,
        "marker_loci": LOCI,
        "nemo_transitions": TRANSITIONS,
        "nemo_generations_parameter": NEMO_GENERATIONS,
        "groups": groups,
        "streams": streams,
        "semantics": {
            "fixed_patch_census_is_literal_arcana_demography": False,
            "nemo_generation_is_literal_arcana_time": False,
            "marker_loci_are_arcana_canonical_genome": False,
            "r53_cdmetapop_values_used_to_fit_nemo": False,
            "r53_used_only_for_side_by_side_reporting": True,
            "matched_no_flow_control_is_required": True,
            "heterogeneous_engine_metrics_forced_to_equality": False,
        },
        "selection_rules": {
            "single_family_winner_selected": False,
            "result_selected_tuning": False,
            "majority_vote": False,
            "external_engine_defines_arcana_target": False,
            "numeric_output_causes_automatic_scientific_pass_fail": False,
        },
        "canonical_state_changed": False,
        "derived_refinement_promoted_to_canon": False,
        "deep_biological_coupling": False,
    }
    write_json(out / "R5_4_NEMO_EXECUTION_PLAN.json", plan)
    binding = {
        "stage": STAGE,
        "status": "R54_PARENT_CANDIDATE_BINDING",
        "r53_plan_sha256": sha256_file(root / R53_PLAN_REL),
        "r53_audit_sha256": sha256_file(root / R53_AUDIT_REL),
        "r53_sensitivity_sha256": sha256_file(root / R53_SENSITIVITY_REL),
        "r53_output_manifest_sha256": sha256_file(root / R53_OUTPUT_MANIFEST_REL),
        "binding_semantics": "R53_CANDIDATE_BOUND_BY_HASH_AFTER_SEMANTIC_AND_MANIFEST_VALIDATION_NO_R53_MICRO_SEAL_REQUIRED",
    }
    write_json(out / "R5_4_PARENT_CANDIDATE_BINDING.json", binding)
    return plan


def parse_qfreq(path: Path) -> dict[str, Any]:
    lines = [ln.strip() for ln in Path(path).read_text(encoding="utf-8").splitlines() if ln.strip()]
    if not lines:
        raise R54Error("empty NEMO qfreq")
    header = lines[0].split()
    if header[:4] != ["pop", "trait", "locus", "allele"] or not all(x.startswith("g") for x in header[4:]):
        raise R54Error("unrecognized NEMO qfreq header")
    generations = [int(x[1:]) for x in header[4:]]
    rows = []
    for ln in lines[1:]:
        tok = ln.split()
        if len(tok) != len(header):
            raise R54Error("qfreq row width mismatch")
        pop, trait, locus = map(int, tok[:3])
        vals = [float(x) for x in tok[4:]]
        rows.append((pop, trait, locus, vals))
    if not rows:
        raise R54Error("qfreq contains no rows")
    pops = sorted({r[0] for r in rows})
    loci = sorted({r[2] for r in rows})
    if loci != list(range(1, LOCI + 1)):
        raise R54Error("qfreq loci differ from R5.4 marker contract")
    pi = {p: i for i, p in enumerate(pops)}
    freq = np.full((len(generations), len(pops), LOCI), np.nan, dtype=float)
    for pop, trait, locus, vals in rows:
        if trait != 1:
            raise R54Error("R5.4 expects one NEMO quantitative marker trait")
        freq[:, pi[pop], locus - 1] = vals
    if np.any(~np.isfinite(freq)) or np.any(freq < -1e-12) or np.any(freq > 1 + 1e-12):
        raise R54Error("invalid/incomplete NEMO qfreq")
    return {"generations": generations, "patch_ids": pops, "frequencies": np.clip(freq, 0.0, 1.0)}


def summarize_qfreq(path: Path, expected_patch_count: int) -> dict[str, Any]:
    parsed = parse_qfreq(path)
    f = np.asarray(parsed["frequencies"], float)
    final = f[-1]
    init = standardized_initial_frequencies(expected_patch_count)
    if final.shape != init.shape:
        raise R54Error(f"qfreq patch/locus shape {final.shape} != expected {init.shape}")
    h0 = float(np.mean(2.0 * init * (1.0 - init)))
    hf = float(np.mean(2.0 * final * (1.0 - final)))
    fixed = np.logical_or(final <= 1e-9, final >= 1.0 - 1e-9)
    across_patch_var = float(np.mean(np.var(final, axis=0)))
    global_shift = float(np.mean(np.abs(np.mean(final, axis=0) - np.mean(init, axis=0))))
    return {
        "generation_columns": list(map(int, parsed["generations"])),
        "represented_patch_count": int(final.shape[0]),
        "locus_count": int(final.shape[1]),
        "initial_He_mean": h0,
        "final_He_mean": hf,
        "He_retention_ratio": float(hf / h0) if h0 > 0 else None,
        "final_fixed_patch_locus_fraction": float(np.mean(fixed)),
        "final_among_patch_frequency_variance_mean": across_patch_var,
        "final_global_frequency_shift_abs_mean": global_shift,
        "automatic_scientific_pass_fail_from_values": False,
    }


def analyze_nemo_evidence(root: Path, allow_non_scientific_dev_parent: bool = False) -> dict[str, Any]:
    root = Path(root).resolve()
    auth = validate_parent_authority(root, allow_non_scientific_dev=allow_non_scientific_dev_parent)
    if auth["failed"]:
        raise R54Error(f"R5.4 parent authority failed: {auth['failed']}")
    out = root / OUT_REL
    plan = load_json(out / "R5_4_NEMO_EXECUTION_PLAN.json")
    runtime = load_json(out / "R5_4_NEMO_RUNTIME_IDENTITY.json")
    bridge = load_json(out / "R5_4_NEMO_EXECUTION_BRIDGE.json")
    r53_reporting = _r53_reporting_by_key(root)

    stream_records: list[dict[str, Any]] = []
    raw_files: dict[str, Any] = {}
    for stream in plan.get("streams") or []:
        wd = root / str(stream["work_dir"])
        rcfile = wd / "engine.returncode.txt"
        meta = wd / "STREAM_RUNTIME.json"
        qfreqs = sorted(wd.glob("*.qfreq"))
        if not rcfile.is_file() or not meta.is_file() or len(qfreqs) != 1:
            continue
        md = load_json(meta)
        if int(rcfile.read_text(encoding="utf-8").strip()) != 0:
            continue
        metrics = summarize_qfreq(qfreqs[0], int(stream["patch_count"]))
        rec = {
            "group_id": stream["group_id"],
            "candidate_id": stream["candidate_id"],
            "family_id": stream["family_id"],
            "demographic_stress_profile": stream["demographic_stress_profile"],
            "variant": stream["variant"],
            "seed": int(stream["seed"]),
            "metrics": metrics,
            "runtime_status": md.get("status"),
        }
        stream_records.append(rec)
        for fp in (rcfile, meta, qfreqs[0]):
            rel = fp.relative_to(root).as_posix()
            raw_files[rel] = {"bytes": fp.stat().st_size, "sha256": sha256_file(fp)}

    expected_streams = int(plan.get("planned_stream_count", -1))
    paired: list[dict[str, Any]] = []
    bypair: dict[tuple[str, str, str, int], dict[str, dict[str, Any]]] = {}
    for r in stream_records:
        key = (r["candidate_id"], r["family_id"], r["demographic_stress_profile"], int(r["seed"]))
        bypair.setdefault(key, {})[r["variant"]] = r
    for key in sorted(bypair):
        variants = bypair[key]
        if set(variants) != set(VARIANTS):
            continue
        f = variants["FLOW"]["metrics"]
        c = variants["MATCHED_NO_FLOW"]["metrics"]
        paired.append({
            "candidate_id": key[0],
            "family_id": key[1],
            "demographic_stress_profile": key[2],
            "seed": key[3],
            "flow_He_retention_ratio": f["He_retention_ratio"],
            "control_He_retention_ratio": c["He_retention_ratio"],
            "delta_He_retention_flow_minus_control": float(f["He_retention_ratio"] - c["He_retention_ratio"]),
            "delta_fixed_fraction_flow_minus_control": float(f["final_fixed_patch_locus_fraction"] - c["final_fixed_patch_locus_fraction"]),
            "delta_patch_frequency_variance_flow_minus_control": float(f["final_among_patch_frequency_variance_mean"] - c["final_among_patch_frequency_variance_mean"]),
            "delta_global_frequency_shift_flow_minus_control": float(f["final_global_frequency_shift_abs_mean"] - c["final_global_frequency_shift_abs_mean"]),
            "automatic_scientific_pass_fail_from_values": False,
        })

    sensitivity: list[dict[str, Any]] = []
    keys = sorted({(p["candidate_id"], p["family_id"], p["demographic_stress_profile"]) for p in paired})
    for key in keys:
        rows = sorted([p for p in paired if (p["candidate_id"], p["family_id"], p["demographic_stress_profile"]) == key], key=lambda x: x["seed"])
        def mm(field: str) -> list[float] | None:
            vals = [float(r[field]) for r in rows]
            return [min(vals), max(vals)] if vals else None
        sensitivity.append({
            "candidate_id": key[0],
            "family_id": key[1],
            "demographic_stress_profile": key[2],
            "seed_membership": [int(r["seed"]) for r in rows],
            "seed_membership_exact": tuple(int(r["seed"]) for r in rows) == SEEDS,
            "nemo_delta_He_retention_flow_minus_control_minmax": mm("delta_He_retention_flow_minus_control"),
            "nemo_delta_fixed_fraction_flow_minus_control_minmax": mm("delta_fixed_fraction_flow_minus_control"),
            "nemo_delta_patch_frequency_variance_flow_minus_control_minmax": mm("delta_patch_frequency_variance_flow_minus_control"),
            "nemo_delta_global_frequency_shift_flow_minus_control_minmax": mm("delta_global_frequency_shift_flow_minus_control"),
            "r53_cdmetapop_reporting": r53_reporting.get(key),
            "cross_engine_equality_required": False,
            "cross_engine_agreement_score_computed": False,
            "automatic_scientific_pass_fail_from_values": False,
        })

    write_json(out / "R5_4_NEMO_STREAM_EVIDENCE.json", {
        "stage": STAGE,
        "status": "R54_GOVERNED_NEMO_STREAM_EVIDENCE",
        "semantics": "FIXED_N_NEUTRAL_GENETIC_ROBUSTNESS_DIAGNOSTIC_NOT_LITERAL_ARCANA_GENOME_OR_DEMOGRAPHY",
        "records": stream_records,
    })
    write_json(out / "R5_4_NEMO_MATCHED_FLOW_CONTROL_PAIRS.json", {
        "stage": STAGE,
        "status": "R54_MATCHED_FLOW_CONTROL_PAIR_EVIDENCE",
        "records": paired,
    })
    write_json(out / "R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json", {
        "stage": STAGE,
        "status": "R54_FIXED_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY",
        "selection_semantics": "NO_WEIGHTED_SCORE_NO_MAJORITY_VOTE_NO_SINGLE_WINNER_NO_AUTOMATIC_NUMERIC_PASS_FAIL_NO_FORCED_METRIC_EQUALITY",
        "records": sensitivity,
    })
    write_json(out / "R5_4_RAW_EVIDENCE_MANIFEST.json", {
        "stage": STAGE,
        "status": "R54_RAW_NEMO_AUTHORIZED_EVIDENCE_MANIFEST",
        "file_count": len(raw_files),
        "files": raw_files,
    })

    bridge_records = bridge.get("records") or []
    checks = {
        "parent_authority_pass": not auth["failed"],
        "runtime_status_pass": runtime.get("status") == "PASS_R54_NEMO_2_4_2_PINNED_RUNTIME_IDENTITY",
        "runtime_version_exact": runtime.get("nemo_version") == EXPECTED_NEMO_VERSION,
        "runtime_conda_package_exact": runtime.get("conda_package_name") == "nemo" and runtime.get("conda_package_version") == EXPECTED_NEMO_VERSION,
        "runtime_executable_exact": runtime.get("nemo_executable_name") == EXPECTED_NEMO_EXECUTABLE,
        "plan_status_exact": plan.get("status") == "PASS_R54_NEMO_GENETIC_ROBUSTNESS_CHALLENGE_PLAN_PREPARED",
        "family_count_exact": int(plan.get("family_count", -1)) == EXPECTED_FAMILY_COUNT,
        "group_count_exact": int(plan.get("group_count", -1)) == EXPECTED_R53_SENSITIVITY_COUNT,
        "planned_stream_count_exact": expected_streams == EXPECTED_FAMILY_COUNT * len(STRESS_PROFILES) * len(VARIANTS) * len(SEEDS),
        "bridge_stream_count_exact": len(bridge_records) == expected_streams,
        "bridge_all_exit_zero": len(bridge_records) == expected_streams and all(int(r.get("exit_code", -1)) == 0 for r in bridge_records),
        "stream_count_exact": len(stream_records) == expected_streams,
        "matched_pair_count_exact": len(paired) == EXPECTED_FAMILY_COUNT * len(STRESS_PROFILES) * len(SEEDS),
        "sensitivity_count_exact": len(sensitivity) == EXPECTED_R53_SENSITIVITY_COUNT,
        "all_sensitivity_seed_membership_exact": all(r["seed_membership_exact"] for r in sensitivity),
        "r53_values_not_used_to_fit_nemo": (plan.get("semantics") or {}).get("r53_cdmetapop_values_used_to_fit_nemo") is False,
        "r53_reporting_only": (plan.get("semantics") or {}).get("r53_used_only_for_side_by_side_reporting") is True,
        "matched_no_flow_required": (plan.get("semantics") or {}).get("matched_no_flow_control_is_required") is True,
        "heterogeneous_metrics_not_forced_equal": (plan.get("semantics") or {}).get("heterogeneous_engine_metrics_forced_to_equality") is False,
        "no_majority_vote": (plan.get("selection_rules") or {}).get("majority_vote") is False,
        "no_result_selected_tuning": (plan.get("selection_rules") or {}).get("result_selected_tuning") is False,
        "no_single_winner": (plan.get("selection_rules") or {}).get("single_family_winner_selected") is False,
        "engine_does_not_define_arcana_target": (plan.get("selection_rules") or {}).get("external_engine_defines_arcana_target") is False,
        "no_automatic_numeric_scientific_pass_fail": (plan.get("selection_rules") or {}).get("numeric_output_causes_automatic_scientific_pass_fail") is False,
        "canonical_state_unchanged": plan.get("canonical_state_changed") is False,
        "derived_refinement_not_promoted": plan.get("derived_refinement_promoted_to_canon") is False,
        "deep_biological_coupling_off": plan.get("deep_biological_coupling") is False,
    }
    checks = {k: bool(v) for k, v in checks.items()}
    failed = [k for k, v in checks.items() if not v]
    audit = {
        "stage": STAGE,
        "status": "PASS_R54_CROSS_ENGINE_GENETIC_ROBUSTNESS_AND_GENE_FLOW_EVIDENCE_CANDIDATE" if not failed else "BLOCKED_R54_NEMO_GENETIC_EVIDENCE",
        "scientific_candidate_eligible": bool(not failed and not allow_non_scientific_dev_parent),
        "checks_passed": sum(checks.values()),
        "checks_total": len(checks),
        "failed": failed,
        "summary": {
            "family_count": EXPECTED_FAMILY_COUNT,
            "group_count": EXPECTED_R53_SENSITIVITY_COUNT,
            "scientific_stream_count": len(stream_records),
            "matched_pair_count": len(paired),
            "sensitivity_record_count": len(sensitivity),
            "external_engine": "NEMO",
            "external_engine_version": EXPECTED_NEMO_VERSION,
            "new_external_engine_execution_performed": True,
            "r53_cdmetapop_values_used_to_fit_nemo": False,
            "cross_engine_numeric_truth_claimed": False,
            "cross_engine_metrics_forced_to_equality": False,
            "majority_vote": False,
            "canonical_state_changed": False,
            "derived_refinement_promoted_to_canon": False,
            "deep_biological_coupling": False,
        },
        "checks": checks,
    }
    write_json(out / "R5_4_INTEGRATED_AUDIT.json", audit)
    artifacts = [
        "R5_4_PARENT_CANDIDATE_BINDING.json",
        "R5_4_NEMO_RUNTIME_IDENTITY.json",
        "R5_4_NEMO_EXECUTION_PLAN.json",
        "R5_4_NEMO_EXECUTION_BRIDGE.json",
        "R5_4_RAW_EVIDENCE_MANIFEST.json",
        "R5_4_NEMO_STREAM_EVIDENCE.json",
        "R5_4_NEMO_MATCHED_FLOW_CONTROL_PAIRS.json",
        "R5_4_CROSS_ENGINE_GENETIC_ROBUSTNESS_SENSITIVITY.json",
        "R5_4_INTEGRATED_AUDIT.json",
    ]
    files = {}
    for name in artifacts:
        p = out / name
        if p.is_file():
            files[name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
    write_json(out / "R5_4_OUTPUT_MANIFEST.json", {"stage": STAGE, "status": audit["status"], "files": files})
    return {"audit": audit, "stream_records": stream_records, "paired": paired, "sensitivity": sensitivity}
