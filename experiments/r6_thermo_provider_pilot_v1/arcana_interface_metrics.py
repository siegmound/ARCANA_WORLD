"""Shared-trace force diagnostics only; no constitutive or physical model changes."""
import numpy as np

BALANCE_TOL = 1e-11

def force_diagnostic(fl, fm):
    """Symmetric scale: ||fl+fm|| / max(||fl||, ||fm||, 1e-300).

    Zero/zero has zero residual but cannot qualify an interface coupling.
    Inputs must be real, finite, nonempty and in the same shared trace space.
    """
    fl, fm = np.asarray(fl), np.asarray(fm)
    if (fl.shape != fm.shape or fl.size == 0 or np.iscomplexobj(fl)
            or np.iscomplexobj(fm)):
        raise ValueError('FORCE_SHAPE_OR_TYPE')
    fl, fm = fl.astype(float), fm.astype(float)
    if not (np.isfinite(fl).all() and np.isfinite(fm).all()):
        raise ValueError('NONFINITE_FORCE')
    with np.errstate(over='ignore', invalid='ignore'):
        residual = fl + fm
        # hypot reduction avoids overflow/underflow from squaring finite forces.
        nl, nm, nr = (float(np.hypot.reduce(x.ravel())) for x in (fl, fm, residual))
        legacy_n = float(np.hypot.reduce((residual-fl).ravel()))
    if not np.isfinite([nl, nm, nr, legacy_n]).all():
        raise ValueError('NONFINITE_FORCE_NORM')
    return {'lithosphere_force_norm_N': nl, 'mantle_force_norm_N': nm,
            'residual_force_norm_N': nr, 'normalization_N': max(nl, nm, 1e-300),
            'action_reaction_relative': nr/max(nl, nm, 1e-300),
            'legacy_action_reaction_relative': legacy_n/max(nl, 1e-300),
            'nonzero_coupling': bool(nl > 0 and nm > 0)}

def balance_screen(diss, qwork, p_err, adj, action, common_err, tangent_work, symmetry,
                   nonzero_coupling=True):
    errors = np.asarray([p_err, adj, action, common_err, tangent_work, symmetry])
    return bool(nonzero_coupling and np.isfinite([diss, qwork]).all()
                and diss > 0 and qwork > 0 and np.isfinite(errors).all()
                and np.all(errors >= 0) and np.all(errors < BALANCE_TOL))

def metric_selftest():
    fl = np.array([3., 4.])
    cases = {'balanced': -fl, 'wrong_sign': fl, 'missing': np.zeros(2),
             'perturbed': -fl + np.array([.03, .04]), 'different_scale': -10*fl,
             'both_zero': np.zeros(2)}
    expected = dict(balanced=0., wrong_sign=2., missing=1., perturbed=.01,
                    different_scale=.9, both_zero=0.)
    rows = {}
    for name, fm in cases.items():
        d = force_diagnostic(np.zeros(2) if name == 'both_zero' else fl, fm)
        if not np.isclose(d['action_reaction_relative'], expected[name], rtol=1e-13, atol=1e-15):
            raise RuntimeError('METRIC_SELFTEST:'+name)
        rows[name] = d
    if rows['balanced']['legacy_action_reaction_relative'] != 1.:
        raise RuntimeError('LEGACY_BUG_NOT_REPRODUCED')
    def accepted(d, action=None):
        return balance_screen(1., 1., 0., 0., d['action_reaction_relative'] if action is None else action,
                              0., 0., 0., d['nonzero_coupling'])
    if not accepted(rows['balanced']):
        raise RuntimeError('BALANCED_GATE_REJECTED')
    for name in ('wrong_sign', 'missing', 'perturbed', 'different_scale', 'both_zero'):
        if accepted(rows[name]):
            raise RuntimeError('NEGATIVE_GATE_ACCEPTED:'+name)
    if accepted(rows['balanced'], rows['balanced']['legacy_action_reaction_relative']):
        raise RuntimeError('LEGACY_GATE_ACCEPTED')
    for value in (float('nan'), float('inf'), -float('inf')):
        try:
            force_diagnostic(fl, [value, 0.])
        except ValueError:
            continue
        raise RuntimeError('NONFINITE_ACCEPTED')
    return {'screen_pass': True, 'cases': rows, 'wrong_reaction_gate_rejected': True,
            'legacy_balanced_gate_rejected': True, 'nonfinite_rejected': True}
