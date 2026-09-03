from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Sequence
import json

import numpy as np

from .nemo242_r36d import _nemo_matrix, _nemo_vector, NEMO_REQUIRED_VERSION, NEMO_REQUIRED_EXECUTABLE
from .serialization import file_sha256


@dataclass(frozen=True)
class R37AB2Phase:
    name: str
    transitions: int
    exchange_matrix: np.ndarray

    def __post_init__(self) -> None:
        m=np.asarray(self.exchange_matrix,dtype=float)
        if m.ndim!=2 or m.shape[0]!=m.shape[1] or self.transitions<1:
            raise ValueError('invalid B2 phase')
        if np.any(m < -1e-15) or np.any(m.sum(axis=1)>1+1e-12) or np.max(np.abs(np.diag(m)))>1e-15:
            raise ValueError('B2 ARCANA exchange matrix must be zero-diagonal with row sum <=1')
        object.__setattr__(self,'exchange_matrix',m.copy()); self.exchange_matrix.setflags(write=False)


def canonical_r37a_b2_phases() -> tuple[R37AB2Phase,...]:
    def sym(n,pairs):
        x=np.zeros((n,n),float)
        for i,j,v in pairs: x[i,j]=x[j,i]=float(v)
        return x
    return (
        R37AB2Phase('CONNECTED_BURNIN',250,sym(4,[(0,1,.03),(1,2,.03),(2,3,.03)])),
        R37AB2Phase('FRAGMENTED',400,sym(4,[(0,1,.03),(2,3,.03)])),
        R37AB2Phase('RECONNECTED',550,sym(4,[(0,1,.03),(1,2,.03),(2,3,.03)])),
    )


def b2_nemo_transition(exchange_matrix: np.ndarray) -> np.ndarray:
    """Convert benchmark per-generation off-diagonal exchange to NEMO matrix.

    R3.7A B2 is a generation-scale reference, not the 125-kyr World-1 cadence.
    The symmetric matrix is completed with self-retention and is therefore both
    row- and column-stochastic, suitable for NEMO breed_disperse backward rates.
    """
    g=np.asarray(exchange_matrix,float)
    if g.ndim!=2 or g.shape[0]!=g.shape[1] or np.max(np.abs(np.diag(g)))>1e-15:
        raise ValueError('exchange must be square zero-diagonal')
    p=g.copy(); np.fill_diagonal(p,1.0-g.sum(axis=1))
    if np.min(p)<-1e-12 or not np.allclose(p.sum(axis=1),1,atol=1e-12,rtol=0):
        raise ValueError('invalid forward transition')
    if not np.allclose(p,p.T,atol=1e-12,rtol=0) or not np.allclose(p.sum(axis=0),1,atol=1e-12,rtol=0):
        raise ValueError('R3.7A B2 reference requires symmetric/doubly-stochastic matrix')
    return p


def render_r37a_b2_phase_ini(
    *,
    phase: R37AB2Phase,
    effect_a: Sequence[float],
    allele_frequencies: np.ndarray,
    population_size: int,
    seed: int,
    output_dir: str|Path,
    chain_id: str,
) -> dict:
    effects=np.asarray(effect_a,float)
    freq=np.asarray(allele_frequencies,float)
    if effects.ndim!=1 or freq.ndim!=2 or freq.shape[1]!=effects.size:
        raise ValueError('effect/frequency shape mismatch')
    if np.any(freq<=0) or np.any(freq>=1) or population_size<20:
        raise ValueError('B2 phase requires interior frequencies and N>=20')
    if freq.shape[0]!=phase.exchange_matrix.shape[0]:
        raise ValueError('patch count mismatch')
    root=Path(output_dir); root.mkdir(parents=True,exist_ok=True)
    trans=b2_nemo_transition(phase.exchange_matrix)
    generations=int(phase.transitions)+1
    half=0.5*effects
    filename=f"arcana_r37a_b2_{chain_id}_{phase.name.lower()}"
    ini=root/'Nemo2_ARCANA_R37A_B2.ini'
    text=f"""## ARCANA WorldSim v0.6D1-R3.7A -- NEMO 2.4.2 B2 frequency-state chain
logfile                 arcana_nemo242_r37a.log
run_mode                overwrite
random_seed             {int(seed)}
root_dir                .
filename                {filename}
replicates              1
generations             {generations}

patch_number            {freq.shape[0]}
patch_nbfem             {_nemo_vector([int(population_size)]*freq.shape[0])}
patch_nbmal             0

quanti_init             1
breed_disperse          2
save_stats              3
save_files              4
mating_system           6
mating_isWrightFisher
breed_disperse_matrix   {_nemo_matrix(trans)}

quanti_traits           1
quanti_loci             {effects.size}
quanti_allele_model     diallelic
quanti_diallele_datatype byte
quanti_allele_value     {_nemo_vector(half.tolist())}
quanti_init_freq        {_nemo_matrix(freq)}
quanti_mutation_rate    0
quanti_recombination_rate 0.5

stat                    adlt.demography adlt.quanti
stat_log_time           {generations}
quanti_freq_output      1
quanti_freq_logtime     {generations}
quanti_dir              .
"""
    ini.write_text(text,encoding='utf-8')
    np.savetxt(root/'initial_allele_frequencies.tsv',freq,delimiter='\t',fmt='%.17g')
    np.savetxt(root/'nemo_transition.tsv',trans,delimiter='\t',fmt='%.17g')
    manifest={
        'schema':'ARCANA_R37A_NEMO_B2_PHASE_BINDING_V1','stage':'v0.6D1-R3.7A',
        'chain_id':str(chain_id),'phase':phase.name,'transitions':int(phase.transitions),
        'nemo_generations_parameter':generations,'population_size':int(population_size),'seed':int(seed),
        'nemo_required_version':NEMO_REQUIRED_VERSION,'nemo_required_executable':NEMO_REQUIRED_EXECUTABLE,
        'protocol':'B2_FREQUENCY_STATE_CHAIN__ADMIXTURE_RECOMBINATION_DRIFT_ONLY',
        'selection_enabled':False,'mutation_rate':0.0,'recombination_rate':0.5,
        'phase_boundary_semantics':'QFREQ_ALLELE_FREQUENCIES_REINITIALIZED__HARDY_WEINBERG_AND_LD_RESET_AT_BOUNDARY',
        'observable_authority':'SEGREGATION_POTENTIAL_S_FROM_ALLELE_FREQUENCY_DISTANCE',
        'canonical_write_allowed':False,'automatic_calibration_allowed':False,
        'ini_file':ini.name,'ini_sha256':file_sha256(ini),
    }
    (root/'R3_7A_B2_PHASE_MANIFEST.json').write_text(json.dumps(manifest,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return manifest


def b2_reduced_order_deterministic_trajectory(
    initial_segregation_potential: np.ndarray,
    phases: Sequence[R37AB2Phase] | None=None,
) -> list[dict]:
    """Exact deterministic migration-only S trajectory for the B2 geometry."""
    from .segregation_aware_admixture import transform_segregation_potential
    s=np.asarray(initial_segregation_potential,float).copy()
    validate_shape=(s.ndim==3 and s.shape[0]==s.shape[1])
    if not validate_shape: raise ValueError('S must be deme x deme x trait')
    out=[]
    for phase in (tuple(phases) if phases is not None else canonical_r37a_b2_phases()):
        p=b2_nemo_transition(phase.exchange_matrix)
        pt=np.linalg.matrix_power(p,int(phase.transitions))
        s=transform_segregation_potential(s,pt)
        vals=s[np.triu_indices(s.shape[0],1)]
        out.append({
            'phase':phase.name,'transitions':phase.transitions,
            'max_S':float(np.max(s)),'mean_pair_S':float(np.mean(vals)) if vals.size else 0.0,
            'S':s.tolist(),'canonical_write_allowed':False,
        })
    return out
