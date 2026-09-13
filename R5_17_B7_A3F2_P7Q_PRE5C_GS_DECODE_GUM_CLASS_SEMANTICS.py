"""PRE5C-GS completeness validator."""
import collections,hashlib,json,struct
from pathlib import Path
R=Path(__file__).resolve().parent;C=R.parent/"_ARCANA_EXTERNAL_SOURCES"/"p7q_parent_state";G=C/"GUM_V1/v1.0/raw/Boerker_et_al_GUM_v1.0.zip";D=C/"GUM_V1/v1.0/raw/extracted/GUM_v1.0.dbf";M=R/"R5_17_B7_A3F2_P7Q_PRE5C_GS_GUM_TO_ARCANA_BRANCH_MAPPING_CANDIDATE.json"
O=set("Au Ae Af Al Ap At Cu Ca Du Eu Ea Ed El Er Gu Gf Gl Gm Gp Gt Iy Lu Mu Ou Op Or Pu Pg Pp Ps Us Wu Wl Wr Yu Yb Yd Yl Ym Ys Zu".split())
def sha(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def main():
 assert sha(G)=="6a2d47f2bc8f6df745c569003f1f536d37c78153e98b54005bfbcccc53d6ee63"
 with D.open("rb") as f:
  h=f.read(32);n=struct.unpack_from("<I",h,4)[0];hl=struct.unpack_from("<H",h,8)[0];rl=struct.unpack_from("<H",h,10)[0];q=f.read(hl-32);fs=[(q[o:o+11].split(b"\0",1)[0].decode(),chr(q[o+11]),q[o+16]) for o in range(0,len(q)-1,32)];i=next(j for j,x in enumerate(fs) if x[0]=="XX");off=1+sum(x[2] for x in fs[:i]);c=collections.Counter(f.read(rl)[off:off+fs[i][2]].decode("latin1").strip() for _ in range(n))
 m=json.loads(M.read_text(encoding="utf-8"));r=m["records"];codes=[x["source_code"] for x in r];g=collections.Counter(x["mapping_status"] for x in r)
 assert n==911551 and set(c)==O and len(r)==41 and set(codes)==O and len(codes)==len(set(codes)) and not m["outside_current_parent_material_scope"]
 assert g==collections.Counter({"EXACT_BRANCH_MAPPING":20,"CONDITIONAL_BRANCH_MAPPING":2,"MIXED_SOURCE_CLASS_RETAIN_UNRESOLVED":7,"NON_MATERIAL_DOMAIN_CLASS":4,"UNKNOWN_MATERIAL_CLASS":1,"REQUIRES_LAND_STATE_BINDING":7})
 e=next(x for x in r if x["source_code"]=="Ea");assert e["mapping_status"]=="EXACT_BRANCH_MAPPING" and e["target_material_branch"]=="TRANSPORTED_AEOLIAN"
 print({"records":n,"official_xx":41,"observed_xx":41,"mapped_xx":41,"missing_mapping":[],"duplicate_mapping":[],"exact":20,"conditional":2,"mixed":7,"non_material":4,"unknown":1,"land_state_gated":7,"Ea":"EXACT_BRANCH_MAPPING -> TRANSPORTED_AEOLIAN","decision":"AUTHORIZE_P7Q_PRE5C_LAND_STATE_BINDING_GATE_WITH_GUM_SEMANTIC_REGISTRY","verdict":"PASS_P7Q_PRE5C_GUM_CLASS_SEMANTIC_DECODING_ADJUDICATED"})
if __name__=="__main__":raise SystemExit(main())
