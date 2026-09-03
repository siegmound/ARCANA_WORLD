from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path, PurePosixPath
from typing import Any, Mapping, Sequence
import csv
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

EXPECTED_D22_NAME = "ARCANA_WorldSim_v0_6_3D2_2_CHA1_High_Resolution_Replay.zip"
EXPECTED_D22_SHA256 = "42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8"
EXPECTED_D22_BYTES = 10_142_030
EXPECTED_D1_SHA256 = "75a8bd4e90103e20ff308ef052871289eb3a608a558288abf1622c36a3b7fb1c"
EXPECTED_EXTINCTION_IDENTITY_SHA256 = "51cea046a868a0df020faf3ed4a47c40b2101f9d1152ad55504bf068c362086a"

EXPECTED_SURVIVORS = (
    "HSG_007","HSG_009","HSG_012","HSG_013","HSG_016","HSG_019","HSG_022","HSG_025",
    "BRW_013","LVF_008","LVF_009","LVF_013","LVF_016","LVF_018",
    "RPT_002","RPT_003","RPT_004","RPT_009","RPT_011","RPT_012","RPT_015","RPT_017",
    "RPT_019","RPT_021","RPT_022","RPT_023","CAR_001","CAR_008","CAR_014","APX_007","APX_008",
)

RAW_DIR_SUFFIX = Path("outputs/hybrid1/cha1_highres_v0_6_3D2_2")
REQUIRED_RAW_BASENAMES = (
    "cha1_highres_state.npz",
    "species_population_timeseries.csv",
    "physical_foodweb_timeseries.csv",
    "extinction_events.json",
    "CHA1_survivor_registry.json",
    "species_diagnostics.json",
    "recovery_milestones.json",
    "solver_diagnostics.json",
    "reptiloid_survivor_E_M.json",
    "cha1_spatial_survivor_footprint_66Ma.npz",
    "cha1_highres_audit.json",
    "cha1_highres_manifest.json",
)

class BindingError(RuntimeError):
    pass


def sha256_file(path: Path, block: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _is_safe_zip_member(name: str) -> bool:
    p = PurePosixPath(name)
    return not (p.is_absolute() or ".." in p.parts or (p.parts and ":" in p.parts[0]))


def verify_canonical_d22_archive(path: Path, *, require_canonical_hash: bool = True,
                                 expected_hash: str = EXPECTED_D22_SHA256,
                                 expected_bytes: int = EXPECTED_D22_BYTES) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise BindingError(f"D2.2 archive missing: {path}: FAIL_CLOSED")
    size = path.stat().st_size
    digest = sha256_file(path)
    if require_canonical_hash and digest.lower() != expected_hash.lower():
        raise BindingError(f"D2.2 SHA-256 mismatch: {digest} != {expected_hash}: FAIL_CLOSED")
    if require_canonical_hash and size != expected_bytes:
        raise BindingError(f"D2.2 byte-size mismatch: {size} != {expected_bytes}: FAIL_CLOSED")
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        unsafe = [n for n in names if not _is_safe_zip_member(n)]
        if unsafe:
            raise BindingError(f"unsafe D2.2 archive members: {unsafe[:3]}: FAIL_CLOSED")
        basenames = {PurePosixPath(n).name for n in names if not n.endswith("/")}
        missing = [x for x in REQUIRED_RAW_BASENAMES if x not in basenames]
        if missing:
            raise BindingError(f"D2.2 required RAW products missing: {missing}: FAIL_CLOSED")
    return {
        "path": str(path), "bytes": size, "sha256": digest,
        "canonical_hash_required": require_canonical_hash,
        "required_raw_products": len(REQUIRED_RAW_BASENAMES),
        "status": "PASS_CANONICAL_D22_ARCHIVE_BINDING" if require_canonical_hash else "PASS_TEST_ARCHIVE_BINDING",
    }


def safe_extract_archive(path: Path, outdir: Path) -> Path:
    path, outdir = Path(path), Path(outdir)
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path) as zf:
        for info in zf.infolist():
            if not _is_safe_zip_member(info.filename):
                raise BindingError(f"unsafe path in archive: {info.filename}: FAIL_CLOSED")
        zf.extractall(outdir)
    return outdir


def find_raw_dir(extracted_root: Path) -> Path:
    extracted_root = Path(extracted_root)
    exact = list(extracted_root.rglob("cha1_highres_manifest.json"))
    if len(exact) != 1:
        raise BindingError(f"expected exactly one D2.2 highres manifest, found {len(exact)}: FAIL_CLOSED")
    raw = exact[0].parent
    missing = [x for x in REQUIRED_RAW_BASENAMES if not (raw / x).is_file()]
    if missing:
        raise BindingError(f"extracted D2.2 RAW set incomplete: {missing}: FAIL_CLOSED")
    return raw


def _load_json(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _survivor_ids(raw: Any) -> list[str]:
    if isinstance(raw, list):
        vals = raw
    elif isinstance(raw, dict):
        for key in ("survivors", "survivor_species", "species_ids", "registry"):
            if key in raw:
                vals = raw[key]
                break
        else:
            vals = [k for k, v in raw.items() if v is True]
    else:
        raise BindingError("unsupported survivor registry schema: FAIL_CLOSED")
    out=[]
    for v in vals:
        if isinstance(v, str): out.append(v)
        elif isinstance(v, Mapping):
            sid=v.get("species_id") or v.get("id")
            if sid: out.append(str(sid))
    return out


def _audit_metrics(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    out = dict(raw)
    for k in ("metrics","summary","bottleneck","result"):
        if isinstance(raw.get(k), dict):
            out = {**out, **raw[k]}
    return out


def validate_d22_raw_reference(raw_dir: Path) -> dict[str, Any]:
    raw_dir = Path(raw_dir)
    survivors = sorted(_survivor_ids(_load_json(raw_dir / "CHA1_survivor_registry.json")))
    if survivors != sorted(EXPECTED_SURVIVORS):
        raise BindingError("D2.2 survivor identity set differs from preferred authority: FAIL_CLOSED")

    audit = _audit_metrics(_load_json(raw_dir / "cha1_highres_audit.json"))
    text = json.dumps(audit, sort_keys=True)
    # The schemas evolved; use explicit values if present and otherwise validate from diagnostics.
    diagnostics = _load_json(raw_dir / "species_diagnostics.json")
    if isinstance(diagnostics, dict):
        for key in ("species", "rows", "diagnostics"):
            if isinstance(diagnostics.get(key), list): diagnostics = diagnostics[key]; break
    if not isinstance(diagnostics, list):
        raise BindingError("species_diagnostics is not a species list: FAIL_CLOSED")
    ids = [str(r.get("species_id")) for r in diagnostics if isinstance(r, dict)]
    if len(ids) != 120 or len(set(ids)) != 120:
        raise BindingError(f"D2.2 diagnostics species cardinality {len(ids)} != 120: FAIL_CLOSED")
    diag_surv = sorted(str(r["species_id"]) for r in diagnostics if r.get("survived_D2_2_CHA1") is True)
    if diag_surv != sorted(EXPECTED_SURVIVORS):
        raise BindingError("D2.2 diagnostic survivor set differs from registry: FAIL_CLOSED")
    extinct = [r for r in diagnostics if r.get("survived_D2_2_CHA1") is False]
    if len(extinct) != 89:
        raise BindingError(f"D2.2 extinction cardinality {len(extinct)} != 89: FAIL_CLOSED")
    max_ext = max(float(r["extinction_time_year"]) for r in extinct)
    if max_ext > 14.4132223338906 + 1e-9:
        raise BindingError("D2.2 extinction timing exceeds authoritative max: FAIL_CLOSED")

    # Time-series anchors are part of the RAW parity witness.
    anchors={0.0:1616.489701140672,1.0:1183.7601444304578,5.0:577.4537216154268,
             10.0:566.1275990697238,100.0:1594.078122887357,1000.0:1616.4934030593372}
    rows=[]
    with (raw_dir / "physical_foodweb_timeseries.csv").open(newline="", encoding="utf-8-sig") as f:
        rows=list(csv.DictReader(f))
    errors={}
    for t, expected in anchors.items():
        candidates=[r for r in rows if abs(float(r["relative_year"])-t)<1e-12]
        if not candidates:
            raise BindingError(f"D2.2 physical timeseries lacks anchor year {t}: FAIL_CLOSED")
        got=float(candidates[0]["total_population"])
        errors[str(t)]=abs(got-expected)
        if abs(got-expected) > max(1e-9, abs(expected)*2e-10):
            raise BindingError(f"D2.2 population parity drift at {t} y: {got} vs {expected}: FAIL_CLOSED")

    return {
        "status":"PASS_D22_RAW_REFERENCE_PARITY",
        "initial_species":120,
        "extinctions":89,
        "survivors":31,
        "survivor_ids":list(EXPECTED_SURVIVORS),
        "max_extinction_time_year":max_ext,
        "population_anchor_abs_errors":errors,
        "audit_contains_pass_status":"PASS_CHA1_HIGH_RESOLUTION_REPLAY_CANDIDATE" in text,
        "expected_extinction_identity_sha256":EXPECTED_EXTINCTION_IDENTITY_SHA256,
    }


def discover_runtime_surfaces(extracted_root: Path) -> dict[str, Any]:
    root=Path(extracted_root)
    py=list(root.rglob("*.py"))
    candidates=[]
    signatures=("solve_ivp","cha1_highres","hazard_threshold","FastProcessProvider","PASS_CHA1_HIGH_RESOLUTION_REPLAY_CANDIDATE")
    for p in py:
        try: txt=p.read_text(encoding="utf-8", errors="ignore")
        except OSError: continue
        score=sum(1 for s in signatures if s in txt)
        if score:
            candidates.append({"path":str(p.relative_to(root)),"score":score,
                               "contains_main":"if __name__" in txt,
                               "contains_solve_ivp":"solve_ivp" in txt})
    candidates.sort(key=lambda x:(-x["score"],x["path"]))
    return {"python_files":len(py),"candidate_runtime_files":candidates[:40],"status":"DISCOVERY_ONLY_NOT_EXECUTION_AUTHORITY"}


def require_historical_hx_inputs(*, d22_archive: Path|None, d1_archive: Path|None,
                                 d2_precha1_archive: Path|None,
                                 d1_population_state: Path|None,
                                 d1_variance_state: Path|None) -> None:
    missing=[]
    for name,val in (("D22_ARCHIVE",d22_archive),("D1_ARCHIVE",d1_archive),("D2_PRECHA1_ARCHIVE",d2_precha1_archive),
                     ("D1_210MA_POPULATION_STATE",d1_population_state),("D1_210MA_VARIANCE_STATE",d1_variance_state)):
        if val is None or not Path(val).is_file(): missing.append(name)
    if missing:
        raise BindingError("historical HX executable inputs missing: "+",".join(missing)+": FAIL_CLOSED")


def run_external_command(command: Sequence[str], cwd: Path, *, env: Mapping[str,str]|None=None) -> dict[str,Any]:
    if not command:
        raise BindingError("empty runtime command: FAIL_CLOSED")
    cp=subprocess.run(list(command),cwd=str(cwd),text=True,capture_output=True,env=None if env is None else dict(env))
    if cp.returncode != 0:
        raise BindingError(f"runtime command failed rc={cp.returncode}: {cp.stderr[-2000:]}: FAIL_CLOSED")
    return {"command":list(command),"returncode":cp.returncode,"stdout_tail":cp.stdout[-4000:],"stderr_tail":cp.stderr[-4000:]}

GOVERNANCE = {
    "reconstruct_D2_from_summaries":False,
    "execute_unverified_D22_archive":False,
    "allow_D22_survivor_identity_drift_in_Deep_OFF":False,
    "direct_Deep_survivor_selector":False,
    "direct_Deep_speciation":False,
    "named_survivor_protection":False,
    "HSG025_proxy_allowed_in_historical_HX":False,
    "full_HX_allowed_without_preCHA1_executable_runtime":False,
}
