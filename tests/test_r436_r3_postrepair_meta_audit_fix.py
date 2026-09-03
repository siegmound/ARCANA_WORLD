from pathlib import Path
import ast
import hashlib

P=Path("tools/r4_36_r2_postrepair_reseal_audit.py")


def test_corrected_postrepair_helper_compiles():
    src=P.read_text(encoding="utf-8")
    compile(src,str(P),"exec")


def test_checks_and_out_are_dict_literals_not_sets():
    tree=ast.parse(P.read_text(encoding="utf-8"))
    assigns={n.targets[0].id:n.value for n in tree.body
             if isinstance(n,ast.Assign)
             and len(n.targets)==1
             and isinstance(n.targets[0],ast.Name)
             and n.targets[0].id in {"checks","out"}}
    assert isinstance(assigns["checks"],ast.Dict)
    assert isinstance(assigns["out"],ast.Dict)


def test_no_double_literal_open_braces_remain_at_bug_sites():
    s=P.read_text(encoding="utf-8")
    assert "checks={{" not in s
    assert "out={{" not in s


def test_helper_is_meta_audit_only():
    s=P.read_text(encoding="utf-8")
    forbidden=[
        "import geonomics",
        "gnx.make_model",
        ".walk(",
        ".run(",
        "run_default_model(",
        "np.save(",
    ]
    for token in forbidden:
        assert token not in s


def test_helper_reads_existing_r436_outputs():
    s=P.read_text(encoding="utf-8")
    assert "R4_36_INTEGRATED_AUDIT.json" in s
    assert "R4_36_FINAL_SEAL_AUDIT.json" in s
    assert "R4_36_GEONOMICS_NATIVE_PARAMETER_AND_MODEL_CONSTRUCTION_PREFLIGHT.json" in s
    assert "R4_36_EXACT_STATE_INJECTION_AND_CANONICAL_PAYLOAD_PREFLIGHT.json" in s
