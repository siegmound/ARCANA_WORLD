from pathlib import Path
import hashlib
import json
import shutil

STAGE = "v0.6D1-R4.54-R3.1"
TARGET = Path("scripts/audit_v0_6D1_R4_54_R3_postrepair.py")
OUT = Path("outputs/v0_6D1_R4_54_R3_1")
PRE_SHA = "5af9d31088bac40497b3d95df313b186427b4177d0692d3543da036d54f5a111"
POST_SHA = "1b359cc4616e7960a9b4d240eb12d00a05f4947af6f267cfc8f03a35673915a7"

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main() -> int:
    root = Path.cwd()
    target = root / TARGET
    if not target.exists():
        raise RuntimeError("R454_R3_1_TARGET_AUDIT_SCRIPT_MISSING")

    current = sha(target)
    preserve = root / OUT / "PREPATCH_SOURCE"
    preserve.mkdir(parents=True, exist_ok=True)

    if current == PRE_SHA:
        q = preserve / TARGET.name
        if not q.exists():
            shutil.copy2(target, q)

        s = target.read_text(encoding="utf-8")
        if "out={{\n" not in s:
            raise RuntimeError("R454_R3_1_OPEN_BRACE_ANCHOR_MISSING")
        if "\n}}\np=root/" not in s:
            raise RuntimeError("R454_R3_1_CLOSE_BRACE_ANCHOR_MISSING")
        s = s.replace("out={{\n", "out={\n", 1)
        s = s.replace("\n}}\np=root/", "\n}\np=root/", 1)
        target.write_text(s, encoding="utf-8", newline="\n")
    elif current == POST_SHA:
        pass
    else:
        raise RuntimeError(
            f"R454_R3_1_SOURCE_HASH_NOT_AUTHORIZED: {current} "
            f"expected pre={PRE_SHA} or post={POST_SHA}"
        )

    actual = sha(target)
    if actual != POST_SHA:
        raise RuntimeError(
            f"R454_R3_1_POSTPATCH_HASH_MISMATCH: {actual} != {POST_SHA}"
        )

    result = {
        "stage": STAGE,
        "status": "PASS_R454_R3_1_POSTREPAIR_AUDIT_LITERAL_BRACE_REPAIR_APPLIED",
        "prepatch_audit_sha256": PRE_SHA,
        "postpatch_audit_sha256": POST_SHA,
        "root_cause": "PYTHON_TEMPLATE_EMITTED_DOUBLE_LITERAL_BRACES_AROUND_OUT_DICT",
        "repair": "ONLY_POSTREPAIR_AUDIT_LITERAL_BRACES_CORRECTED",
        "r454_scientific_or_runtime_evidence_modified": False,
        "r454_rerun_performed": False,
        "historical_scientific_execution_performed": False,
        "canonical_state_changed": False,
        "gate_weakening_performed": False
    }
    (root / OUT).mkdir(parents=True, exist_ok=True)
    (root / OUT / "R4_54_R3_1_REPAIR_APPLICATION.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
