"""Bind extracted SHELLS fields to parent supports before any T1 update."""
from numbers import Integral

import numpy as np

from arcana_worldsim.r6.shellset_mesh.coordinates import rotation_matrices


def bind_solution(case, nodes, elements):
    """Join finite native fields by local IDs, in documented SHELLS order.

    The caller extracts converged v(2,node) and EDot eRate(3,7,element).
    Input maps use integer local IDs. Values are SI. No update is performed.
    """
    if (any(not isinstance(key, Integral) or isinstance(key, bool) for key in nodes)
            or any(not isinstance(key, Integral) or isinstance(key, bool) for key in elements)
            or set(nodes) != {row["local_id"] for row in case["nodes"]}
            or set(elements) != {row["local_id"] for row in case["elements"]}):
        raise ValueError("Missing, unexpected or invalid local solution IDs")
    _, inverse_rotation = rotation_matrices()
    velocities = {}
    for row in case["nodes"]:
        value = np.asarray(nodes[row["local_id"]], dtype=float)
        if value.shape != (2,) or not np.isfinite(value).all():
            raise ValueError("Invalid SHELLS velocity (south, east)")
        phi, lam = np.deg2rad(row["runtime_lat_lon_deg"])
        south = np.array([np.sin(phi)*np.cos(lam), np.sin(phi)*np.sin(lam), -np.cos(phi)])
        east = np.array([-np.sin(lam), np.cos(lam), 0.])
        velocities[row["parent_id"]] = (inverse_rotation @ (value[0]*south + value[1]*east)).tolist()
    strain = {}
    for row in case["elements"]:
        value = np.asarray(elements[row["local_id"]], dtype=float)
        if value.shape != (7, 3) or not np.isfinite(value).all():
            raise ValueError("Expected seven EDot points with xx, yy, tensor xy")
        strain[row["parent_id"]] = {
            "runtime_xx_yy_xy_s_inv": value.tolist(),
            "horizontal_trace_s_inv": (value[:, 0] + value[:, 1]).tolist(),
        }
    return {"canonical_xyz_m_s_by_parent_node": velocities,
            "strain_rate_by_parent_element": strain}
