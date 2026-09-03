from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping
import hashlib
import json
import math

import numpy as np

STAGE = "v0.6D1-R5.0"
STAGE_NAME = "SELECTIVE_HIGH_RESOLUTION_NESTED_REPLAY_AND_ARBITRARY_AGE_STATE_QUERY"
CANDIDATE_PASS = "PASS_R50_QUERY_CONTRACT_AUTHORITY_RESOLVER_AND_20KA_17P5KA_END_TO_END_CANDIDATE"
DEV_PASS = "PASS_R50_NON_SCIENTIFIC_DEV_VALIDATION"

EXPECTED_R456_VERDICT = (
    "ARCANA_MULTI_ENGINE_23_JOB_FULLY_REVALIDATED_WITH_EXACT_INTEGRITY_AND_"
    "GOVERNED_DESCRIPTIVE_EVIDENCE_NO_NUMERIC_CORROBORATION_CLAIM"
)

EXPECTED_PARENT_HASHES: dict[str, str] = {
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz":
        "16a48a3ec8736b4b6297186222d7274a5ce376085f27bfa9108d7ba5cd0ec99a",
    "outputs/v0_6D1_R3_28/R3_28_HIGH_RESOLUTION_REPLAY_AUTHORITY.json":
        "f81755225fe301fb5519c3ca4e6e6ce715937e35a42a48a4e5c184c85879b29a",
    "outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz":
        "5fd7b11df5051245551aa2d23ce334b0a540f171e85ac8a451c603eb63f685b9",
    "outputs/v0_6D1_R3_33/R3_33_DOMESTICATION_TRAJECTORIES.npz":
        "175959669ba5daa84ab0937b4b213c1633ee674e89e67690915dbc622b2e1b84",
    "outputs/v0_6D1_R3_33/R3_33_ECOLOGICAL_PARTNER_CANDIDATE_REGISTRY.json":
        "ab3d6e50966946c95ffa60bdf48115275b3b7669640715b99836570828886711",
    "outputs/v0_6D1_R3_33/R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY.json":
        "17cc1bf7c0096b51eb333c0de7bbc4f0a827f7a4a0f821868f9db3bfa4b2936a",
    "outputs/v0_6D1_R3_34/R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz":
        "31f5954b846be3cb4a6bb14afb2ae19e7cccafd47c90719a1434e9058bc35d86",
    "outputs/v0_6D1_R3_34/R3_34_PRODUCER_TAXON_REGISTRY.json":
        "b24960a86a745a028c1096fe636885310d1ecaa3213a612696c7687ebb2e535c",
    "outputs/v0_6D1_R3_34/R3_34_PRODUCER_OPERATIONAL_TAXON_AUTHORITY.json":
        "5851a7e2d0822bab8c006bc8cd6f49f506138a3aab0533b000ecc603f9e4c39e",
}

DEFAULT_DOMAINS = (
    "population",
    "surface_paleogeography",
    "climate",
    "hydrology",
    "resources",
    "flora",
    "fauna",
)

FULL_DOMAIN_MIN_AGE_KA = 0.0
FULL_DOMAIN_MAX_AGE_KA = 20.0
TOL = 1e-9


class R50AuthorityError(RuntimeError):
    """Raised when a sealed parent or governance authority does not close."""


class R50QueryError(RuntimeError):
    """Raised when a query would violate the R5.0 contract."""


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=False) + "\n", encoding="utf-8")


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _semantic_array_hash(arrays: Mapping[str, np.ndarray]) -> str:
    h = hashlib.sha256()
    for key in sorted(arrays):
        a = np.ascontiguousarray(arrays[key])
        h.update(key.encode("utf-8") + b"\0")
        h.update(a.dtype.str.encode("ascii") + b"\0")
        h.update(_canonical_json_bytes(list(a.shape)) + b"\0")
        h.update(a.tobytes(order="C"))
    return h.hexdigest()


def _walk_key_values(obj: Any, out: dict[str, list[Any]]) -> None:
    if isinstance(obj, dict):
        for key, value in obj.items():
            out.setdefault(str(key), []).append(value)
            _walk_key_values(value, out)
    elif isinstance(obj, list):
        for value in obj:
            _walk_key_values(value, out)


def discover_r456_authority(root: Path) -> dict[str, Any]:
    """Find the sealed R4.56 closure without depending on one administrative filename.

    R4.56 evolved through many repair stages, so R5 binds to the scientific closure
    semantics rather than inventing an unknown file hash. All exact R3 scientific
    parents used by R5 are separately hash-pinned.
    """
    root = Path(root)
    outputs = root / "outputs"
    dirs = sorted({
        *outputs.glob("*R4_56*"),
        *outputs.glob("*R456*"),
        *outputs.glob("*R4.56*"),
    }) if outputs.is_dir() else []
    files: list[Path] = []
    for d in dirs:
        if d.is_dir():
            files.extend(sorted(d.rglob("*.json")))
        elif d.suffix.lower() == ".json":
            files.append(d)
    # Some local layouts keep R4.56 JSON directly under outputs or use a seal suffix.
    if outputs.is_dir():
        for p in outputs.rglob("*.json"):
            s = str(p).upper()
            if "R4_56" in s or "R456" in s or "R4.56" in s:
                files.append(p)
    files = sorted(set(files))
    if not files:
        raise R50AuthorityError("Missing R4.56 runtime artifacts; R5.0 requires the post-R4.56 SEALED baseline")

    kv: dict[str, list[Any]] = {}
    verdict_found = False
    parsed: list[tuple[Path, Any]] = []
    for p in files:
        try:
            obj = load_json(p)
        except Exception:
            continue
        parsed.append((p, obj))
        _walk_key_values(obj, kv)
        if EXPECTED_R456_VERDICT in json.dumps(obj, ensure_ascii=False):
            verdict_found = True

    def has_value(key: str, expected: Any) -> bool:
        return any(v == expected for v in kv.get(key, []))

    def has_semantic_value(expected: Any, *tokens: str) -> bool:
        for key, values in kv.items():
            lk = key.lower()
            if all(token.lower() in lk for token in tokens) and any(v == expected for v in values):
                return True
        return False

    checks = {
        "verdict_exact": verdict_found,
        "exact_frozen_jobs_23": (
            has_value("exact_frozen_jobs", 23)
            or has_value("total_jobs", 23)
            or has_semantic_value(23, "frozen", "job")
        ),
        "closed_jobs_23": (
            has_value("closed_jobs", 23)
            or has_value("fully_revalidated_closed_jobs", 23)
            or has_semantic_value(23, "closed", "job")
            or has_semantic_value(23, "revalidated", "job")
        ),
        "closure_gaps_0": (
            has_value("gaps", 0)
            or has_value("closure_gaps", 0)
            or has_semantic_value(0, "gap")
        ),
        "full_revalidation_closed": (
            has_value("multi_engine_full_revalidation_closed", True)
            or has_semantic_value(True, "revalidation", "closed")
        ),
        "numeric_corroboration_not_claimed": (
            has_value("numeric_cross_engine_corroboration_claimed", False)
            or has_semantic_value(False, "numeric", "corroboration")
        ),
        "canonical_state_unchanged": (
            has_value("canonical_state_changed", False)
            or has_semantic_value(False, "canonical", "changed")
        ),
        "deep_biological_coupling_off": (
            has_value("deep_biological_coupling", False)
            or has_semantic_value(False, "deep", "biological", "coupling")
        ),
    }
    failed = [name for name, ok in checks.items() if not ok]
    if failed:
        raise R50AuthorityError(f"R4.56 authority scan failed closed: {failed}")
    return {
        "status": "R456_RUNTIME_AUTHORITY_VERIFIED",
        "expected_verdict": EXPECTED_R456_VERDICT,
        "checks": checks,
        "evidence_files": [
            {"path": str(p.relative_to(root)), "sha256": sha256_file(p), "bytes": p.stat().st_size}
            for p, _ in parsed
        ],
    }


@dataclass(frozen=True)
class R50QueryContract:
    query_id: str
    target_age_ka: float
    requested_domains: tuple[str, ...] = DEFAULT_DOMAINS
    resolution_profile: str = "NATIVE_90X180_WITH_DEME_DETAIL"
    region: dict[str, int] | None = None
    allow_temporal_interpolation: bool = True
    allow_temporal_extrapolation: bool = False
    canonical_write: bool = False

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "R50QueryContract":
        domains = tuple(value.get("requested_domains", DEFAULT_DOMAINS))
        return cls(
            query_id=str(value["query_id"]),
            target_age_ka=float(value["target_age_ka"]),
            requested_domains=domains,
            resolution_profile=str(value.get("resolution_profile", "NATIVE_90X180_WITH_DEME_DETAIL")),
            region=value.get("region"),
            allow_temporal_interpolation=bool(value.get("allow_temporal_interpolation", True)),
            allow_temporal_extrapolation=bool(value.get("allow_temporal_extrapolation", False)),
            canonical_write=bool(value.get("canonical_write", False)),
        )

    def validate(self) -> None:
        if not self.query_id or any(ch in self.query_id for ch in "\\/:"):
            raise R50QueryError("query_id must be non-empty and filesystem-safe")
        if not math.isfinite(self.target_age_ka) or self.target_age_ka < 0:
            raise R50QueryError("target_age_ka must be finite and >= 0")
        unknown = set(self.requested_domains) - set(DEFAULT_DOMAINS)
        if unknown:
            raise R50QueryError(f"Unknown requested domains: {sorted(unknown)}")
        if self.canonical_write:
            raise R50QueryError("R5.0 derived queries may not write canonical state")
        if self.allow_temporal_extrapolation:
            raise R50QueryError("R5.0 forbids temporal extrapolation")
        if self.resolution_profile != "NATIVE_90X180_WITH_DEME_DETAIL":
            raise R50QueryError("R5.0 implements only NATIVE_90X180_WITH_DEME_DETAIL; no synthetic spatial upsampling")
        if self.region is not None:
            required = {"grid_row_min", "grid_row_max", "grid_col_min", "grid_col_max"}
            if set(self.region) != required:
                raise R50QueryError(f"region must contain exactly {sorted(required)}")
            r0, r1 = int(self.region["grid_row_min"]), int(self.region["grid_row_max"])
            c0, c1 = int(self.region["grid_col_min"]), int(self.region["grid_col_max"])
            if not (0 <= r0 <= r1 <= 89 and 0 <= c0 <= 179 and 0 <= c1 <= 179):
                raise R50QueryError("region grid bounds outside World1 90x180 support")

    def to_json(self) -> dict[str, Any]:
        out = asdict(self)
        out["requested_domains"] = list(self.requested_domains)
        out.update({
            "stage": STAGE,
            "authority_semantics": "DERIVED_QUERY_ONLY_NO_CANONICAL_WRITE",
        })
        return out


def _match_or_bracket(axis: np.ndarray, target: float) -> dict[str, Any]:
    axis = np.asarray(axis, dtype=float)
    exact = np.where(np.isclose(axis, target, atol=TOL, rtol=0))[0]
    if exact.size:
        i = int(exact[0])
        return {"mode": "EXACT", "indices": [i], "ages_ka": [float(axis[i])], "weight_younger": 0.0}
    older = [(float(a), i) for i, a in enumerate(axis) if a > target]
    younger = [(float(a), i) for i, a in enumerate(axis) if a < target]
    if not older or not younger:
        raise R50QueryError(f"Target age {target} ka is outside available authority range [{axis.min()}, {axis.max()}]")
    old_age, old_i = min(older, key=lambda x: x[0] - target)
    young_age, young_i = min(younger, key=lambda x: target - x[0])
    den = old_age - young_age
    if den <= 0:
        raise R50QueryError("Invalid authority bracket")
    w = (old_age - target) / den
    return {
        "mode": "BRACKETED_LINEAR",
        "indices": [old_i, young_i],
        "ages_ka": [old_age, young_age],
        "weight_younger": float(w),
    }


def _interp_pair(old: np.ndarray, young: np.ndarray, w_young: float) -> np.ndarray:
    return (1.0 - w_young) * np.asarray(old, float) + w_young * np.asarray(young, float)


def _interp_longitude(old: np.ndarray, young: np.ndarray, w_young: float) -> np.ndarray:
    old = np.asarray(old, float)
    young = np.asarray(young, float)
    delta = ((young - old + 90.0) % 180.0) - 90.0
    return (old + w_young * delta) % 180.0


def _region_indices(region: dict[str, int] | None) -> tuple[np.ndarray, np.ndarray]:
    if region is None:
        return np.arange(90, dtype=np.int16), np.arange(180, dtype=np.int16)
    rows = np.arange(int(region["grid_row_min"]), int(region["grid_row_max"]) + 1, dtype=np.int16)
    c0, c1 = int(region["grid_col_min"]), int(region["grid_col_max"])
    if c0 <= c1:
        cols = np.arange(c0, c1 + 1, dtype=np.int16)
    else:
        cols = np.concatenate((np.arange(c0, 180, dtype=np.int16), np.arange(0, c1 + 1, dtype=np.int16)))
    return rows, cols


def _slice_grid(field: np.ndarray, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    # Grid axes are always the last grid pair before optional variable axis.
    if field.ndim == 3:  # R,C,V
        return field[np.ix_(rows, cols, np.arange(field.shape[2]))]
    if field.ndim == 4:  # P,R,C,V
        return field[:, rows][:, :, cols, :]
    raise R50QueryError(f"Unsupported grid field rank {field.ndim}")


class R50AuthorityResolver:
    def __init__(self, root: Path, *, allow_unverified_r456: bool = False):
        self.root = Path(root).resolve()
        self.allow_unverified_r456 = bool(allow_unverified_r456)
        self.parent_paths = {rel: self.root / rel for rel in EXPECTED_PARENT_HASHES}
        self.parent_hashes = self._validate_parent_hashes()
        try:
            self.r456 = discover_r456_authority(self.root)
            self.r456_verified = True
        except R50AuthorityError:
            if not self.allow_unverified_r456:
                raise
            self.r456 = {
                "status": "UNVERIFIED_R456_DEV_ALLOWANCE",
                "expected_verdict": EXPECTED_R456_VERDICT,
                "scientific_evidence_eligible": False,
            }
            self.r456_verified = False
        self._load_and_validate()

    def _validate_parent_hashes(self) -> dict[str, str]:
        got: dict[str, str] = {}
        for rel, expected in EXPECTED_PARENT_HASHES.items():
            p = self.root / rel
            if not p.is_file():
                raise R50AuthorityError(f"Missing exact parent artifact: {rel}")
            value = sha256_file(p)
            got[rel] = value
            if value != expected:
                raise R50AuthorityError(f"Parent hash mismatch for {rel}: {value} != {expected}")
        return got

    def _load_and_validate(self) -> None:
        r28 = self.root / "outputs/v0_6D1_R3_28"
        r33 = self.root / "outputs/v0_6D1_R3_33"
        r34 = self.root / "outputs/v0_6D1_R3_34"
        self.z28 = np.load(r28 / "R3_28_HIGH_RESOLUTION_POPULATION_REPLAY.npz", allow_pickle=False)
        self.z33env = np.load(r33 / "R3_33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE.npz", allow_pickle=False)
        self.z33fauna = np.load(r33 / "R3_33_DOMESTICATION_TRAJECTORIES.npz", allow_pickle=False)
        self.z34flora = np.load(r34 / "R3_34_PRODUCER_RESOURCE_LANDSCAPE.npz", allow_pickle=False)
        self.fauna_registry = load_json(r33 / "R3_33_ECOLOGICAL_PARTNER_CANDIDATE_REGISTRY.json")
        self.env_authority = load_json(r33 / "R3_33_HOLOCENE_ENVIRONMENT_DOMESTICATION_AUTHORITY.json")
        self.flora_registry = load_json(r34 / "R3_34_PRODUCER_TAXON_REGISTRY.json")
        self.flora_authority = load_json(r34 / "R3_34_PRODUCER_OPERATIONAL_TAXON_AUTHORITY.json")

        if self.z28["species_summary"].shape != (32, 2, 280, 8):
            raise R50AuthorityError("R3.28 species summary geometry mismatch")
        if self.z28["snapshot_deme_state"].shape != (32, 2, 15, 6, 7):
            raise R50AuthorityError("R3.28 snapshot detail geometry mismatch")
        if self.z33env["environment_fields"].shape != (9, 90, 180, 7):
            raise R50AuthorityError("R3.33 environment geometry mismatch")
        if self.z34flora["producer_landscape"].shape != (36, 9, 90, 180, 4):
            raise R50AuthorityError("R3.34 producer landscape geometry mismatch")
        if self.z33fauna["trajectory_state"].shape != (32, 2, 24, 9, 9):
            raise R50AuthorityError("R3.33 fauna partner trajectory geometry mismatch")
        anchors = np.asarray([20., 15., 14., 13., 12., 11., 10., 5., 0.])
        if not np.array_equal(np.asarray(self.z33env["anchor_age_ka"], float), anchors):
            raise R50AuthorityError("R3.33 environment anchor axis mismatch")
        if not np.array_equal(np.asarray(self.z34flora["anchor_age_ka"], float), anchors):
            raise R50AuthorityError("R3.34 flora anchor axis mismatch")
        if not np.array_equal(np.asarray(self.z33fauna["anchor_age_ka"], float), anchors):
            raise R50AuthorityError("R3.33 fauna anchor axis mismatch")
        if self.env_authority.get("deep_biological_coupling") is not False:
            raise R50AuthorityError("R3.33 deep biological coupling premise mismatch")
        if self.flora_authority.get("deep_biological_coupling") is not False:
            raise R50AuthorityError("R3.34 deep biological coupling premise mismatch")
        if self.env_authority.get("plant_species_registry_available") is not False:
            raise R50AuthorityError("R3.33 plant registry premise mismatch")

    def close(self) -> None:
        for z in (self.z28, self.z33env, self.z33fauna, self.z34flora):
            try:
                z.close()
            except Exception:
                pass

    def __enter__(self) -> "R50AuthorityResolver":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _population_summary(self, age: float) -> tuple[np.ndarray, dict[str, Any]]:
        axis = np.asarray(self.z28["age_ka"], float)
        b = _match_or_bracket(axis, age)
        if b["mode"] == "EXACT":
            state = np.asarray(self.z28["species_summary"][:, :, b["indices"][0], :], np.float32)
        else:
            if not b:
                raise R50QueryError("Population summary authority unavailable")
            i0, i1 = b["indices"]
            state = _interp_pair(self.z28["species_summary"][:, :, i0, :], self.z28["species_summary"][:, :, i1, :], b["weight_younger"]).astype(np.float32)
        prov = {
            "authority": "R3.28_HIGH_RESOLUTION_POPULATION_REPLAY.species_summary",
            "mode": b["mode"],
            "source_ages_ka": b["ages_ka"],
            "weight_younger": b["weight_younger"],
            "semantic": "POPULATION_SUMMARY_EXACT_WHEN_TARGET_ON_R3_28_HIGH_RESOLUTION_AXIS_OTHERWISE_BOUNDED_LINEAR_DERIVATION",
        }
        return state, prov

    def _detail_source(self, age: float) -> tuple[np.ndarray, np.ndarray, str] | None:
        snap = np.asarray(self.z28["snapshot_age_ka"], float)
        m = np.where(np.isclose(snap, age, atol=TOL, rtol=0))[0]
        if m.size:
            i = int(m[0])
            return (
                np.asarray(self.z28["snapshot_deme_state"][:, :, i, :, :], np.float32),
                np.asarray(self.z28["snapshot_active"][:, :, i, :], np.uint8),
                "R3.28.snapshot_deme_state",
            )
        cha = np.asarray(self.z28["cha2_age_ka"], float)
        m = np.where(np.isclose(cha, age, atol=TOL, rtol=0))[0]
        if m.size:
            i = int(m[0])
            return (
                np.asarray(self.z28["cha2_deme_state"][:, :, i, :, :], np.float32),
                np.asarray(self.z28["cha2_active"][:, :, i, :], np.uint8),
                "R3.28.cha2_deme_state",
            )
        return None

    def _population_detail(self, age: float, summary: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, Any]]:
        exact = self._detail_source(age)
        if exact is not None:
            state, active, source = exact
            return state, active, {
                "authority": source,
                "mode": "EXACT",
                "source_ages_ka": [age],
                "weight_younger": 0.0,
                "constraints": ["parent_state_direct"],
            }

        detail_axis = np.unique(np.concatenate((
            np.asarray(self.z28["snapshot_age_ka"], float),
            np.asarray(self.z28["cha2_age_ka"], float),
        )))
        b = _match_or_bracket(detail_axis, age)
        if b["mode"] == "EXACT":
            raise AssertionError("Exact detail should have been resolved")
        old_age, young_age = b["ages_ka"]
        old = self._detail_source(old_age)
        young = self._detail_source(young_age)
        if old is None or young is None:
            raise R50QueryError("Detailed population bracket could not be materialized")
        s0, _, _ = old
        s1, _, _ = young
        w = b["weight_younger"]
        state = _interp_pair(s0, s1, w).astype(np.float64)
        # Longitude is cyclic on the 180-column World1 support.
        state[..., 2] = _interp_longitude(s0[..., 2], s1[..., 2], w)
        state[..., 0] = np.maximum(state[..., 0], 0.0)
        state[..., 1] = np.clip(state[..., 1], 0.0, 89.0)
        state[..., 2] %= 180.0
        state[..., 3:] = np.clip(state[..., 3:], 0.0, 1.0)

        summary_names = list(map(str, self.z28["species_summary_variable_names"]))
        pop_i = summary_names.index("population_proxy")
        dem_i = summary_names.index("active_demes")
        active = np.zeros(state.shape[:-1], dtype=np.uint8)
        # Preserve the exact/authorized target population total and target active-deme count.
        for m in range(state.shape[0]):
            for l in range(state.shape[1]):
                target_total = max(float(summary[m, l, pop_i]), 0.0)
                p = np.maximum(state[m, l, :, 0], 0.0)
                total = float(p.sum())
                if total > 0:
                    state[m, l, :, 0] = p * (target_total / total)
                elif target_total > 0:
                    state[m, l, 0, 0] = target_total
                n_active = int(np.clip(round(float(summary[m, l, dem_i])), 0, state.shape[2]))
                if n_active:
                    order = np.argsort(-state[m, l, :, 0], kind="stable")
                    active[m, l, order[:n_active]] = 1
        return state.astype(np.float32), active, {
            "authority": "R3.28.snapshot_deme_state",
            "mode": "BOUNDED_SPATIAL_RECONSTRUCTION",
            "source_ages_ka": [old_age, young_age],
            "weight_younger": w,
            "constraints": [
                "cyclic_longitude_shortest_path",
                "target_population_total_constrained_to_population_summary",
                "target_active_deme_count_constrained_to_population_summary",
                "no_new_deme_slots",
                "no_stochastic_motion",
            ],
            "semantic": "DERIVED_SPATIAL_DETAIL_BETWEEN_SEALED_SNAPSHOTS_NOT_A_CANONICAL_REWRITE",
        }

    def _environment(self, age: float) -> tuple[np.ndarray, dict[str, Any]]:
        axis = np.asarray(self.z33env["anchor_age_ka"], float)
        b = _match_or_bracket(axis, age)
        if b["mode"] == "EXACT":
            state = np.asarray(self.z33env["environment_fields"][b["indices"][0]], np.float64)
        else:
            i0, i1 = b["indices"]
            state = _interp_pair(self.z33env["environment_fields"][i0], self.z33env["environment_fields"][i1], b["weight_younger"])
        return state, {
            "authority": "R3.33_HOLOCENE_ENVIRONMENTAL_RESOURCE_LANDSCAPE",
            "mode": b["mode"],
            "source_ages_ka": b["ages_ka"],
            "weight_younger": b["weight_younger"],
            "semantic": self.env_authority["environmental_semantics"],
        }

    def _flora(self, age: float) -> tuple[np.ndarray, dict[str, Any]]:
        axis = np.asarray(self.z34flora["anchor_age_ka"], float)
        b = _match_or_bracket(axis, age)
        if b["mode"] == "EXACT":
            state = np.asarray(self.z34flora["producer_landscape"][:, b["indices"][0], :, :, :], np.float32)
        else:
            i0, i1 = b["indices"]
            state = _interp_pair(
                self.z34flora["producer_landscape"][:, i0, :, :, :],
                self.z34flora["producer_landscape"][:, i1, :, :, :],
                b["weight_younger"],
            ).astype(np.float32)
        return state, {
            "authority": "R3.34_PRODUCER_RESOURCE_LANDSCAPE",
            "mode": b["mode"],
            "source_ages_ka": b["ages_ka"],
            "weight_younger": b["weight_younger"],
            "semantic": self.flora_authority["producer_authority_semantics"],
        }

    def _fauna(self, age: float) -> tuple[np.ndarray, dict[str, Any]]:
        axis = np.asarray(self.z33fauna["anchor_age_ka"], float)
        b = _match_or_bracket(axis, age)
        if b["mode"] == "EXACT":
            state = np.asarray(self.z33fauna["trajectory_state"][:, :, :, b["indices"][0], :], np.float32)
        else:
            i0, i1 = b["indices"]
            state = _interp_pair(
                self.z33fauna["trajectory_state"][:, :, :, i0, :],
                self.z33fauna["trajectory_state"][:, :, :, i1, :],
                b["weight_younger"],
            ).astype(np.float32)
        return state, {
            "authority": "R3.33_DOMESTICATION_TRAJECTORIES_ANIMAL_ECOLOGICAL_PARTNERS",
            "mode": b["mode"],
            "source_ages_ka": b["ages_ka"],
            "weight_younger": b["weight_younger"],
            "semantic": "PARTIAL_FAUNA_AUTHORITY_24_H0_DERIVED_ECOLOGICAL_PARTNER_CANDIDATES_AND_INTERACTION_TRAJECTORIES_ONLY_NO_GLOBAL_FAUNA_RASTER_CLAIM",
        }

    def resolve(self, query: R50QueryContract) -> dict[str, Any]:
        query.validate()
        if any(d != "population" for d in query.requested_domains):
            if not (FULL_DOMAIN_MIN_AGE_KA - TOL <= query.target_age_ka <= FULL_DOMAIN_MAX_AGE_KA + TOL):
                raise R50QueryError(
                    f"R5.0 full-domain authority is currently bounded to 0-20 ka; requested {query.target_age_ka} ka"
                )
        if not query.allow_temporal_interpolation:
            # Every requested product must be exact at the target, including population detail.
            exact_requirements: list[tuple[str, np.ndarray]] = []
            if "population" in query.requested_domains:
                exact_requirements.append(("population_summary", np.asarray(self.z28["age_ka"], float)))
                detail_axis = np.unique(np.concatenate((
                    np.asarray(self.z28["snapshot_age_ka"], float),
                    np.asarray(self.z28["cha2_age_ka"], float),
                )))
                exact_requirements.append(("population_detail", detail_axis))
            if any(d in query.requested_domains for d in ("surface_paleogeography", "climate", "hydrology", "resources")):
                exact_requirements.append(("environment", np.asarray(self.z33env["anchor_age_ka"], float)))
            if "flora" in query.requested_domains:
                exact_requirements.append(("flora", np.asarray(self.z34flora["anchor_age_ka"], float)))
            if "fauna" in query.requested_domains:
                exact_requirements.append(("fauna", np.asarray(self.z33fauna["anchor_age_ka"], float)))
            missing_exact = [
                name for name, ax in exact_requirements
                if not np.any(np.isclose(ax, query.target_age_ka, atol=TOL, rtol=0))
            ]
            if missing_exact:
                raise R50QueryError(
                    "Query disables interpolation but exact target state is unavailable for: "
                    + ", ".join(missing_exact)
                )

        rows, cols = _region_indices(query.region)
        arrays: dict[str, np.ndarray] = {
            "target_age_ka": np.asarray([query.target_age_ka], dtype=np.float64),
            "grid_row_indices": rows,
            "grid_col_indices": cols,
        }
        provenance: dict[str, Any] = {}

        if "population" in query.requested_domains:
            summary, p_summary = self._population_summary(query.target_age_ka)
            detail, active, p_detail = self._population_detail(query.target_age_ka, summary)
            axis = np.asarray(self.z28["age_ka"], float)
            b = _match_or_bracket(axis, query.target_age_ka)
            if b["mode"] == "EXACT":
                idx = b["indices"][0]
                contact = np.asarray(self.z28["contact_index"][:, idx], np.float32)
                admix = np.asarray(self.z28["admixture_opportunity_cumulative"][:, idx], np.float32)
            else:
                i0, i1 = b["indices"]
                contact = _interp_pair(self.z28["contact_index"][:, i0], self.z28["contact_index"][:, i1], b["weight_younger"]).astype(np.float32)
                admix = _interp_pair(self.z28["admixture_opportunity_cumulative"][:, i0], self.z28["admixture_opportunity_cumulative"][:, i1], b["weight_younger"]).astype(np.float32)
            arrays.update({
                "candidate_ids": np.asarray(self.z28["candidate_ids"]),
                "parent_member_indices": np.asarray(self.z28["parent_member_indices"]),
                "population_summary_variable_names": np.asarray(self.z28["species_summary_variable_names"]),
                "population_summary": summary,
                "deme_state_variable_names": np.asarray(self.z28["state_variable_names"]),
                "deme_state": detail,
                "deme_active": active,
                "contact_index": contact,
                "admixture_opportunity_cumulative": admix,
            })
            provenance["population_summary"] = p_summary
            provenance["population_detail"] = p_detail
            provenance["contact_admixture"] = {
                "authority": "R3.28_HIGH_RESOLUTION_POPULATION_REPLAY.contact_index+admixture_opportunity_cumulative",
                "mode": b["mode"],
                "source_ages_ka": b["ages_ka"],
                "weight_younger": b["weight_younger"],
            }

        if any(d in query.requested_domains for d in ("surface_paleogeography", "climate", "hydrology", "resources")):
            env, p_env = self._environment(query.target_age_ka)
            env = _slice_grid(env, rows, cols)
            arrays.update({
                "environment_variable_names": np.asarray(self.z33env["environment_variable_names"]),
                "environment_fields": env,
            })
            provenance["environment"] = p_env

        if "flora" in query.requested_domains:
            flora, p_flora = self._flora(query.target_age_ka)
            flora = _slice_grid(flora, rows, cols)
            arrays.update({
                "producer_taxon_ids": np.asarray(self.z34flora["producer_taxon_ids"]),
                "producer_variable_names": np.asarray(self.z34flora["landscape_variable_names"]),
                "producer_landscape": flora,
            })
            provenance["flora"] = p_flora

        if "fauna" in query.requested_domains:
            fauna, p_fauna = self._fauna(query.target_age_ka)
            trait_names = list(self.fauna_registry["partner_trait_names"])
            by_id = {str(x["species_id"]): x for x in self.fauna_registry["candidates"]}
            ids = list(map(str, self.z33fauna["partner_species_ids"]))
            trait_matrix = np.asarray([[float(by_id[s][name]) for name in trait_names] for s in ids], dtype=np.float32)
            arrays.update({
                "fauna_partner_species_ids": np.asarray(ids),
                "fauna_partner_trait_names": np.asarray(trait_names),
                "fauna_partner_traits": trait_matrix,
                "fauna_trajectory_variable_names": np.asarray(self.z33fauna["trajectory_variable_names"]),
                "fauna_partner_trajectory_state": fauna,
            })
            provenance["fauna"] = p_fauna

        domain_coverage = {
            "population": "FULL_R3_28_TWO_CANDIDATE_COHORT_SUMMARY_PLUS_MAX_6_DEME_DETAIL" if "population" in query.requested_domains else "NOT_REQUESTED",
            "surface_paleogeography": "PARTIAL_LAND_FRACTION_PLUS_SEA_LEVEL_SURFACE_SUPPORT_NOT_DEEP_GEOLOGY" if "surface_paleogeography" in query.requested_domains else "NOT_REQUESTED",
            "climate": "R3_33_TEMPERATURE_ANOMALY_PLUS_PRECIPITATION_FACTOR" if "climate" in query.requested_domains else "NOT_REQUESTED",
            "hydrology": "PARTIAL_R3_33_HYDROCLIMATE_RESOURCE_PLUS_COASTAL_EDGE_NO_RIVER_NETWORK" if "hydrology" in query.requested_domains else "NOT_REQUESTED",
            "resources": "R3_33_NPP_PRECIPITATION_HYDROCLIMATE_RESOURCE_FIELDS" if "resources" in query.requested_domains else "NOT_REQUESTED",
            "flora": "R3_34_36_ANONYMOUS_FUNCTIONAL_OPERATIONAL_PRODUCER_TAXA" if "flora" in query.requested_domains else "NOT_REQUESTED",
            "fauna": "PARTIAL_R3_33_24_ECOLOGICAL_PARTNER_CANDIDATES_AND_INTERACTION_TRAJECTORIES_NO_GLOBAL_FAUNA_RASTER" if "fauna" in query.requested_domains else "NOT_REQUESTED",
        }
        semantic_hash = _semantic_array_hash(arrays)
        return {
            "query": query,
            "arrays": arrays,
            "provenance": provenance,
            "domain_coverage": domain_coverage,
            "semantic_state_sha256": semantic_hash,
            "governance": {
                "canonical_state_changed": False,
                "canonical_write": False,
                "full_history_rerun_performed": False,
                "external_engine_execution_performed": False,
                "target_numeric_execution_performed": False,
                "readjudication_of_arcana_canonical_target_performed": False,
                "temporal_extrapolation_performed": False,
                "randomness_used": False,
                "deep_biological_coupling": False,
                "renderer_or_visualization_execution_performed": False,
            },
        }


def _age_slug(age_ka: float) -> str:
    if abs(age_ka - round(age_ka)) < TOL:
        return f"{int(round(age_ka))}KA"
    s = (f"{age_ka:.6f}").rstrip("0").rstrip(".").replace(".", "P")
    return f"{s}KA"


def _uncertainty_record(result: dict[str, Any]) -> dict[str, Any]:
    records = []
    for name, p in result["provenance"].items():
        mode = p["mode"]
        if mode == "EXACT":
            cls = "PARENT_EXACT_STATE"
        elif mode == "BRACKETED_LINEAR":
            cls = "DERIVED_BETWEEN_SEALED_ANCHORS"
        elif mode == "BOUNDED_SPATIAL_RECONSTRUCTION":
            cls = "DERIVED_SPATIAL_DETAIL_CONSTRAINED_BY_AUTHORIZED_SUMMARY"
        else:
            cls = "DERIVED_UNCLASSIFIED"
        records.append({
            "product": name,
            "uncertainty_class": cls,
            "quantified_uncertainty_available": False,
            "source_ages_ka": p.get("source_ages_ka", []),
            "method": mode,
            "note": "No numeric confidence interval is invented when the sealed parent does not provide one.",
        })
    return {
        "stage": STAGE,
        "query_id": result["query"].query_id,
        "target_age_ka": result["query"].target_age_ka,
        "records": records,
        "global_rules": {
            "no_hidden_interpolation": True,
            "no_extrapolation": True,
            "no_invented_numeric_uncertainty": True,
            "derived_state_is_not_canonical": True,
        },
    }


def _recipe_record(result: dict[str, Any]) -> dict[str, Any]:
    recipe = {
        "stage": STAGE,
        "query_id": result["query"].query_id,
        "target_age_ka": result["query"].target_age_ka,
        "steps": [
            "verify_R4_56_governance_baseline",
            "verify_exact_R3_parent_hashes",
            "resolve_each_requested_product_independently",
            "use_exact_parent_state_when_target_age_exists",
            "otherwise_use_only_bounded_bracketing_authorities",
            "for_population_spatial_detail_use_cyclic_longitude_and_constrain_population_total_and_active_deme_count_to_R3_28_summary",
            "apply_optional_native_grid_region_slice",
            "emit_derived_state_without_canonical_write",
        ],
        "product_methods": result["provenance"],
        "randomness_used": False,
        "external_engine_execution": False,
        "full_history_rerun": False,
        "canonical_write": False,
    }
    recipe["recipe_sha256"] = hashlib.sha256(_canonical_json_bytes(recipe)).hexdigest()
    return recipe


def _query_summary(result: dict[str, Any]) -> dict[str, Any]:
    a = result["arrays"]
    return {
        "stage": STAGE,
        "status": "R50_DERIVED_STATE_QUERY_COMPLETE",
        "query_id": result["query"].query_id,
        "target_age_ka": result["query"].target_age_ka,
        "semantic_state_sha256": result["semantic_state_sha256"],
        "array_shapes": {k: list(v.shape) for k, v in a.items()},
        "domain_coverage": result["domain_coverage"],
        "provenance_modes": {k: v["mode"] for k, v in result["provenance"].items()},
        "governance": result["governance"],
    }


def write_query_package(result: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    query = result["query"]
    slug = _age_slug(query.target_age_ka)
    prefix = f"R5_0_{slug}"
    query_path = out_dir / f"{prefix}_QUERY.json"
    state_path = out_dir / f"{prefix}_DERIVED_STATE.npz"
    provenance_path = out_dir / f"{prefix}_PROVENANCE.json"
    uncertainty_path = out_dir / f"{prefix}_UNCERTAINTY.json"
    recipe_path = out_dir / f"{prefix}_REPLAY_RECIPE.json"
    summary_path = out_dir / f"{prefix}_QUERY_SUMMARY.json"

    write_json(query_path, query.to_json())
    np.savez_compressed(state_path, **result["arrays"])
    write_json(provenance_path, {
        "stage": STAGE,
        "query_id": query.query_id,
        "target_age_ka": query.target_age_ka,
        "parent_hashes": EXPECTED_PARENT_HASHES,
        "products": result["provenance"],
        "domain_coverage": result["domain_coverage"],
        "canonical_write": False,
    })
    write_json(uncertainty_path, _uncertainty_record(result))
    write_json(recipe_path, _recipe_record(result))
    write_json(summary_path, _query_summary(result))

    return {
        "query": query_path,
        "state": state_path,
        "provenance": provenance_path,
        "uncertainty": uncertainty_path,
        "recipe": recipe_path,
        "summary": summary_path,
    }


def execute_query(
    root: Path,
    query: R50QueryContract | Mapping[str, Any],
    *,
    out_dir: Path | None = None,
    allow_unverified_r456: bool = False,
) -> dict[str, Any]:
    q = query if isinstance(query, R50QueryContract) else R50QueryContract.from_mapping(query)
    with R50AuthorityResolver(root, allow_unverified_r456=allow_unverified_r456) as resolver:
        result = resolver.resolve(q)
        result["r456_authority"] = resolver.r456
        result["r456_verified"] = resolver.r456_verified
    if out_dir is not None:
        result["package_files"] = write_query_package(result, out_dir)
    return result


def _audit_demo(
    root: Path,
    resolver: R50AuthorityResolver,
    r20: dict[str, Any],
    r175: dict[str, Any],
    parent_before: dict[str, str],
    parent_after: dict[str, str],
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def ck(name: str, cond: bool, detail: Any = None) -> None:
        checks.append({"name": name, "pass": bool(cond), "detail": detail})

    ck("r456_governance_verified_or_explicit_dev_mode", resolver.r456_verified or resolver.allow_unverified_r456, resolver.r456["status"])
    ck("all_exact_parent_hashes_match", parent_before == EXPECTED_PARENT_HASHES)
    ck("parent_hashes_unchanged_after_queries", parent_before == parent_after)
    ck("20ka_population_summary_exact", r20["provenance"]["population_summary"]["mode"] == "EXACT")
    ck("20ka_population_detail_exact", r20["provenance"]["population_detail"]["mode"] == "EXACT")
    ck("20ka_environment_exact", r20["provenance"]["environment"]["mode"] == "EXACT")
    ck("20ka_flora_exact", r20["provenance"]["flora"]["mode"] == "EXACT")
    ck("20ka_fauna_partner_trajectory_exact", r20["provenance"]["fauna"]["mode"] == "EXACT")
    ck("17p5ka_population_summary_exact", r175["provenance"]["population_summary"]["mode"] == "EXACT")
    ck("17p5ka_population_detail_bounded_20_15", r175["provenance"]["population_detail"]["mode"] == "BOUNDED_SPATIAL_RECONSTRUCTION" and r175["provenance"]["population_detail"]["source_ages_ka"] == [20.0, 15.0])
    ck("17p5ka_environment_bounded_20_15", r175["provenance"]["environment"]["mode"] == "BRACKETED_LINEAR" and r175["provenance"]["environment"]["source_ages_ka"] == [20.0, 15.0])
    ck("17p5ka_flora_bounded_20_15", r175["provenance"]["flora"]["mode"] == "BRACKETED_LINEAR" and r175["provenance"]["flora"]["source_ages_ka"] == [20.0, 15.0])
    ck("17p5ka_fauna_bounded_20_15", r175["provenance"]["fauna"]["mode"] == "BRACKETED_LINEAR" and r175["provenance"]["fauna"]["source_ages_ka"] == [20.0, 15.0])
    ck("20ka_expected_native_shapes", r20["arrays"]["environment_fields"].shape == (90, 180, 7) and r20["arrays"]["producer_landscape"].shape == (36, 90, 180, 4))
    ck("17p5ka_expected_native_shapes", r175["arrays"]["environment_fields"].shape == (90, 180, 7) and r175["arrays"]["producer_landscape"].shape == (36, 90, 180, 4))
    ck("fauna_scope_explicitly_partial", r175["domain_coverage"]["fauna"].startswith("PARTIAL_"))
    ck("geology_scope_explicitly_surface_only", r175["domain_coverage"]["surface_paleogeography"].startswith("PARTIAL_"))
    ck("no_extrapolation", not r20["governance"]["temporal_extrapolation_performed"] and not r175["governance"]["temporal_extrapolation_performed"])
    ck("no_full_history_rerun", not r20["governance"]["full_history_rerun_performed"] and not r175["governance"]["full_history_rerun_performed"])
    ck("no_external_engine_execution", not r20["governance"]["external_engine_execution_performed"] and not r175["governance"]["external_engine_execution_performed"])
    ck("no_canonical_write", not r20["governance"]["canonical_state_changed"] and not r175["governance"]["canonical_state_changed"])
    ck("deep_biological_coupling_off", not r20["governance"]["deep_biological_coupling"] and not r175["governance"]["deep_biological_coupling"])
    # Resolve 17.5 a second time: semantic hash must be identical with no stochastic state.
    r175_repeat = resolver.resolve(r175["query"])
    ck("17p5ka_deterministic_semantic_hash", r175_repeat["semantic_state_sha256"] == r175["semantic_state_sha256"])
    failed = [x for x in checks if not x["pass"]]
    scientific = resolver.r456_verified and not failed
    status = CANDIDATE_PASS if scientific else (DEV_PASS if not failed else "FAIL_R50_INTEGRATED_AUDIT")
    return {
        "stage": STAGE,
        "stage_name": STAGE_NAME,
        "status": status,
        "scientific_candidate_eligible": scientific,
        "checks_passed": len(checks) - len(failed),
        "checks_total": len(checks),
        "checks_failed": len(failed),
        "checks": checks,
        "summary": {
            "queries": [20.0, 17.5],
            "r456_runtime_verified": resolver.r456_verified,
            "exact_parent_hash_count": len(EXPECTED_PARENT_HASHES),
            "full_history_rerun_performed": False,
            "external_engine_execution_performed": False,
            "canonical_state_changed": False,
            "deep_biological_coupling": False,
            "20ka_semantic_state_sha256": r20["semantic_state_sha256"],
            "17p5ka_semantic_state_sha256": r175["semantic_state_sha256"],
        },
    }


def run_demonstration(
    root: Path,
    *,
    out_dir: Path | None = None,
    allow_unverified_r456: bool = False,
) -> dict[str, Any]:
    root = Path(root).resolve()
    out_dir = Path(out_dir) if out_dir is not None else root / "outputs" / "v0_6D1_R5_0"
    queries = [
        R50QueryContract(query_id="R50_DEMO_EXACT_20KA", target_age_ka=20.0),
        R50QueryContract(query_id="R50_DEMO_ARBITRARY_17P5KA", target_age_ka=17.5),
    ]
    with R50AuthorityResolver(root, allow_unverified_r456=allow_unverified_r456) as resolver:
        parent_before = dict(resolver.parent_hashes)
        r20 = resolver.resolve(queries[0])
        r175 = resolver.resolve(queries[1])
        files20 = write_query_package(r20, out_dir)
        files175 = write_query_package(r175, out_dir)
        parent_after = {rel: sha256_file(root / rel) for rel in EXPECTED_PARENT_HASHES}
        audit = _audit_demo(root, resolver, r20, r175, parent_before, parent_after)
        audit_path = out_dir / "R5_0_INTEGRATED_AUDIT.json"
        authority_path = out_dir / "R5_0_AUTHORITY_RESOLUTION_SUMMARY.json"
        recipes_path = out_dir / "R5_0_DETERMINISTIC_REPLAY_RECIPES.json"
        write_json(audit_path, audit)
        write_json(authority_path, {
            "stage": STAGE,
            "status": "R50_AUTHORITY_RESOLUTION_COMPLETE",
            "r456_authority": resolver.r456,
            "exact_parent_hashes": parent_before,
            "queries": {
                "20ka": _query_summary(r20),
                "17p5ka": _query_summary(r175),
            },
        })
        write_json(recipes_path, {
            "stage": STAGE,
            "status": "R50_DETERMINISTIC_REPLAY_RECIPES",
            "recipes": [_recipe_record(r20), _recipe_record(r175)],
        })

        # Candidate manifest is deliberately allowlist-driven. A rerun after a seal,
        # or a directory containing ad-hoc query products, must not absorb stale or
        # unrelated files into the scientific candidate authority.
        candidate_paths = [
            *files20.values(),
            *files175.values(),
            audit_path,
            authority_path,
            recipes_path,
        ]
        manifest_files = {}
        for p in sorted(candidate_paths, key=lambda x: x.name):
            if not p.is_file():
                raise R50QueryError(f"Missing candidate artifact while building manifest: {p}")
            manifest_files[p.name] = {"bytes": p.stat().st_size, "sha256": sha256_file(p)}
        if len(manifest_files) != 15:
            raise R50QueryError(f"R5.0 candidate artifact allowlist drift: expected 15 files, got {len(manifest_files)}")
        write_json(out_dir / "R5_0_OUTPUT_MANIFEST.json", {
            "stage": STAGE,
            "status": audit["status"],
            "scientific_candidate_eligible": audit["scientific_candidate_eligible"],
            "candidate_artifact_count": len(manifest_files),
            "manifest_policy": "EXACT_ALLOWLIST_NO_DIRECTORY_SWEEP",
            "files": manifest_files,
        })
        return {
            "audit": audit,
            "out_dir": out_dir,
            "query_files": {"20ka": files20, "17p5ka": files175},
        }
