from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1'))
import arcana_g45_distributed_amr_cbf as c

def test_refinement_strategy_is_unique_and_solver_unchanged():
    original='subsection Mesh refinement\n  set Initial global refinement = 2\n  set Initial adaptive refinement = 1\n  set Strategy = velocity\n  set Refinement fraction = 0.2\nend\nset Linear solver tolerance = 1e-6\n'
    text=c.refinement_settings(original)
    assert text.count('set Strategy')==1 and 'Strategy = arcana g45 deterministic' in text
    assert text.count('set Refinement fraction')==1 and 'Refinement fraction = 0\n' in text
    assert 'Initial adaptive refinement = 1' in text and 'Linear solver tolerance = 1e-6' in text

def test_analytic_postprocessors_are_unique(monkeypatch,tmp_path):
    p=tmp_path/'upstream.prm';p.write_text('set Additional shared libraries = ./libhollow_sphere.so\nsubsection Mesh refinement\nset Initial global refinement = 4\nset Initial adaptive refinement = 0\nset Strategy = velocity\nend\nsubsection Postprocess\nset List of postprocessors = HollowSpherePostprocessor, dynamic topography\nend\n')
    monkeypatch.setattr(c.old,'runtime',lambda:(None,None,None,None,None,p,None,None))
    text=c.prm_for({'family':'analytic','base_refinement':2,'adaptive_cycles':1})
    line=next(x for x in text.splitlines() if 'List of postprocessors' in x)
    names=[x.strip() for x in line.split('=',1)[1].split(',')]
    assert len(names)==len(set(names)) and 'arcana g45 distributed cbf' in names
    assert 'Initial adaptive refinement = 1' in text
