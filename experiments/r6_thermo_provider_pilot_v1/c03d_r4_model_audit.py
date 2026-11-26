"""Source-bound diagnostic model audit and native stdout readback, no phase qualification."""
from __future__ import annotations
import re
from experiments.r6_thermo_provider_pilot_v1.c03d_r3_composition_audit import active_text


def model_audit(blocks):
    if len(blocks)!=18 or any(v is None for v in blocks.values()):
        raise ValueError("C03D_R4_MODEL_BLOCKS")
    flags={}
    for name,block in blocks.items():
        active=active_text(block["text"]).splitlines()
        flags[name]={"site_check_override":"site_check_override" in active,
                     "normalized_text_sha256":block["normalized_text_sha256"]}
    legacy=sorted(k for k,v in flags.items() if v["site_check_override"])
    if legacy!=["GlTrTsPg"]:
        raise ValueError("C03D_R4_SITE_CHECK_OVERRIDE_DRIFT")
    return {"models":flags,"allowed_diagnostic_warning_models":legacy,
            "source_condition":"not stck and not refine and iam < 3",
            "scientific_acceptance":False,"replacement_authorized":False}


def native_model_details(raw,roster,records=None):
    """Capture warning 114 continuations and generated counts, not phase admission.
    Unknown tokens/blocks are retained as unresolved rather than silently dropped.
    """
    text=raw.decode("utf-8",errors="replace") if isinstance(raw,bytes) else raw
    lines=text.splitlines()
    missing=[]
    counts=[]
    records=records or {}
    for i,line in enumerate(lines):
        hit=re.match(r"^\s*\*\*warning ver114\*\* the following endmembers are missing for\s+(.+?):\s*$",line)
        if hit:
            model=hit[1].strip()
            j=i+1
            while j<len(lines) and not lines[j].strip():
                j+=1
            body=[]
            while j<len(lines) and lines[j].strip() and re.fullmatch(r"\s*[A-Za-z0-9_+().-]+(?:\s+[A-Za-z0-9_+().-]+)*\s*",lines[j]):
                body.extend(lines[j].split())
                j+=1
            detail=[]
            for name in body:
                record=records.get(name)
                outside=record.get("outside_active_components",[]) if record else []
                detail.append({"endmember":name,
                    "source_classification":("DIRECT_RECORD_REQUIRES_INACTIVE_COMPONENT" if outside else
                        "DIRECT_RECORD_PRESENT_NATIVE_CAUSE_UNRESOLVED" if record else
                        "NO_DIRECT_EOS_RECORD_MAKE_OR_OTHER_CAUSE_UNRESOLVED"),
                    "outside_active_components":outside})
            missing.append({"model":model,"requested_model":model in roster,
                            "endmembers":detail,"header_line":i+1,
                            "parsed_nonempty":bool(body)})
        hit=re.match(r"^\s*(\d+)\s+pseudocompounds generated for:\s*(\S+)\s*$",line)
        if hit:
            counts.append({"model":hit[2],"count":int(hit[1]),
                           "requested_model":hit[2] in roster,"line":i+1})
    total=re.findall(r"(?m)^\s*Total number of pseudocompounds:\s*(\d+)\s*$",text)
    return {"missing_endmember_reports":missing,"pseudocompound_reports":counts,
            "native_total_pseudocompounds_reports":[int(x) for x in total],
            "full_native_pruning_verified":False,"scientific_acceptance":False}
