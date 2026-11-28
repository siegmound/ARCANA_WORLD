from pathlib import Path
import sys
import pytest
sys.path.insert(0,str(Path(__file__).parents[1]/'experiments/r6_thermo_provider_pilot_v1'))
import arcana_g44_hpc_campaign as c

@pytest.fixture(autouse=True)
def topology_fixture(monkeypatch):
    # Synthetic machine contract: no dependency on FAIR's external evidence.
    h={'topology':[{'cpu':i+64*smt,'socket':i//32,'core':i%32}
                   for smt in (0,1) for i in range(64)],
       'numa_nodes':{str(i):{'cpulist':f'{16*i}-{16*i+15},{64+16*i}-{79+16*i}'} for i in range(4)}}
    def read(path):
        assert path.name=='HARDWARE_BEFORE.json'
        return h
    monkeypatch.setattr(c,'read',read)

def test_refinement_scope():
    raw='set Initial global refinement = 4\nset Linear solver tolerance = 1e-6\nset End time = 0\n'
    for level in (2,3,4,5,6):
        actual=c.candidate(raw,level)
        assert actual.replace('refinement = '+str(level),'refinement = 4')==raw
    with pytest.raises(RuntimeError):c.candidate(raw,7)

def test_explicit_cpu_mapping():
    a=c.cpus(64,'spread');b=c.cpus(128,'spread')
    assert len(set(a))==64 and len(set(b))==128 and b[:64]==a
    h=c.read(c.ROOT/'HARDWARE_BEFORE.json')
    topology={r['cpu']:(r['socket'],r['core']) for r in h['topology']}
    assert len({topology[i] for i in a})==64
    assert all(topology[b[i]]==topology[b[i+64]] for i in range(64))

def test_mixed_native_statistics():
    assert c.numeric_or_text('4.2e-6')==4.2e-6
    assert c.numeric_or_text('output/solution/solution-00000')=='output/solution/solution-00000'

def test_throughput_uses_disjoint_physical_cores():
    all_cpus=c.cpus(64,'spread');a=c.validate_cpu_ids(32,all_cpus[:32]);b=c.validate_cpu_ids(32,all_cpus[32:])
    assert not set(a)&set(b) and set(a+b)==set(all_cpus)
    with pytest.raises(RuntimeError):c.validate_cpu_ids(32,[a[0]]*32)
    with pytest.raises(RuntimeError):c.validate_cpu_ids(32,c.cpus(128,'spread')[64:96])
