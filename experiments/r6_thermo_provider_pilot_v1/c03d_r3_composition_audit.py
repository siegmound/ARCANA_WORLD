"""C03D-R3 limited direct EoS composition audit, not a native phase parser."""
from __future__ import annotations

from decimal import Decimal
import re

HEADER = re.compile(r"^(\S+)\s+EoS\s*=\s*(\d+)\b")
TERM = re.compile(r"([A-Z0-9]+)\(([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?)\)")


def active_text(text):
    return "\n".join(line.split("|", 1)[0].strip() for line in text.splitlines())


def inventory(raw, components, active):
    """All uncommented direct EoS headers; skip blank/comment-only lines.

    Decimal sums describe source coefficients, not runtime floating-point
    operations, transformed compositions, or generated make entities.
    """
    lines = active_text(raw.decode("utf-8")).splitlines()
    records = {}
    for i, line in enumerate(lines):
        header = HEADER.match(line)
        if not header:
            continue
        name = header[1]
        if name in records:
            raise ValueError("C03D_R3_DUPLICATE_EOS:" + name)
        composition = next((x for x in lines[i+1:] if x), "")
        compact = "".join(composition.split())
        terms = list(TERM.finditer(compact))
        if not terms or "".join(x[0] for x in terms) != compact:
            raise ValueError("C03D_R3_UNPARSED_COMPOSITION:" + name)
        coeff = {}
        for match in terms:
            key, value = match.groups()
            if key not in components or key in coeff:
                raise ValueError("C03D_R3_COMPONENT:" + name + ":" + key)
            coeff[key] = Decimal(value)
        outside = sorted(k for k, v in coeff.items() if v != 0 and k not in active)
        total = sum(coeff.values(), Decimal(0))
        records[name] = {"line": i+1, "eos": int(header[2]),
                         "coefficients": {k: str(v) for k, v in coeff.items()},
                         "total": str(total), "outside_active_components": outside,
                         "nonpositive": total <= 0}
    return records


def audit(hp, components, active, model_blocks, pure_names):
    records = inventory(hp, components, active)
    compatible = {k: v for k, v in records.items() if not v["outside_active_components"]}
    nonpositive = sorted(k for k, v in compatible.items() if v["nonpositive"])
    # Exact observed source condition, not a general permission for ver013.
    si = records.get("Si(s)", {})
    if (len(records) != 198 or len(compatible) != 158 or nonpositive != ["Si(s)"]
            or si.get("eos") != 2 or si.get("coefficients") != {"SIO2": "1", "O2": "-1"}):
        raise ValueError("C03D_R3_PINNED_INVENTORY_DRIFT")
    if len(model_blocks) != 18 or any(v is None for v in model_blocks.values()):
        raise ValueError("C03D_R3_MODEL_BLOCKS")
    makes = active_text(hp.decode("utf-8")).split("\nbegin_makes\n", 1)[1].split("\nend_makes\n", 1)[0]
    hits = [k for k, v in model_blocks.items() if "Si(s)" in active_text(v["text"])]
    if hits or "Si(s)" in makes or "Si(s)" in pure_names:
        raise ValueError("C03D_R3_SILICON_DEPENDENCY")
    return {"schema": "R6_C03D_R3_DIRECT_EOS_AUDIT_V1",
            "direct_eos_count": len(records), "active_basis_compatible_count": len(compatible),
            "nonpositive_compatible": nonpositive,
            "nonpositive_outside_basis": sorted(k for k, v in records.items()
                                               if v["nonpositive"] and v["outside_active_components"]),
            "records": records, "checked_requested_model_blocks": sorted(model_blocks),
            "silicon_active_make_or_model_reference": False,
            "allowed_diagnostic_warning_species": ["Si(s)"],
            "native_phase_admission_verified": False, "scientific_acceptance": False,
            "scope": "DIRECT_LITERAL_RECORDS_AND_REQUESTED_MODEL_TEXT_ONLY"}
