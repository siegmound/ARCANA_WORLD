"""Synthetic HR1 infrastructure only; no global physical solver tests."""
import json,sys
from pathlib import Path
import numpy as np
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import r6_hr1_mres as h

@pytest.mark.parametrize('name,w,n',h.TIERS)
def test_spherical_coverage_and_seam(name,w,n):
    cfg=h.config(w,n,1);g=h.geometry(cfg)
    assert len(g['row_cell_areas_m2'])==n
    assert all(a>0 for a in g['row_cell_areas_m2'])
    assert abs(g['area_residual_m2'])/g['analytic_sphere_area_m2']<5e-15
    assert (0,w-1) in h.neighbors(0,0,w,n)
    assert all(r>=0 for r,c in h.neighbors(0,0,w,n))
    assert all(r<n for r,c in h.neighbors(n-1,w-1,w,n))

@pytest.mark.parametrize('payload',[64,256,1024])
def test_lossless_partial_tile_and_corruption(payload):
    cfg=h.config(258,129,10,payload);r,c,nr,nc=list(h.tiles(cfg))[-1]
    values=h.expected_tile(cfg,r,c,nr,nc,7).reshape(nr,nc,cfg['fields'])
    mask=h.masks(cfg)[r:r+nr,c:c+nc];cost=h.defaultdict(float)
    blob,raw,packed,n=h.encode_tile(values,mask,cost)
    meta={'rows':nr,'columns':nc,'raw_sha256':raw,'compressed_sha256':packed}
    decoded,m=h.decode_tile(blob,meta,cfg['fields'])
    assert np.array_equal(decoded,values) and np.array_equal(m,mask)
    assert n==nr*nc*(payload+1)
    with pytest.raises(ValueError,match='CORRUPT'):h.decode_tile(blob[:-1],meta,cfg['fields'])


def test_independent_dyadic_table():
    cfg=h.config(4,2,3)
    actual=h.expected_tile(cfg,0,0,1,1,0)[0]
    assert actual.tolist()==[0,1/64,2/64,3/64,4/64,5/64,6/64,7/64]
    actual+=(np.arange(1,9)/1048576)
    assert actual.tolist()==[(16384*f+f+1)/1048576 for f in range(8)]


def test_b0_direct_split_continuation(tmp_path):
    cfg=h.config(258,129,3)
    direct=h.Workload(tmp_path/'direct',cfg)
    for _ in range(3):direct.advance()
    direct.publish()
    split=h.Workload(tmp_path/'split',cfg);split.advance();split.publish()
    resumed=h.Workload(tmp_path/'split',cfg,resume=True)
    for _ in range(2):resumed.advance()
    resumed.publish()
    assert np.array_equal(direct.state,resumed.state)
    for root in [tmp_path/'direct',tmp_path/'split']:
        reader=h.Reader(root,cfg);assert reader.verify_prefix()['years']==3
        assert np.array_equal(reader.load(3),direct.state)
        with pytest.raises(ValueError,match='UNCOMMITTED'):reader.index(4)


@pytest.mark.parametrize('stage,new',[('before_visibility_switch',False),('after_visibility_switch',True),('during_cleanup',True)])
def test_b0_interrupted_pair_selection(tmp_path,stage,new):
    tmp_path=tmp_path/'run'
    class Interrupt(BaseException):pass
    cfg=h.config(8,4,3);work=h.Workload(tmp_path,cfg);work.advance();work.publish()
    def fault(found,count):
        if found==stage:raise Interrupt()
    # Use constructor's supported hook; preserve previous paired arrays.
    work.store=h.HistoryStore(tmp_path/'b0',_fault_injector=fault)
    work.advance()
    with pytest.raises(Interrupt):work.publish()
    reader=h.Reader(tmp_path,cfg);reader.verify_prefix();assert reader.year==(2 if new else 1)
    assert np.array_equal(reader.load(reader.year).reshape(-1,8),h.expected_tile(cfg,0,0,4,8,reader.year))


@pytest.mark.parametrize('kind',['data','index','events','source','config'])
def test_closed_corruptions(tmp_path,kind):
    tmp_path=tmp_path/'run'
    cfg=h.config(8,4,1);w=h.Workload(tmp_path,cfg);w.advance();w.publish()
    if kind in ['source','config']:
        p=tmp_path/('SOURCE.json' if kind=='source' else 'CONFIG.json');p.write_text('{}')
        with pytest.raises(ValueError):h.Reader(tmp_path,cfg)
    else:
        suffix={'data':'bin','index':'index.jsonl','events':'events.jsonl'}[kind]
        p=tmp_path/'years'/('0001.'+suffix);p.write_bytes(p.read_bytes()+b'x')
        with pytest.raises(ValueError,match='CORRUPT'):h.Reader(tmp_path,cfg).verify_prefix()


def test_event_null_semantics_and_probe(tmp_path):
    tmp_path=tmp_path/'run'
    cfg=h.config(16,8,10,event_period=11);h.run(tmp_path,cfg)
    result=h.probe(tmp_path,cfg)
    assert result['status']=='PASS_EXACT_QUERY_AND_SYNTHETIC_RESTART'
    assert result['integrity']['null_events']>0 and result['physical_advances']==0
    assert result['restart_from_year']==0


@pytest.mark.parametrize('args',[(16,9,1,64),(16,8,0,64),(16,8,1,65)])
def test_invalid_configuration(args):
    with pytest.raises(ValueError):h.config(*args)
