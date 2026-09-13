"""PRE5-C static provider-grid diagnostic; never creates canonical ARCANA state."""
from __future__ import annotations
import hashlib, json, struct, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT.parent / "_ARCANA_EXTERNAL_SOURCES" / "p7q_parent_state"
OUT = CACHE / "PRE5C_STATIC_PROTOTYPE"
EXPECTED = {
    "GUM_V1": ("GUM_V1/v1.0/raw/Boerker_et_al_GUM_v1.0.zip", "6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63"),
    "GLIM_V1": ("GLIM_V1/v1.0/raw/hartmann-moosdorf_2012.zip", "43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e"),
}

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""): h.update(chunk)
    return h.hexdigest()

def read_grid(path: Path):
    lines = path.read_text(encoding="ascii").splitlines()
    header = {}
    for line in lines[:6]:
        k, v = line.split(None, 1); header[k.lower()] = float(v) if k.lower() != "ncols" and k.lower() != "nrows" else int(v)
    values = [int(float(x)) for line in lines[6:] for x in line.split()]
    assert len(values) == header["ncols"] * header["nrows"]
    nodata = int(header["nodata_value"])
    valid = sum(v != nodata for v in values)
    return header, values, valid, len(values) - valid

def main() -> int:
    hashes = {}
    for name, (rel, expected) in EXPECTED.items():
        path = CACHE / rel; assert path.is_file(), path
        actual = sha256(path); assert actual == expected, (name, actual)
        hashes[name] = {"path": str(path), "bytes": path.stat().st_size, "sha256": actual}
    glim_path = CACHE / "GLIM_V1/v1.0/metadata/extracted/glim_wgs84_0point5deg.txt.asc"
    gum_path = CACHE / "GUM_V1/v1.0/raw/extracted/gum_v1.0_0point5deg.txt.asc"
    gh, gv, glim_valid, glim_nodata = read_grid(glim_path)
    uh, uv, gum_valid, gum_nodata = read_grid(gum_path)
    congruent = gh == uh and len(gv) == len(uv)
    assert not congruent and gh["nrows"] == 360 and uh["nrows"] == 347
    OUT.mkdir(parents=True, exist_ok=True)
    payload = OUT / "PRE5C_PROVIDER_GRID_DIAGNOSTIC.bin"
    with payload.open("wb") as f:
        f.write(b"ARCANA_PRE5C_PROVIDER_GRID_DIAGNOSTIC_V1\0")
        for vals in (gv, uv):
            f.write(struct.pack("<I", len(vals)))
            f.write(struct.pack("<" + "i" * len(vals), *vals))
    summary = {"format":"deterministic raw binary", "grid_binding_mode":"INCONGRUENT_PROVIDER_GRIDS__NO_CELLWISE_STATE", "GUM_V1":{"grid":uh,"valid_cells":gum_valid,"nodata_cells":gum_nodata}, "GLIM_V1":{"grid":gh,"valid_cells":glim_valid,"nodata_or_nd_cells":glim_nodata}, "payload":{"path":str(payload),"bytes":payload.stat().st_size,"sha256":sha256(payload)}, "source_archives":hashes}
    (OUT / "PRE5C_PROVIDER_GRID_DIAGNOSTIC.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"source_hashes_verified":True,"grid_congruent":False,"gum_valid":gum_valid,"glim_valid":glim_valid,"payload":summary["payload"]}, sort_keys=True))
    return 0
if __name__ == "__main__": raise SystemExit(main())
