# ARCANA R6 — S3-D4-C original S2 phase chemistry: read-only audited next step

Date: 2026-11-24. Status: SOURCE-ONLY PROCEDURE READY; FAIR READBACK NOT YET EXECUTED. The D4-D source code at exact commit fbb1e77c54e3545ea2e7e7b52226ed0576f1993e passed 122/122 targeted Python tests on user-operated FAIR in 0.42s with exit 0. This does not prove numerical repeatability acceptance or scientific calibration.

## Scientific need

For original Perple_X BL691 source commit 950d882bb6a9325a627109aa7154f7b526aa3087, solution_model.dat blob 564742a569998a768c2d8e15d2b9599ee90438d1 warns:
- Fsp(C1) does not intrinsically select stable I1/C1 feldspar state;
- Augite(G) is not intended for Na-rich compositions; source whole-rock Na2O input alone does not determine phase composition;
- cAmph(G) omits some Fe3+/Ti exchanges and requires phase-specific applicability review.
No numeric sodium cutoff or I1/C1 state can be decided by a single archived output. The goal now is to **extract authentic source-native per-phase composition tokens**, not change phase model or certify rock realism.

## Bounded proposed operation

Run the following shell code in an existing FAIR S3 worktree with arcana-r6-linux, PYTHONPATH pointing to repository src+root, no engine calls. It verifies original S2 REAL manifest SHA256 74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604 and separately verifies original member file SHA256 before reading two anchored native outputs. It reuses exact previously FAIR-tested D3 source parsers to validate the outputs before extracting native phase rows. It does not write, execute a solver, deduplicate, create manifests, or modify S2. Output may be large; preserve original stdout and report an exact exit.

```bash
python - <<'PY'
from pathlib import Path
from decimal import Decimal
import hashlib, json, re, tomllib
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import (
    read_magemin_case, read_perplex_prn
)

ROOT = Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_S2_REPEATABILITY_NEW01")
EXPECTED = "74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604"

def sha(data):
    return hashlib.sha256(data).hexdigest()

raw = (ROOT / "MANIFEST.json").read_bytes()
assert sha(raw) == EXPECTED
manifest = json.loads(raw)
def member(name):
    path = ROOT / name
    assert path.is_file() and not path.is_symlink()
    assert path.resolve().is_relative_to(ROOT.resolve())
    data = path.read_bytes()
    assert sha(data) == manifest["files_sha256"][name]
    return data

print("=== S2 ORIGINAL MAGEMIN CUSTOM_IG PHASE CHEMISTRY ===")
native = tomllib.loads(member("MAGEMIN_01/NATIVE.toml").decode("utf-8"))
case = native["cases"]["MAGEMIN_CUSTOM_IG"]
parsed = read_magemin_case(case, 10, 1100)
print("P_KBAR=10 T_C=1100 N_PHASES=", len(parsed["phases"]))
for phase, wt, components in zip(case["phases"], case["phase_mass_fractions"],
                                  case["phase_comp_wt"], strict=True):
    print(json.dumps({"phase":phase, "phase_mass_fraction":wt,
                      "component_mass_fractions":dict(zip(case["oxides"],components,strict=True))},
                      sort_keys=True))

print("=== S2 ORIGINAL PERPLEX BL691 PHASE CHEMISTRY ===")
prn = member("PERPLEX_01/BL691_MEEMUM/bl691_MEEMUM.prn").decode("utf-8",errors="replace")
parsed = read_perplex_prn(prn, 4000, 1050)
body = prn.split("Phase Compositions (molar  proportions):",1)[1].split("Phase speciation",1)[0]
lines = [x.strip() for x in body.splitlines() if x.strip()]
columns = re.split(r"\s{2,}",lines[0])[4:]
expected_components = {"Na2O","MgO","Al2O3","K2O","CaO","TiO2","FeO","O2","H2O","SiO2"}
assert len(columns)==10 and set(columns)==expected_components
count=0
found=set()
for line in lines[1:]:
    fields=line.split()
    assert len(fields)==15, (len(fields), fields[:3])
    name=fields[0]
    assert name in parsed["phases"] and name not in found
    components=dict(zip(columns,fields[5:],strict=True))
    assert all(Decimal(v).is_finite() and Decimal(v)>=0 for v in components.values())
    row={"phase":name,"phase_wt_percent_printed":fields[1],
         "phase_mol_printed":fields[4],
         "native_oxide_molar_proportion_tokens":components}
    print(json.dumps(row,sort_keys=True))
    found.add(name);count+=1
assert found == set(parsed["phases"])
print("PERPLEX_PHASES=",count)
for name in ("Fsp(C1)","Augite(G)","cAmph(G)"):
    print(name,"PRESENT_IN_ORIGINAL_S2=",name in found)
print("PERPLEX_I1_C1_STABLE_BRANCH=UNKNOWN")
print("PERPLEX_AUGITE_NA_MODEL_CALIBRATION=UNKNOWN")
print("PERPLEX_AMPH_FE3_TI_MODEL_APPLICABILITY=UNKNOWN")
print("S3_D4_C_ORIGINAL_S2_PHASE_CHEMISTRY_READONLY_PASS")
PY
S3_D4_C_EXIT=$?
echo "S3_D4_C_PHASE_AUDIT_EXIT=$S3_D4_C_EXIT"
```

## Interpretation

- MAGEMin `phase_comp_wt` is a **native mass-fraction vector** over oxide components after source Fe2O3-to-FeO+O bookkeeping; separate from original input oxide wt%.
- Perple_X `Phase Compositions (molar  proportions)` table reports **printed molar component tokens**, with finite decimal precision; the Python code validates no malformed/non-finite token but does not treat values as calibrated cation site fractions. The `Fsp(C1)`, `Augite(G)`, `cAmph(G)` labels are flags for further literature-based model checks.
- These two chemistry bases cannot be directly compared. `UNKNOWN` is preserved for all 50 S3 candidate P/T-X cells. Original two points are engineering anchors, not scientific experimental validation.
- Green et al 2025 corrected G25 model uncertainty about ±1kbar/±50°C boundary scale and accessory minerals remains a **geological uncertainty**, never the native solver's mass/energy tolerance.

The next source-only review should use these original phase-specific values to annotate which *phase chemistry* risks appear at the historical anchor (not whether they are physically valid) and identify independent experimental/cation-site stability criteria required for an explicitly authorized, small future Earth-only S3-D5 run.

Governance: D-024=ACTIVE, physical_T1=null, mechanical_solve_authorized=false, WORLD_HISTORY_PRODUCTION_AUTHORIZED=false; S2 SEALED remains immutable.
