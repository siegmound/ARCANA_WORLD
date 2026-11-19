"""Test the regional artifact, original PRE evaluator parity and mapping."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

import numpy as np

from build_case import LOADER, PRE, ROOT, perimeter, parse_feg, _unit_vectors
from solution_mapping import bind_solution


def evaluate(work, module, ids, data, node_count, *, rejects=False):
    work.mkdir()
    driver = work / "probe.f90"
    node_ids = ",".join(map(str, ids))
    driver.write_text(f"""program probe
use ArcanaRuntime
implicit none
integer, parameter :: chosen({len(ids)}) = (/{node_ids}/)
integer :: input, requested, ierr, i, j, phase
real(8) :: temperature, props(7), values(51), z(4)
character(4096) :: path, count_arg, message
call get_command_argument(1,path)
call get_command_argument(2,count_arg)
read(count_arg,*) requested
open(newunit=input,file=trim(path),status='old')
call ArcanaRuntimeRead(input,requested,ierr,message)
close(input)
if (ierr /= 0) then
  print '(A)', trim(message)
  stop 2
end if
do i=1,size(chosen)
  call ArcanaRuntimeGet(chosen(i),values,ierr)
  if (ierr /= 0) stop 3
  write(*,'(50ES26.17E3)') values(2:)
  z = (/0d0, values(16), values(18), values(18)+1000d0/)
  do j=1,4
    call ArcanaRuntimeEvaluateNode(chosen(i),z(j),temperature,props,phase,ierr)
    if (ierr /= 0) stop 4
    write(*,'(I3,8ES26.17E3)') phase,temperature,props
  end do
end do
end program
""")
    exe = work / "probe"
    subprocess.run(["gfortran", "-O0", "-fcheck=all", str(module), str(driver), "-o", str(exe)],
                   cwd=work, check=True)
    result = subprocess.check_output([str(exe), str(data), str(node_count)], text=True)
    errors = {}
    if rejects:
        corrupt = work / "short.dat"
        corrupt.write_text("\n".join(data.read_text().splitlines()[:-1])+"\n")
        for label, payload, count, message in [
            ("wrong_count", data, node_count + 1, "ARCANA_FEG_NODE_COUNT_MISMATCH"),
            ("missing_row", corrupt, node_count, "ARCANA_RUNTIME_RECORD_MISSING"),
            ("global_schema", ROOT/(PRE+".dat"), node_count, "ARCANA_RUNTIME_BAD_MAGIC"),
        ]:
            run = subprocess.run([str(exe), str(payload), str(count)], capture_output=True, text=True)
            assert run.returncode == 2 and run.stdout.strip() == message
            errors[label] = message
    return result, errors


def main(directory):
    directory = directory.resolve()
    case = json.loads((directory/"CASE.json").read_text())
    model = parse_feg((directory/"regional.feg").read_text(), mode="SHELLS_READY")
    assert (len(model.nodes), len(model.elements), len(model.faults)) == (9, 8, 0)
    assert perimeter(model.elements) == case["perimeter_local_ids"]
    assert all(row["prescribed_components"] is None for row in case["nodes"])
    assert all(row["prescribed_traction_pa"] is None for row in case["nodes"])
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        parent_ids = [row["parent_id"] for row in case["nodes"]]
        parent, _ = evaluate(work/"parent", ROOT/LOADER, parent_ids, ROOT/(PRE+".dat"), 64442)
        regional, errors = evaluate(work/"regional", directory/"MOD_ArcanaRuntime.regional.f90",
                                    list(range(1, 10)), directory/"regional_PRE.dat", 9, rejects=True)
        assert parent == regional
    velocities = {r["local_id"]: r["candidate_euler_south_east_m_s"] for r in case["nodes"]}
    # Sentinel strain tests identity, slot ordering and tensor trace only.
    strain = {r["local_id"]: [[r["local_id"], -2., 3.]]*7 for r in case["elements"]}
    mapped = bind_solution(case, velocities, strain)
    euler = json.loads((ROOT/"R6_T0_CANONICAL_PLATE_KINEMATICS.json").read_text())
    omega = next(p["euler_vector_rad_per_year"] for p in euler["plates"] if p["plate_id"] == case["plate_id"])
    for row in case["nodes"]:
        xyz = _unit_vectors(np.array([row["canonical_lat_lon_deg"]]))[0]
        expected = np.cross(omega, xyz)*6_371_000/31_557_600
        np.testing.assert_allclose(mapped["canonical_xyz_m_s_by_parent_node"][row["parent_id"]],
                                   expected, atol=1e-22, rtol=0)
    for row in case["elements"]:
        assert mapped["strain_rate_by_parent_element"][row["parent_id"]]["horizontal_trace_s_inv"] == [row["local_id"]-2.]*7
    for invalid in ({}, {**velocities, 1: [float("nan"), 0.]}):
        try:
            bind_solution(case, invalid, strain)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid velocity inventory admitted")
    print(json.dumps(dict(status="PASS", node_records_equal=9, exact_evaluator_samples=36,
                          regional_loader_rejections=errors, mapping_checks="PASS",
                          solver_runs=0), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    main(parser.parse_args().directory)
