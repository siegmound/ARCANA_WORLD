"""REC1 explicit forcing and B0 committed-coupled-prefix contracts."""
import json

import pytest

from arcana_worldsim.r6.runtime_run_plan import AnnualUpliftPlan
from arcana_worldsim.r6.runtime_recovery import RecoveryController, RecoveryError
from arcana_worldsim.r6.int10k_runtime_compact import CompactRuntime
from arcana_worldsim.r6.regional_geological_evolution import RegionalConfig, _canonical
from arcana_worldsim.r6.geological_surface_microdomain import SUPPORTS
from arcana_worldsim.r6.store import HistoryStore, ImmutableRecordConflict
from test_r6_regional_geological_evolution import _initial_states, _identity


def plan(years):
    return AnnualUpliftPlan(years, {SUPPORTS[0]: 0.0001, SUPPORTS[1]: 0.0})


def controller(path, *, years=1000, fault=None, explicit=False):
    return RecoveryController(path, _initial_states(), _identity(),
        config=RegionalConfig(duration_years=years), run_id="REC1_TEST",
        run_plan=plan(years) if explicit else None, fault=fault)


def test_named_uplift_zero_advance_and_reference_default():
    for years,total in [(1000,0.1),(10000,1.0)]:
        p=plan(years)
        assert p.totals_by_support()[SUPPORTS[0]] == total
        rt=CompactRuntime(_initial_states(),_identity(),config=RegionalConfig(duration_years=years),
                          runtime_compact_history=True,run_plan=p)
        assert rt.time_year == 0
        assert rt.configuration['unified_config']['prescribed_uplift_total_m_by_support'] == [total,0.0]
    a=CompactRuntime(_initial_states(),_identity(),config=RegionalConfig(duration_years=1000),runtime_compact_history=True)
    b=CompactRuntime(_initial_states(),_identity(),config=RegionalConfig(duration_years=1000),runtime_compact_history=True,run_plan=plan(1000))
    a.advance(3);b.advance(3)
    assert _canonical(a.checkpoint()) == _canonical(b.checkpoint())


@pytest.mark.parametrize('bad',[{}, {SUPPORTS[0]:float('nan'),SUPPORTS[1]:0.0},
                                  {SUPPORTS[0]:0.0001,SUPPORTS[1]:0.0001}])
def test_invalid_or_wrong_support_forcing_rejected(bad):
    with pytest.raises(ValueError):AnnualUpliftPlan(10000,bad)


@pytest.mark.parametrize('years,split,planned,explicit',[(3,1,1000,False),(10,5,1000,False),
                                                       (3,1,10000,True),(10,5,10000,True)])
def test_committed_history_restart_matches_continuous(tmp_path,years,split,planned,explicit):
    direct=controller(tmp_path/'direct',years=planned,explicit=explicit)
    direct.start();direct.advance(years);direct.commit()
    split_run=controller(tmp_path/'split',years=planned,explicit=explicit)
    split_run.start();split_run.advance(split);split_run.commit();split_run.close()
    resumed=controller(tmp_path/'split',years=planned,explicit=explicit)
    assert resumed.recover()['time_year'] == split
    resumed.advance(years-split);resumed.commit()
    assert _canonical(direct.native_checkpoint()) == _canonical(resumed.native_checkpoint())
    assert [(k,_canonical(v)) for k,v in direct.history()] == [(k,_canonical(v)) for k,v in resumed.history()]
    assert resumed.recover()['time_year'] == years
    direct.close();resumed.close()


class Interrupt(BaseException):pass


@pytest.mark.parametrize('stage,new_visible',[
    ('before_journal_fsync',False),('after_journal_fsync',False),
    ('before_checkpoint_seal',False),('after_checkpoint_persistence',False),
    ('before_visibility_switch',False),('after_visibility_switch',True),('during_cleanup',True)])
def test_interrupted_commit_recovers_old_or_new_b0_pair(tmp_path,stage,new_visible):
    c=controller(tmp_path);c.start();c.advance(1);c.commit();c.close()
    def fault(found,count):
        if found==stage:raise Interrupt()
    failing=controller(tmp_path,fault=fault);failing.recover();failing.advance(2)
    with pytest.raises(Interrupt):failing.commit()
    failing.close()
    reopened=controller(tmp_path)
    assert reopened.recover()['time_year']==(3 if new_visible else 1)
    assert reopened.recover()['time_year']==(3 if new_visible else 1)
    reopened.close()


def test_stale_parent_and_old_pinned_view(tmp_path):
    first=controller(tmp_path);first.start();first.advance();first.commit()
    stale=controller(tmp_path);stale.recover();stale.advance()
    reader=HistoryStore(tmp_path/'b0')
    with reader.read_view() as old:
        before=reader.checkpoints()
        first.advance();first.commit()
        assert reader.checkpoints()==before
        assert reader.read_view is not None
        with pytest.raises(ImmutableRecordConflict):stale.commit()
    assert len(reader.checkpoints())==2
    first.close();stale.close()


@pytest.mark.parametrize('kind',['chunk_truncate','chunk_corrupt','native_corrupt','config'])
def test_corrupt_or_incoherent_pair_fails_closed(tmp_path,kind):
    c=controller(tmp_path);c.start();c.advance(3);c.commit();c.close()
    if kind=='config':
        other=controller(tmp_path,years=10000,explicit=True)
        with pytest.raises(RecoveryError):other.recover()
        return
    directory='chunks' if kind.startswith('chunk') else 'frontiers'
    file=next((tmp_path/directory).glob('*'))
    data=file.read_bytes()
    file.write_bytes(data[:-17] if kind=='chunk_truncate' else data.replace(b'"time_year":',b'"tampered_":',1))
    if file.read_bytes()==data:file.write_bytes(b'{}')
    with pytest.raises(RecoveryError):controller(tmp_path).recover()


def test_history_ownership_and_incoherent_valid_checkpoint(tmp_path):
    c=controller(tmp_path/'history');c.start();c.advance(3);c.commit()
    retained=list(c.history())
    assert retained[0][1]['time_year']==0
    assert _canonical(retained)==_canonical(list(c.history()))
    retained[0][1]['cells'][0]['deposits'].append({'reader_mutation':True})
    assert _canonical(retained)!=_canonical(list(c.history()))
    other=controller(tmp_path/'other');other.start();other.advance(1);other.commit()
    bad=other.native_checkpoint()  # valid seal, wrong frontier/clock
    c.advance()
    c.runtime.checkpoint=lambda:bad
    with pytest.raises(RecoveryError,match='INCOMPLETE_COUPLED_HISTORY'):c.commit()
    assert controller(tmp_path/'history').recover()['time_year']==3
    c.close();other.close()


def test_horizon_source_and_orphan_fail_closed(tmp_path):
    c=controller(tmp_path);c.start();c.advance();c.commit();c.close()
    (tmp_path/'active'/'uncommitted.json').write_text('not a checkpoint')
    assert controller(tmp_path).recover()['time_year']==1
    changed=controller(tmp_path)
    changed.runtime_identity['sources']['store.py']='0'*64
    with pytest.raises(RecoveryError,match='SOURCE_OR_CONFIG'):changed.recover()
    with pytest.raises(ValueError):
        CompactRuntime(_initial_states(),_identity(),config=RegionalConfig(duration_years=1000),
                       runtime_compact_history=True,run_plan=plan(10000))
