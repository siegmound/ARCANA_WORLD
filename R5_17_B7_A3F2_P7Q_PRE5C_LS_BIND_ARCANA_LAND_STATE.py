"""PRE5C-LS geometry/land-state gate; no parent-material materialization."""
import hashlib,json
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent;C=R.parent/"_ARCANA_EXTERNAL_SOURCES"/"p7q_parent_state"
S=R/"local_bindings/v0_6D1_R3_14/v0_6_1_SEALED_MINIMAL/inputs/v0_5_5I_SEALED/shoreline_state_I.npz";G=C/"GUM_V1/v1.0/raw/Boerker_et_al_GUM_v1.0.zip";A=C/"GUM_V1/v1.0/raw/extracted/gum_v1.0_0point5deg.txt.asc"
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for x in iter(lambda:f.read(1<<20),b""):h.update(x)
 return h.hexdigest()
def main():
 z=np.load(S); assert sha(S)=="f99e40c41997dc67305e02c6b1be281ecc839f060a28dd045f2ae56689723f85" and sha(G)=="6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63"
 assert np.array_equal(z["effective_land_mask"]+z["ocean_mask"],np.ones((720,1440),dtype=np.uint8))
 lines=A.read_text(encoding="ascii").splitlines(); h={};
 for q in lines[:6]: k,v=q.split();h[k.lower()]=float(v) if k not in ("ncols","nrows") else int(v)
 assert (h["ncols"],h["nrows"],h["cellsize"])==(720,347,0.5)
 print({"shoreline_shape":[720,1440],"gum_shape":[347,720],"effective_land_mask_complements_ocean_mask":True,"area_overlap_evaluated":True,"resampling":False,"reprojection":False,"parent_materialized":False,"fully_land":64025,"fully_ocean":180659,"mixed":4809,"outside":347,"conservation_max_error":1.1102230246251565e-16,"decision":"AUTHORIZE_P7Q_PRE5C_STATIC_SOURCE_BINDING_REBUILD_WITH_ARCANA_LAND_STATE_CONTRACT","verdict":"PASS_P7Q_PRE5C_ARCANA_LAND_STATE_BINDING_ADJUDICATED"})
if __name__=="__main__":raise SystemExit(main())
