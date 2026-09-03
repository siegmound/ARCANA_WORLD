from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import json
import sys
import tempfile
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from arcana_worldsim.scientific_engines import (  # noqa:E402
    ENGINE_REGISTRY, NEMO_242, ScientificExperiment, Nemo242Adapter, Nemo242MappingSpec,
    deny_direct_canonical_write, CanonicalWriteDenied,
)

EXPECTED_PARENT_HASHES = {
    "src/rebased_natural_control_runtime_v0_6D1_R3_4.py": "087d05f532d84f53f8c99d08ae0099657792526eb3aa97bab7cb9e64cb342e45",
    "src/rebased_natural_control_runtime_v0_6D1_R3_5.py": "634237eb15383000e88180b890ead9b6facc281c0a77eb5ce00efe32f3d0bc95",
    "src/d3_additive_variance_v0_6_3D3_3A.py": "3b235b186e234f66a77443bec3a46c80ef699ecd715737be7d36103db01b4c21",
    "src/rebased_deep_time_barrier_provider_v0_6D1_R3.py": "1eace956da7254be21e5513a5c75f2efc360b80410f4c72dafedef01f584ce0c",
    "src/d3_paleogeographic_history_v0_6_3D3_2C.py": "5831f41ba9cd7bc05be0cd25f8cd84e895c6c9fa453bde7634d7b27c82394730",
}


def digest(p: Path) -> str:
    return sha256(p.read_bytes()).hexdigest()


def main() -> int:
    checks=[]
    def ck(name, ok, detail=""):
        checks.append({"check":name,"pass":bool(ok),"detail":str(detail)})

    cfg=json.loads((ROOT/"configs/world1_scientific_engine_bridge_v0_6D1_R3_6A.json").read_text())
    ck("stage_id", cfg["stage"]=="v0.6D1-R3.6A")
    ck("parent_r35", cfg["parent_stage"]=="v0.6D1-R3.5")
    ck("canonical_owner_arcana", cfg["canonical_state_owner"]=="ARCANA_WorldSim")
    ck("external_direct_write_false", cfg["external_engine_direct_canonical_write"] is False)
    ck("auto_promotion_false", cfg["automatic_promotion_from_external_evidence"] is False)
    ck("all_five_engines_registered", set(ENGINE_REGISTRY)=={"NEMO","Madingley","Geonomics","CDMetaPOP","RangeShifter"})
    ck("all_external_writes_denied", all(not d.canonical_write_allowed for d in ENGINE_REGISTRY.values()))
    ck("nemo_version_pinned_242", NEMO_242.version=="2.4.2")
    ck("geonomics_version_pinned_149", ENGINE_REGISTRY["Geonomics"].version=="1.4.9")
    ck("cdmetapop_reference_308", ENGINE_REGISTRY["CDMetaPOP"].version=="3.08-reference")
    ck("rangeshifter_reference_30", ENGINE_REGISTRY["RangeShifter"].version=="3.0-reference")

    for rel, expected in EXPECTED_PARENT_HASHES.items():
        got=digest(ROOT/rel)
        ck(f"parent_authority_unchanged::{rel}", got==expected, got)

    try:
        deny_direct_canonical_write()
        denied=False
    except CanonicalWriteDenied:
        denied=True
    ck("direct_write_api_denies", denied)

    arr=np.array([1.0,2.0])
    exp=ScientificExperiment(experiment_id="audit",arcana_stage="v0.6D1-R3.5",age_ma=191.0,engine=NEMO_242,
        source_state_sha256="a"*64,random_seed=1,arrays={
            "component_ids":np.array(["D0","D1"]),"component_species":np.array(["S","S"]),
            "population_total":np.array([10.,8.]),"trait_mean":np.zeros((2,3)),"additive_variance":np.full((2,3),0.02),
            "generation_time_years":np.array([5.,5.]),"exchange_matrix":np.array([[0.,0.1],[0.1,0.]]),"immutability_probe":arr})
    arr[0]=99
    ck("export_copy_isolated", exp.arrays["immutability_probe"][0]==1.0)
    ck("export_read_only", exp.arrays["immutability_probe"].flags.writeable is False)
    ck("semantic_hash_sha256", len(exp.semantic_sha256)==64)

    with tempfile.TemporaryDirectory() as td:
        adapter=Nemo242Adapter(Nemo242MappingSpec(population_units_to_individuals=10.0,carrying_capacity_multiplier=1.5))
        ev=adapter.run(exp,td)
        ck("nemo_preparation_status", ev.status=="PREPARED_REFERENCE_INPUTS")
        ck("nemo_does_not_execute_without_validated_template", ev.metrics["execution_attempted"] is False)
        ck("nemo_bridge_files_present", all((Path(td)/x).exists() for x in ["arcana_patches.tsv","arcana_quantitative_traits.tsv","arcana_exchange_matrix.tsv","arcana_nemo_bridge.json","NEMO_TEMPLATE_REQUIRED.txt"]))
        ck("evidence_hash_sha256", len(ev.semantic_sha256)==64)

    required=[
        "SCIENTIFIC_ENGINE_INTEGRATION_CONTRACT_v0_6D1_R3_6A.md",
        "EXTERNAL_SCIENTIFIC_ENGINE_REUSE_AUDIT_v0_6D1_R3_6A.md",
        "V0_6D1_R3_6A_STATUS.md","NEXT_STAGE_HANDOFF_v0_6D1_R3_6A.md",
        "scripts/prepare_nemo_reference_v0_6D1_R3_6A.py",
        "tests/test_scientific_engine_bridge_v0_6D1_R3_6A.py",
    ]
    for rel in required: ck(f"required_file::{rel}",(ROOT/rel).exists())

    passed=sum(int(x["pass"]) for x in checks)
    out={"stage":"v0.6D1-R3.6A","status":"PASS" if passed==len(checks) else "FAIL","passed":passed,"total":len(checks),"checks":checks,
         "verdict":"PASS_GOVERNED_SCIENTIFIC_ENGINE_BRIDGE_FOUNDATION__R3_6B_NEMO_REFERENCE_PENDING" if passed==len(checks) else "FAIL"}
    print(json.dumps(out,indent=2))
    return 0 if passed==len(checks) else 1

if __name__=="__main__": raise SystemExit(main())
