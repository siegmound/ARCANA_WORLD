"""Deterministic numerical mesh support for the R6 ShellSet adapter."""

from .adapter import (CanonicalMesh, build_canonical_mesh, load_canonical_mesh,
                      project_cell_field_to_nodes)
from .model import (ElementRecord, FEGModel, FaultRecord, NodeRecord,
                    PhysicalFieldBinding, model_from_mesh)
from .feg import (fixture_roundtrip_evidence, normalized_feg_sha256,
                  parse_feg, write_feg)

__all__ = ["CanonicalMesh", "build_canonical_mesh", "load_canonical_mesh",
           "project_cell_field_to_nodes",
           "ElementRecord", "FEGModel", "FaultRecord", "NodeRecord",
           "PhysicalFieldBinding", "model_from_mesh", "normalized_feg_sha256",
           "parse_feg", "write_feg", "fixture_roundtrip_evidence"]
