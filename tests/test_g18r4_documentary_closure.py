from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1'))
from arcana_g18r4_documentary_closure import recover_markers

@pytest.mark.parametrize('split',['G17_SPARSE_SOLVED  @  1','G17_SPARSE_SOLVE@D    1'])
def test_actual_interleaving(split):
    raw=split.replace('@','Warning: ieee_inexact is signaling\n    0\n')+'\n'
    assert recover_markers(raw,1)['screen_pass']

@pytest.mark.parametrize('raw',[
 'G17_SPARSE_SOLVED  Warning: ieee_inexact is signaling\n    0\n',
 'G17_SPARSE_SOLVED  Warning: ieee_invalid is signaling\n    0\n  1\n',
 'G17_SPARSE_SOLVED  Warning: ieee_inexact is signaling\n    0\n  1\nG17_SPARSE_SOLVED 1\n',
 'G17_SPARSE_SOLVED 1\n',
 'G17_SPARSE_SOLVEWarning: ieee_inexact is signaling\n    0\nD  2\n'])
def test_no_inferred_id_or_waived_warning(raw):
    assert not recover_markers(raw,1)['screen_pass']
