# ARCANA R6 — S3-D4-C: S2 phase-specific chemistry readback and Fsp(C1) source criterion

**Data:** 2026-11-24. **Decisione:** `S3_D4_C_S2_OPERATOR_PHASE_READBACK_PASS__FSP_C1_SOURCE_HEURISTIC_FLAG__PHYSICAL_VALIDITY_UNKNOWN`.

## Evidence provenance and limits

FAIR user-operated isolated S3 worktree, source exact `fbb1e77c54e3545ea2e7e7b52226ed0576f1993e`, operator output `S3_D4_C_ORIGINAL_S2_PHASE_CHEMISTRY_READONLY_PASS` and `S3_D4_C_PHASE_AUDIT_EXIT=0`. Original immutable S2 REAL MANIFEST SHA256 `74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604`, SHA-guarded original two member paths `MAGEMIN_01/NATIVE.toml` and `PERPLEX_01/BL691_MEEMUM/bl691_MEEMUM.prn`. These are *operator-reported* read-only tests; the GitHub author has not independently read/rehash original FAIR bytes. Full data transcribed in `experiments/r6_thermo_provider_pilot_v1/s3_d4_c_s2_original_phase_chemistry_receipt_v1.json`; it is an operator transcript-derived report **not** a replacement for raw S2 source.

## MAGEMin original Earth demonstrator (10kbar / 1100°C)

- `liq` **0.7313343478373275** mass fraction (73.1334%).
- `cpx` **0.2489167968690463** (24.8917%).
- `opx` **0.019748855293626123** (1.9749%).

Native `phase_comp_wt` contains 11 components, including native `O` produced by source original Fe2O3→2FeO+O basis. This is a melt-dominated *computational reference point*, not proof the G25 `ig/tc_ds636` P/T-X model is calibrated for that source demonstrator. Do not compare its phase assemblage directly to BL691; the P/T, database, chemistry and redox bases are different.

## Perple_X original BL691 (4000bar / 1050K)

| Phase | Original printed mass % | Source-validated relevant observation |
|---|---:|---|
| `cAmph(G)` | 50.80 | TiO2 0.14105, O2 0.12131 and FeO 2.47675 in printed molar oxide components; these are **not direct Fe3+ site fractions** |
| `Fsp(C1)` | 31.05 | printed Na2O 0.22451, CaO 0.54275, K2O 0.00412; structural state issue below |
| `q` | 11.90 | quartz, SiO2 1.00000 |
| `Augite(G)` | 3.09 | printed Na2O 0.01463 and CaO 0.88092; cannot determine model's "Na-rich" applicability from a bulk threshold |
| `Ilm(WPH)` | 2.34 | TiO2 0.90342 |
| `melt(G)` | 0.82 | distinct from MAGEMin G25 liquid model |

`Fsp(C1)`, `Augite(G)`, `cAmph(G)` together account for **84.94%** of the reported mass, but this **does not** imply that 84.94% of the phase result is inaccurate. It indicates that warnings on these models are relevant to non-negligible phase mass.

## Exact Fsp(C1) source-heuristic review

Original upstream pinned model: `jadconnolly/Perple_X@950d882bb6a9325a627109aa7154f7b526aa3087`, `test/bl691_MEEMUM/solution_model.dat` Git blob `564742a569998a768c2d8e15d2b9599ee90438d1`. Official source link https://github.com/jadconnolly/Perple_X/blob/950d882bb6a9325a627109aa7154f7b526aa3087/test/bl691_MEEMUM/solution_model.dat .

The file contains an explicit caution that **I1/C1 do not automatically determine the stable feldspar structure**, followed by the assumed guideline `X(Ab) > 1 - (0.12 + 0.00038*T_K)` for choosing C1; it also describes the C1 branch as Ab-rich in the Ab–An join (with caveats about ternary and solvus interactions). `Fsp(C1)` is selected in the original BL691 source `.dat`. It uses endmember `an`, `san`, `abh`, with `z(Ca)=1 an`, `z(K)=1 san`, `z(Na)=1 abh`.

**From original printed native oxide molar coefficients:** Na cations `2×0.22451=0.44902`, Ca `0.54275`, K `2×0.00412=0.00824`; site sum `1.00001` (printing), giving:

- `X(Ab) = 0.44901551`
- `X(An) = 0.54274457`
- `X(Or) = 0.00823992`
- Upstream heuristic at `T_K=1050`: `1 - (0.12 + 0.00038×1050) = 0.481`
- Gap `X(Ab)-threshold = -0.03198449` (≈**−3.20 percentage points**).
- Simple printed-decimal half-ULP intervals bound the calculated XAb approximately `[0.44900326, 0.44902775]`, still below 0.481.
- Additional stoichiometry sanity: `SiO2 + 2×Al2O3 = 2.45725 + 1.54276 = 4.00001`, consistent with the feldspar tetrahedral cation count within decimal printing.

**Conclusion:** For this specific original 1050 K source-computed feldspar, the published *source-file selection heuristic* for C1 is **not met** when applied to the reported phase composition. This is a **documented phase-model selection conflict requiring scientific adjudication**, not evidence that S2 execution failed, not definitive phase stability proof, and **not** blanket scientific rejection of the 25 BL691 P/T-X candidates. The source warns its ternary phase behavior is more complex than a one-number threshold. Because the feldspar phase mass is 31.05%, the issue is not merely an accessory trace.

## Other model warnings

- `Augite(G)`: original phase sodium proxy `2Na2O/(2Na2O+CaO) = 0.03214749` (3.215%), but this is only a simple projected alkali-earth mix ratio and **not** validated octahedral site occupancy or a source-approved "Na-rich" cutoff. Limit remains UNKNOWN.
- `cAmph(G)`: non-zero TiO2, FeO and O2 component tokens establish the species are represented, but not which full-model omitted exchanges would affect this phase's real Fe3+/Ti assemblage. Limit remains UNKNOWN.
- MAGEMin G25: 73.13% liquid under original demonstration P/T; separate from Perple_X G16 0.82% liquid at a different P/T/chemistry, **not a cross-provider disagreement experiment**.

## Next narrowly scoped check — 5 original Perple_X PRN files, no engine

The old 5/5 Perple_X **stdout** logs were byte-identical, but that is not proof that the five original PRN member files (and Fsp C1 composition) have exactly the same bytes. Before deciding whether this conflict reflects one anomalous native file or consistent original solver output, independently SHA-check and inspect all five immutable PRN files. This preserves the scientific risk flag, does not run thermodynamics, and does not change S2:

```bash
(
set -euo pipefail
cd /home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_R6_THERMO_S3_DESIGN_VERIFY
test "$(git rev-parse HEAD)" = "fbb1e77c54e3545ea2e7e7b52226ed0576f1993e"
source /home/jlpfritas/miniforge3/etc/profile.d/conda.sh
conda activate arcana-r6-linux
export PYTHONPATH="$PWD/src:$PWD"
export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1
python - <<'PY'
from decimal import Decimal
from pathlib import Path
import hashlib, json, re
from experiments.r6_thermo_provider_pilot_v1.s3_native_readback import read_perplex_prn

root=Path("/home/jlpfritas/HPC-POMDP/Arcana/ARCANA_WORLD_EVIDENCE/R6/R6_THERMO_S2_REPEATABILITY_NEW01")
expected="74871bd46fdb67a2828566a12e11140e52a505e828ded81751b239bf20b5b604"
sha=lambda b:hashlib.sha256(b).hexdigest()
manifest_raw=(root/"MANIFEST.json").read_bytes()
assert sha(manifest_raw)==expected
manifest=json.loads(manifest_raw)
last=None
hashes=[]
for i in range(1,6):
    rel=f"PERPLEX_{i:02d}/BL691_MEEMUM/bl691_MEEMUM.prn"
    p=root/rel
    assert p.is_file() and not p.is_symlink() and p.resolve().is_relative_to(root.resolve())
    raw=p.read_bytes()
    assert sha(raw)==manifest["files_sha256"][rel]
    hashes.append(sha(raw))
    prn=raw.decode("utf-8",errors="replace")
    parsed=read_perplex_prn(prn,4000,1050)
    assert len(parsed["phases"])==6 and "Fsp(C1)" in parsed["phases"]
    body=prn.split("Phase Compositions (molar  proportions):",1)[1].split("Phase speciation",1)[0]
    rows=[s.strip() for s in body.splitlines() if s.strip()]
    cols=re.split(r"\s{2,}",rows[0])[4:]
    assert set(cols)=={"Na2O","MgO","Al2O3","K2O","CaO","TiO2","FeO","O2","H2O","SiO2"}
    fsp=[r.split() for r in rows[1:] if r.split()[0]=="Fsp(C1)"]
    assert len(fsp)==1 and len(fsp[0])==15
    x=dict(zip(cols,fsp[0][5:],strict=True))
    Na=2*Decimal(x["Na2O"])
    Ca=Decimal(x["CaO"])
    K=2*Decimal(x["K2O"])
    S=Na+Ca+K
    assert S>0
    Ab,An,Or=Na/S,Ca/S,K/S
    cut=Decimal(1)-(Decimal("0.12")+Decimal("0.00038")*Decimal(1050))
    flag=Ab<cut
    print(f"RUN={i} PRN_SHA256={hashes[-1]} FSP_WT_PCT={fsp[0][1]} X_AB={Ab:.8f} X_AN={An:.8f} X_OR={Or:.8f} C1_CUTOFF={cut} HEURISTIC_NOT_MET={flag}")
    current=(x["Na2O"],x["CaO"],x["K2O"],fsp[0][1],tuple(sorted(parsed["phases"])))
    if last is None:
        last=current
    else:
        assert current==last, "S2_5_PROCESS_FSP_COMPOSITION_OR_PHASE_SET_DRIFT_REQUIRES_REVIEW"
    assert flag, "S2_C1_HEURISTIC_FLAG_NOT_REPRODUCED"
print("PRN_FULL_BYTE_IDENTICAL_5_OF_5=", len(set(hashes))==1)
print("S3_D4_C_FIVE_PROCESS_FSP_BRANCH_READONLY_PASS")
print("S3_ENGINE_RUNS=0")
PY
)
S3_EXIT=$?
echo "S3_D4_C_FIVE_PROCESS_EXIT=$S3_EXIT"
```

The `HEURISTIC_NOT_MET` boolean is not a numerical-error pass/fail gate: it is a source-rule annotation. If the 5 original anchored PRN phase assemblies differ, keep the evidence and investigate; do not rewrite them or interpret source gaps as zero. No physical model data promoted.

## Roadmap after review

S3-D4-C: original readback PASS, structural-state flag identified; five-native-file S2 repeat-check pending. Next independently source/calibrate structural feldspar I1/C1 branch and phase-composition dependence, Augite Na-rich boundary, cAmph Fe3/Ti, G25 melt/phase X. S3-D4-D: software 122/122 FAIR PASS; numerical repeatability acceptance and per-point resource budget not ratified. S3-D5: tiny noncanonical Earth-only pilot **requires separate authorization**, fresh source/snapshot identity, evidence write-once and safe caps; 25+25 grids blocked. D-024 permits separate geodynamic regional T0→T1 work with qualified upstream physics, but no current physical T1 or World History production.

`D-024=ACTIVE`, `physical_T1=null`, `mechanical_solve_authorized=false`, `WORLD_HISTORY_PRODUCTION_AUTHORIZED=false`.
