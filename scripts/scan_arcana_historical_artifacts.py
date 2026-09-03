#!/usr/bin/env python3
"""ARCANA v0.6D1-R0 local historical artifact recovery scanner.

Searches directories for exact historical package hashes and RAW artifact names.
It does NOT reconstruct simulation state and never promotes name-only matches to authority.
"""
from __future__ import annotations
import argparse, hashlib, json, os, sys, zipfile
from pathlib import Path
from typing import Iterable

EXPECTED_PACKAGES = {
    "v0.6.3D1": "75a8bd4e90103e20ff308ef052871289eb3a608a558288abf1622c36a3b7fb1c",
    "v0.6.3D2.T": "3b236d3a0a3a048b300d1fcd818006bedc93130c6a17abf9378635f0b6d76aa8",
    "v0.6.3D2.1": "e751668c7a8232cf67b791b93312ad89050d8a7b2fd8cd4f9da4422fc0bc8828",
    "v0.6.3D2.1.1": "918b5693efb0db81628efaba3f7f63b6365c1f975aba36d123401c2aede52905",
    "v0.6.3D2.2": "42f6c506dcb81ed06549713bdf6f2313aa51bd2cb55fe17571fce493923394a8",
}

RAW_TARGETS = {
    "arcana_rawfirst.sqlite": "D2.T population/event query store",
    "physical_reference_cube.nc": "D2.T physical reference cube",
    "cha1_highres_state.npz": "D2.2 full high-resolution state",
    "species_population_timeseries.csv": "D2.2 species population timeseries",
    "physical_foodweb_timeseries.csv": "D2.2 physical/food-web timeseries",
    "extinction_events.json": "D2.2 extinction event ledger",
    "CHA1_survivor_registry.json": "D2.2 survivor registry",
    "species_diagnostics.json": "D2.2 species diagnostics",
    "recovery_milestones.json": "D2.2 recovery milestones",
    "solver_diagnostics.json": "D2.2 solver diagnostics",
    "reptiloid_survivor_E_M.json": "D2.2 derived reptiloid diagnostic",
    "cha1_spatial_survivor_footprint_66Ma.npz": "D2.2 survivor spatial footprint",
    "cha1_highres_audit.json": "D2.2 audit",
    "cha1_highres_manifest.json": "D2.2 manifest",
}

SUPPORT_TARGETS = {
    "species_metadata.json": "D1 metadata surface",
    "post_cha1_spatial_bridge_state.npz": "D3.0A 31->115 spatial bridge state",
    "spatial_bridge_diagnostics.json": "D3.0A bridge diagnostics",
}

def sha256(path: Path, chunk: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()

def iter_files(roots: Iterable[Path]):
    seen = set()
    for root in roots:
        root = root.resolve()
        if root.is_file():
            if root not in seen:
                seen.add(root); yield root
            continue
        if not root.exists():
            continue
        for dp, dns, fns in os.walk(root):
            # skip common heavy/noisy generated dirs
            dns[:] = [d for d in dns if d not in {".git", ".venv", "__pycache__", ".pytest_cache"}]
            for fn in fns:
                p = (Path(dp) / fn).resolve()
                if p not in seen:
                    seen.add(p); yield p

def zip_members(path: Path):
    try:
        with zipfile.ZipFile(path) as z:
            return z.namelist()
    except (zipfile.BadZipFile, OSError):
        return []

def classify_package_hash(digest: str):
    return [k for k,v in EXPECTED_PACKAGES.items() if v == digest]

def scan(roots: list[Path], hash_all_zips: bool = True):
    package_hits=[]; raw_hits=[]; support_hits=[]; zip_member_hits=[]; errors=[]
    exact_raw_names=set(RAW_TARGETS); support_names=set(SUPPORT_TARGETS)
    for p in iter_files(roots):
        name=p.name
        low=name.lower()
        if low.endswith(".zip"):
            digest=None
            if hash_all_zips:
                try: digest=sha256(p)
                except OSError as e:
                    errors.append({"path":str(p),"error":str(e)}); continue
                stages=classify_package_hash(digest)
                if stages:
                    for stage in stages:
                        package_hits.append({"stage":stage,"status":"FOUND_HASH_EXACT","path":str(p),"sha256":digest,"bytes":p.stat().st_size})
            members=zip_members(p)
            for member in members:
                base=Path(member).name
                if base in exact_raw_names or base in support_names:
                    zip_member_hits.append({"zip":str(p),"member":member,"kind":"RAW" if base in exact_raw_names else "SUPPORT","target":base})
        if name in exact_raw_names:
            raw_hits.append({"target":name,"status":"FOUND_FILE","path":str(p),"bytes":p.stat().st_size})
        if name in support_names:
            support_hits.append({"target":name,"status":"FOUND_FILE","path":str(p),"bytes":p.stat().st_size})

    found_stages={x['stage'] for x in package_hits}
    packages=[{"stage":s,"expected_sha256":h,"status":"FOUND_HASH_EXACT" if s in found_stages else "NOT_FOUND_HASH_EXACT","matches":[x for x in package_hits if x['stage']==s]} for s,h in EXPECTED_PACKAGES.items()]
    def target_summary(targets, direct, zhits, kind):
        out=[]
        for t,desc in targets.items():
            ds=[x for x in direct if x['target']==t]
            zs=[x for x in zhits if x['target']==t and x['kind']==kind]
            status="FOUND_FILE" if ds else ("FOUND_IN_ZIP" if zs else "NOT_FOUND")
            out.append({"target":t,"description":desc,"status":status,"direct_matches":ds,"zip_matches":zs})
        return out
    report={
      "schema":"ARCANA_HISTORICAL_ARTIFACT_RECOVERY_SCAN_v0_6D1_R0",
      "roots":[str(r.resolve()) for r in roots],
      "authority_rule":"Only FOUND_HASH_EXACT historical packages can restore executable authority. RAW name hits are evidence/data, not executable parity authority.",
      "packages":packages,
      "raw_targets":target_summary(RAW_TARGETS,raw_hits,zip_member_hits,"RAW"),
      "support_targets":target_summary(SUPPORT_TARGETS,support_hits,zip_member_hits,"SUPPORT"),
      "errors":errors,
    }
    min_parent = all(next((x for x in packages if x['stage']==s), {"status":"NOT_FOUND_HASH_EXACT"})['status']=="FOUND_HASH_EXACT" for s in ("v0.6.3D1","v0.6.3D2.2"))
    report["summary"]={
      "exact_packages_found":sum(x['status']=="FOUND_HASH_EXACT" for x in packages),
      "raw_targets_found":sum(x['status']!="NOT_FOUND" for x in report['raw_targets']),
      "support_targets_found":sum(x['status']!="NOT_FOUND" for x in report['support_targets']),
      "minimum_exact_parent_set_found": min_parent,
      "production_historical_hx_authorized": False,
      "authorization_note": "R0 never authorizes production HX by itself. The original pre-CHA1 D2 executable/runtime authority must also be bound and Deep-OFF parity must pass."
    }
    return report

def main(argv=None):
    ap=argparse.ArgumentParser()
    ap.add_argument("roots", nargs="+", help="Directories/files to scan recursively")
    ap.add_argument("--output", "-o", help="Write JSON report here")
    args=ap.parse_args(argv)
    report=scan([Path(x) for x in args.roots])
    txt=json.dumps(report,indent=2,sort_keys=True)
    if args.output:
        out=Path(args.output); out.parent.mkdir(parents=True,exist_ok=True); out.write_text(txt+"\n",encoding="utf-8")
    print(txt)
    return 0
if __name__=="__main__": raise SystemExit(main())
