"""Deterministic reader/writer for ARCANA's source-established ShellSet FEG subset."""
from __future__ import annotations

import hashlib
import json
import math
import re

from .model import ElementRecord, FEGModel, FaultRecord, NodeRecord

_FLOAT = re.compile(r"^[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[EeDd][+-]?\d+)?$")
PRODUCTION_TITLE_MARKER = "ARCANA_R6_PRE_ORBDATA_RUNTIME_V1"


def _f(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("FEG records cannot contain nonfinite numbers")
    return format(float(value), ".17g")


def _validate(model: FEGModel) -> None:
    if model.mode not in {"PRE_ORBDATA", "SHELLS_READY"}:
        raise ValueError(f"unsupported FEG mode {model.mode}")
    ids = [n.node_id for n in model.nodes]
    if ids != list(range(1, len(ids) + 1)):
        raise ValueError("ARCANA FEG node IDs must be contiguous, unique, and one-based")
    element_ids = [e.element_id for e in model.elements]
    if element_ids != list(range(1, len(element_ids) + 1)):
        raise ValueError("ARCANA continuum element IDs must be contiguous and one-based")
    fault_ids = [f.fault_id for f in model.faults]
    if fault_ids != list(range(1, len(fault_ids) + 1)):
        raise ValueError("ARCANA fault IDs must be contiguous and one-based")
    known = set(ids)
    if model.mode == "SHELLS_READY" and any(
        None in (n.crustal_thickness_m, n.mantle_lithosphere_thickness_m,
                 n.chemical_density_anomaly_kg_m3, n.cooling_curvature_k_m2)
        for n in model.nodes
    ):
        raise ValueError("SHELLS_READY requires all nine source-defined nodal fields")
    if any(n not in known for e in model.elements for n in e.node_ids):
        raise ValueError("continuum element references an unknown node")
    if any(n not in known for f in model.faults for n in f.node_ids):
        raise ValueError("fault element references an unknown node")
    if any(len(set(e.node_ids)) != 3 for e in model.elements):
        raise ValueError("continuum triangle must reference three distinct node IDs")
    if model.n_fake_nodes != 0:
        raise ValueError("ARCANA subset rejects legacy fake-node numbering")
    if model.n1000 < 0:
        raise ValueError("FEG n1000 must be nonnegative")
    if model.title.startswith(PRODUCTION_TITLE_MARKER) and len(ids) > model.n1000:
        raise ValueError("production FEG requires n1000 >= nRealN")
    _brief_token(model.brief)
    if model.faults and model.mode not in {"PRE_ORBDATA", "SHELLS_READY"}:
        raise ValueError("fault records require a supported FEG mode")
    if any(f.past_offset_m < 0 for f in model.faults):
        raise ValueError("fault past offsets must be nonnegative")


def write_feg(model: FEGModel) -> str:
    """Serialize title, five-value header, nodes, triangles and faults."""
    _validate(model)
    node_fields = []
    for node in model.nodes:
        values = [str(node.node_id), _f(node.longitude_deg), _f(node.latitude_deg),
                  _f(node.elevation_m), _f(node.heat_flow_w_m2)]
        if model.mode == "SHELLS_READY":
            values.extend(_f(v) for v in (node.crustal_thickness_m,
                node.mantle_lithosphere_thickness_m,
                node.chemical_density_anomaly_kg_m3,
                node.cooling_curvature_k_m2))
        node_fields.append(" ".join(values))
    lines = [model.title[:80],
             f"{len(model.nodes)} {len(model.nodes)} {model.n_fake_nodes} {model.n1000} {_brief_token(model.brief)}",
             *node_fields, str(len(model.elements))]
    for element in model.elements:
        row = f"{element.element_id} {' '.join(map(str, element.node_ids))}"
        if element.lr_id is not None:
            row += f" LR {element.lr_id}"
        lines.append(row)
    lines.append(str(len(model.faults)))
    for fault in model.faults:
        row = (f"{fault.fault_id} {' '.join(map(str, fault.node_ids))} "
               f"{_f(fault.dip1_deg)} {_f(fault.dip2_deg)} {_f(fault.past_offset_m)}")
        if fault.lr_id is not None:
            row += f" LR {fault.lr_id}"
        lines.append(row)
    return "\n".join(lines) + "\n"


def _tokens(text: str) -> list[str]:
    lines = text.splitlines()
    if len(lines) < 2:
        raise ValueError("FEG text must contain title and header")
    return [lines[0], *re.sub(r"[,\t]", " ", "\n".join(lines[1:])).split()]


def _int(tokens: list[str], position: int) -> tuple[int, int]:
    try:
        return int(tokens[position]), position + 1
    except (IndexError, ValueError) as exc:
        raise ValueError(f"expected integer FEG token at offset {position}") from exc


def _brief_value(value: bool | int | str) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, int) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().upper()
        if token in {"T", ".TRUE."}:
            return True
        if token in {"F", ".FALSE."}:
            return False
        if token in {"0", "1"}:
            return token == "1"
    raise ValueError("FEG brief must be a Fortran logical or legacy 0/1")


def _brief_token(value: bool | int | str) -> str:
    return "T" if _brief_value(value) else "F"


def _float(tokens: list[str], position: int) -> tuple[float, int]:
    try:
        token = tokens[position].replace("D", "E").replace("d", "e")
        if not _FLOAT.fullmatch(token):
            raise ValueError
        value = float(token)
        if not math.isfinite(value):
            raise ValueError
        return value, position + 1
    except (IndexError, ValueError) as exc:
        raise ValueError(f"expected finite real FEG token at offset {position}") from exc


def _lr(tokens: list[str], position: int) -> tuple[int | None, int]:
    if position < len(tokens) and tokens[position].upper() == "LR":
        return _int(tokens, position + 1)[0], position + 2
    return None, position


def parse_feg(text: str, *, mode: str,
              fixture_status: tuple[str, ...] = ()) -> FEGModel:
    tokens = _tokens(text)
    title, pos = tokens[0], 1
    num_nodes, pos = _int(tokens, pos)
    n_real, pos = _int(tokens, pos)
    n_fake, pos = _int(tokens, pos)
    n1000, pos = _int(tokens, pos)
    try:
        brief = _brief_value(tokens[pos])
        pos += 1
    except (IndexError, ValueError) as exc:
        raise ValueError(f"expected Fortran logical FEG brief token at offset {pos}") from exc
    if num_nodes < 0 or n_real != num_nodes or n_fake != 0:
        raise ValueError("unsupported ShellSet FEG node numbering header")
    node_width = 5 if mode == "PRE_ORBDATA" else 9 if mode == "SHELLS_READY" else 0
    if not node_width:
        raise ValueError(f"unsupported FEG mode {mode}")
    nodes = []
    for _ in range(num_nodes):
        node_id, pos = _int(tokens, pos)
        lon, pos = _float(tokens, pos)
        lat, pos = _float(tokens, pos)
        values = []
        for _ in range(node_width - 3):
            value, pos = _float(tokens, pos)
            values.append(value)
        if node_width == 5:
            nodes.append(NodeRecord(node_id, lon, lat, *values))
        else:
            nodes.append(NodeRecord(node_id, lon, lat, *values))
    num_elements, pos = _int(tokens, pos)
    elements = []
    for _ in range(num_elements):
        element_id, pos = _int(tokens, pos)
        n1, pos = _int(tokens, pos); n2, pos = _int(tokens, pos); n3, pos = _int(tokens, pos)
        lr_id, pos = _lr(tokens, pos)
        elements.append(ElementRecord(element_id, (n1, n2, n3), lr_id))
    num_faults, pos = _int(tokens, pos)
    faults = []
    for _ in range(num_faults):
        fault_id, pos = _int(tokens, pos)
        node_ids = []
        for _ in range(4):
            value, pos = _int(tokens, pos); node_ids.append(value)
        dip1, pos = _float(tokens, pos); dip2, pos = _float(tokens, pos)
        offset, pos = _float(tokens, pos)
        lr_id, pos = _lr(tokens, pos)
        faults.append(FaultRecord(fault_id, tuple(node_ids), dip1, dip2, offset, lr_id))
    if pos != len(tokens):
        raise ValueError(f"unexpected trailing FEG tokens at offset {pos}")
    model = FEGModel(title, mode, tuple(nodes), tuple(elements), tuple(faults),
                     n_fake, n1000, brief, tuple(sorted(set(fixture_status))))
    _validate(model)
    return model


def normalized_feg_dict(model: FEGModel) -> dict:
    _validate(model)
    node_records = []
    for node in model.nodes:
        record = {"node_id": node.node_id}
        for name in ("longitude_deg", "latitude_deg", "elevation_m", "heat_flow_w_m2",
                     "crustal_thickness_m", "mantle_lithosphere_thickness_m",
                     "chemical_density_anomaly_kg_m3", "cooling_curvature_k_m2"):
            value = getattr(node, name)
            record[name] = None if value is None else _f(value)
        node_records.append(record)
    elements = [{"element_id": e.element_id, "node_ids": list(e.node_ids), "lr_id": e.lr_id}
                for e in model.elements]
    faults = [{"fault_id": f.fault_id, "node_ids": list(f.node_ids),
               "dip1_deg": _f(f.dip1_deg), "dip2_deg": _f(f.dip2_deg),
               "past_offset_m": _f(f.past_offset_m), "lr_id": f.lr_id}
              for f in model.faults]
    return {
        "schema": "ARCANA_FEG_SUBSET_V1", "mode": model.mode,
        "fixture_status": sorted(set(model.fixture_status)),
        "header": {"numNod": len(model.nodes), "nRealN": len(model.nodes),
                   "nFakeN": model.n_fake_nodes, "n1000": model.n1000,
                   "brief": int(_brief_value(model.brief))},
        "nodes": node_records,
        "elements": elements,
        "faults": faults,
        "title_policy": "title excluded from semantic identity; title record remains serialized",
    }


def normalized_feg_sha256(model: FEGModel) -> str:
    body = json.dumps(normalized_feg_dict(model), sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(body).hexdigest()


def fixture_roundtrip_evidence() -> dict[str, str | bool]:
    """Exercise only a tiny, explicitly noncanonical test FEG model."""
    from .model import ElementRecord, FaultRecord, NodeRecord

    flags = ("TEST_FIXTURE_ONLY", "NOT_CANONICAL", "NOT_WORLD_HISTORY",
             "NOT_PRODUCTION_INPUT")
    model = FEGModel(
        title="ARCANA TEST FIXTURE ONLY",
        mode="SHELLS_READY",
        nodes=(
            NodeRecord(1, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
            NodeRecord(2, 1.0, 0.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
            NodeRecord(3, 1.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
            NodeRecord(4, 0.0, 1.0, 0.0, 0.0, 1.0, 1.0, 0.0, 0.0),
        ),
        elements=(ElementRecord(1, (1, 2, 3), 7), ElementRecord(2, (1, 3, 4))),
        faults=(FaultRecord(1, (1, 2, 3, 4), 30.0, 35.0, 0.0, 2),),
        fixture_status=flags,
    )
    text = write_feg(model)
    parsed = parse_feg(text, mode=model.mode, fixture_status=flags)
    rerendered = write_feg(parsed)
    return {
        "normalized_sha256": normalized_feg_sha256(model),
        "semantic_equality": normalized_feg_sha256(model) == normalized_feg_sha256(parsed),
        "normalized_serialization_stable": text == rerendered,
        "fixture_authority": "TEST_FIXTURE_ONLY; NOT_CANONICAL; NOT_WORLD_HISTORY; NOT_PRODUCTION_INPUT",
    }
