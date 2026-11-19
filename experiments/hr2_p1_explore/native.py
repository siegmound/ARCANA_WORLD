"""Complete experimental numerical checkpoint; not REC1/B0 qualification."""
from pathlib import Path
import hashlib,json,dataclasses
import numpy as np
from scipy.sparse import csr_matrix
from .model import Operator,Mesh

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def model_sha():return digest(Path(__file__).with_name('model.py'))
def save(path,op,V,steps,dt):
    data={k:np.asarray(getattr(op.mesh,k)) for k in op.mesh.__dataclass_fields__}
    data.update(G_data=op.G.data,G_indices=op.G.indices,G_indptr=op.G.indptr,G_shape=op.G.shape,
      c=op.c,V=np.asarray(V))
    meta={'version':'EXPLORE_NATIVE_1','model_sha256':model_sha(),'numpy':np.__version__,'kappa':op.kappa,'order':op.order,
      'cfl':op.cfl,'steps':steps,'dt':dt,'year':steps*dt,'B0_qualified':False}
    data['metadata_utf8']=np.frombuffer(json.dumps(meta,sort_keys=True).encode(),dtype='u1')
    with Path(path).open('xb') as f:np.savez(f,**data)
    return digest(path)
def load(path,expected):
    if digest(path)!=expected:raise ValueError('CHECKPOINT_SHA')
    with np.load(path,allow_pickle=False) as z:
        meta=json.loads(z['metadata_utf8'].tobytes())
        if meta['model_sha256']!=model_sha() or meta['version']!='EXPLORE_NATIVE_1' or meta['numpy']!=np.__version__:raise ValueError('CHECKPOINT_SOURCE_RUNTIME')
        kw={k:np.array(z[k],copy=True) for k in Mesh.__dataclass_fields__}
        for k in ['width','height']:kw[k]=int(kw[k])
        kw['radius']=float(kw['radius']);op=Operator.__new__(Operator);op.mesh=Mesh(**kw)
        op.kappa=meta['kappa'];op.order=meta['order'];op.cfl=meta['cfl'];op.c=np.array(z['c'],copy=True)
        op.G=csr_matrix((np.array(z['G_data'],copy=True),np.array(z['G_indices'],copy=True),np.array(z['G_indptr'],copy=True)),shape=tuple(z['G_shape']))
        V=np.array(z['V'],copy=True)
    if V.shape!=op.mesh.areas.shape or not np.isfinite(V).all() or (V<0).any():raise ValueError('CHECKPOINT_STATE')
    return op,V,meta
