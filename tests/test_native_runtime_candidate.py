from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1'))
from arcana_native_runtime_candidate import in_root,inherit_search_path

def test_absolute_root_symlink_is_namespace_relative(tmp_path):
    (tmp_path/'usr').mkdir();(tmp_path/'usr/lib').mkdir();(tmp_path/'usr/lib/library').write_text('payload')
    (tmp_path/'lib').symlink_to('/usr/lib')
    assert in_root(tmp_path,'lib/library')==tmp_path/'usr/lib/library'

def test_root_escape_rejected(tmp_path):
    (tmp_path/'bad').symlink_to('../../outside')
    with pytest.raises(ValueError):in_root(tmp_path,'bad')

def test_elf_patcher_rejects_arbitrary_payload(tmp_path):
    p=tmp_path/'not-elf';p.write_bytes(b'x'*64)
    with pytest.raises(ValueError):inherit_search_path(p)
