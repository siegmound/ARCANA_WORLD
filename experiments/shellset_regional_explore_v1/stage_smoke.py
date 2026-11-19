"""Stage one engineering-only run from the sealed regional PRE case."""
import argparse
import json
import math
from pathlib import Path
import shutil

from build_case import ROOT, sha

REGION = ROOT.parent / "ARCANA_WORLD_EVIDENCE/R6/SHELLSET_REGIONAL_CASE_20261118_01"
VENDOR = ROOT / "external/ShellSet-v1.1.0"
CAPTURE = """! Engineering-only output capture from existing solver arrays
       OPEN(UNIT=71,FILE='native_fields.txt',STATUS='NEW')
       WRITE(71,*) numNod,numEl,nCond,SHELLSconv
       DO n=1,numNod
         WRITE(71,'(I5,2ES26.17E3,I5)') n,v(:,n),whichP(n)
       END DO
       DO n=1,numEl
         DO j=1,7
           WRITE(71,'(2I5,6ES26.17E3)') n,j,eRate(:,j,n),tauMat(:,j,n)
         END DO
       END DO
       DO n=1,nCond
         WRITE(71,*) nodCon(n),iCond(n),vBCArg(n),vBCMag(n)
       END DO
       CLOSE(71)
"""


def stage(output):
    manifest = json.loads((REGION / "MANIFEST.json").read_text())
    for name in ("CASE.json", "regional.feg", "regional_PRE.dat", "MOD_ArcanaRuntime.regional.f90"):
        if sha(REGION/name) != manifest["files"][name]:
            raise ValueError(f"Wrong regional input bytes: {name}")
    case = json.loads((REGION/"CASE.json").read_text())
    output.mkdir()
    for name in ("CASE.json", "regional.feg", "regional_PRE.dat"):
        shutil.copyfile(REGION/name, output/name)
    shutil.copyfile(REGION/"MOD_ArcanaRuntime.regional.f90", output/"MOD_ArcanaRuntime.f90")
    for name in ("MOD_SharedVars.f90", "MOD_ShellSet.f90", "DMods.f90", "MOD_Shells.f90"):
        shutil.copyfile(VENDOR/"src"/name, output/name)
    original = (VENDOR/"src/SHELLS_v5.0.f90").read_text()
    marker = "!   Test and display the equilibrium found:"
    if original.count(marker) != 1:
        raise ValueError("Ambiguous SHELLS capture site")
    (output/"SHELLS_v5.0.f90").write_text(original.replace(marker, CAPTURE+"\n"+marker))
    shutil.copyfile(Path(__file__).with_name("smoke_driver.f90"), output/"smoke_driver.f90")
    parameters = (VENDOR/"INPUT/iEarth5-049.in").read_text().splitlines()
    parameters[0] = "ENGINEERING_ONLY: inherited Earth5-049 numerical reference"
    assert parameters[13].startswith("0,1.00") and parameters[14].startswith("0.0")
    (output/"engineering.in").write_text("\n".join(parameters)+"\n")
    # Manufactured eastward extension of 2e-9 m/s across the cut,
    # superposed on the Euler field. All perimeter DOFs have Dirichlet data.
    low = min(row["canonical_lat_lon_deg"][1] for row in case["nodes"])
    high = max(row["canonical_lat_lon_deg"][1] for row in case["nodes"])
    table = ["ENGINEERING_ONLY Euler plus manufactured extension"]
    prescribed = {}
    for index, node in enumerate(case["perimeter_local_ids"], 1):
        row = case["nodes"][node-1]
        south, east = row["candidate_euler_south_east_m_s"]
        east += 2e-9 * (row["canonical_lat_lon_deg"][1] - low)/(high-low)
        prescribed[node] = [south,east]
        magnitude = math.hypot(south,east)
        azimuth = math.degrees(math.atan2(east,-south)) % 360
        table.append(f"{index} {node} 2 {magnitude:.17e} {azimuth:.17e}")
    (output/"engineering.bcs").write_text("\n".join(table)+"\n")
    (output/"PRESCRIBED.json").write_text(json.dumps(prescribed,indent=2)+"\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    stage(parser.parse_args().output)
