"""Validate the saved engineering SHELLS output without invoking the solver."""
import argparse
import json
import math
from pathlib import Path
import re

import numpy as np

from solution_mapping import bind_solution


def check(root):
    case = json.loads((root/"CASE.json").read_text())
    rows = [line.split() for line in (root/"native_fields.txt").read_text().splitlines()]
    assert rows[0] == ["9", "8", "8", "T"] and len(rows) == 74
    velocities = {}
    for row in rows[1:10]:
        node, south, east, slot = row
        assert int(slot) == 1 and int(node) not in velocities
        velocities[int(node)] = list(map(float, (south, east)))
    rates, stress = {}, {}
    for row in rows[10:66]:
        element, point = map(int, row[:2])
        values = list(map(float, row[2:]))
        assert len(values) == 6 and all(math.isfinite(x) for x in values)
        assert point == len(rates.get(element, [])) + 1
        rates.setdefault(element, []).append(values[:3])
        stress.setdefault(element, []).append(values[3:])
    expected = json.loads((root/"PRESCRIBED.json").read_text())
    max_bc_error = 0.
    for node, row in zip(case["perimeter_local_ids"], rows[66:], strict=True):
        n, kind, angle, speed = row
        assert int(n) == node and int(kind) == 2
        speed, angle = float(speed), float(angle)
        imposed = np.array([math.cos(angle), math.sin(angle)])*speed
        np.testing.assert_allclose(imposed, expected[str(node)], atol=1e-22, rtol=0)
        error = float(np.max(abs(np.asarray(velocities[node])-imposed)))
        max_bc_error = max(max_bc_error,error)
    assert max_bc_error < 1e-20
    solution = bind_solution(case, velocities, rates)
    solution["integrated_stress_N_m_by_parent_element"] = {
        str(row["parent_id"]): stress[row["local_id"]] for row in case["elements"]}
    log = (root/"shells.log").read_text()
    iteration_log = log.split("Iteration history:",1)[1].split("CONVERGED",1)[0]
    iterations = [line.split() for line in iteration_log.splitlines()
                  if len(line.split()) >= 5 and line.split()[0].isdigit()]
    last = iterations[-1]
    assert "CONVERGED" in log and float(last[3]) <= 0.0005
    assert (root/"solve.exit").read_text().strip()=="0"
    assert not (root/"FatalError.txt").exists()
    for name in ["shells.log","velocity.22","reactions.23","torques.24"]:
        assert not re.search(r"\b(?:nan|inf|infinity)\b",(root/name).read_text(),re.I)
    solution.update(classification="ENGINEERING_ONLY", accepted_T1=None, solver_calls=1,
                    iterations=int(last[0]), relative_velocity_change=float(last[3]),
                    relative_velocity_threshold=0.0005,
                    max_boundary_component_error_m_s=max_bc_error,
                    rms_speed_m_s=float(np.sqrt(np.mean(np.sum(np.array(list(velocities.values()))**2,axis=1)))),
                    max_abs_EDot_component_s_inv=float(np.max(np.abs(list(rates.values())))),
                    max_abs_integrated_stress_N_m=float(np.max(np.abs(list(stress.values())))))
    print(json.dumps(solution, indent=2,allow_nan=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output",type=Path)
    check(parser.parse_args().output)
