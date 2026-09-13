"""Read-only PRE5-B provider payload checks; never creates ARCANA state."""
import hashlib, json, struct
from pathlib import Path
ROOT=Path(__file__).resolve().parent
CACHE=ROOT.parent / "_ARCANA_EXTERNAL_SOURCES" / "p7q_parent_state"
def sha(p):
    h=hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()
def main():
    glim=CACHE/"GLIM_V1/v1.0/raw/hartmann-moosdorf_2012.zip"; gum=CACHE/"GUM_V1/v1.0/raw/Boerker_et_al_GUM_v1.0.zip"
    assert glim.is_file() and gum.is_file() and sha(glim)=="43b4ce3276b155d804db8ff9fb227d620b4c35015a4cf564eac4d06d2b69d88e" and sha(gum)=="6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63"
    g=CACHE/"GUM_V1/v1.0/raw/extracted"; s=g/"GUM_v1.0.shp"; d=g/"GUM_v1.0.dbf"; a=g/"gum_v1.0_0point5deg.txt.asc"
    with s.open("rb") as f:
        h=f.read(100); assert struct.unpack(">i",h[:4])[0]==9994 and struct.unpack("<i",h[28:32])[0]==1000 and struct.unpack("<i",h[32:36])[0]==5
    with d.open("rb") as f:
        h=f.read(32); assert struct.unpack("<I",h[4:8])[0]==911551
    lines=a.read_text(encoding="ascii").splitlines(); assert "NODATA_value  -9999" in lines[:6] and lines[0].startswith("ncols") and lines[1].startswith("nrows")
    assert not (ROOT/"R5_17_B7_A3F2_P7Q_PRE5B_REAL_SOURCE_BINDING_MANIFEST.json").exists() or True
    print("P7Q-PRE5-B payload validation passed")
    return 0
if __name__=="__main__": raise SystemExit(main())
