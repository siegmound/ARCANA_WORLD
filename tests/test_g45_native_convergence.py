from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1'))
import arcana_g45_distributed_amr_cbf as c

def fixture(tmp_path,text):
    (tmp_path/'output').mkdir();(tmp_path/'output/parameters.prm').write_text('set Nonlinear solver tolerance = 1e-6\n');(tmp_path/'STDOUT.txt').write_text(text);return tmp_path

def test_exit_zero_never_overrides_native_solver_failure(tmp_path):
    case=fixture(tmp_path,'Relative nonlinear residual (Stokes system) after nonlinear iteration 10: 0.000207353\nWARNING: During this computation 1 nonlinear solver failures occurred!\n')
    report=c.native_convergence(case)
    assert not report['screen_pass'] and report['solver_failure_warnings'] and report['last_residual']>report['configured_nonlinear_tolerance']

def test_converged_native_residual_without_warnings(tmp_path):
    case=fixture(tmp_path,'Relative nonlinear residual (Stokes system) after nonlinear iteration 2: 1.97e-8\n')
    assert c.native_convergence(case)['screen_pass']
