"""Interface-aligned 1D conduction; immutable materials, no geometry motion."""
import numpy as np

def properties(z,H,mat):
    z=np.asarray(z,dtype=float)
    if not np.all(np.isfinite(z)) or np.any(np.diff(z)<=0) or not z[0]==0 or not 0<H<z[-1]: raise ValueError('invalid geometry')
    m=np.asarray(mat,dtype=float) # two rows k,rho,Cp,A
    if m.shape!=(2,4) or not np.all(np.isfinite(m)) or np.any(m[:,:3]<=0) or np.any(m[:,3]<0):raise ValueError('invalid materials')
    edges=np.r_[z[0],(z[:-1]+z[1:])/2,z[-1]]
    crust=np.clip(H-edges[:-1],0,np.diff(edges)); mantle=np.diff(edges)-crust
    C=crust*m[0,1]*m[0,2]+mantle*m[1,1]*m[1,2]
    S=crust*m[0,3]+mantle*m[1,3]
    lc=np.clip(H-z[:-1],0,np.diff(z)); lm=np.diff(z)-lc
    g=1/(lc/m[0,0]+lm/m[1,0])
    return C,S,g,edges

def advance(z,H,mat,T0,duration,steps):
    C,S,g,edges=properties(z,H,mat); T=np.asarray(T0,float).copy()
    limit=float(np.min(C[1:-1]/(g[:-1]+g[1:])));dt=duration/steps
    if dt>.8*limit:raise ValueError('unsafe dt')
    histories=[T.copy()];flux=[];ledger=[]
    for _ in range(steps):
        Q=g*np.diff(T); nxt=T.copy();nxt[1:-1]+=dt*(np.diff(Q)+S[1:-1])/C[1:-1]
        if not np.isfinite(nxt).all() or np.min(nxt)<=0:raise ValueError('nonpositive temperature')
        change=np.sum(C[1:-1].astype(np.longdouble)*(nxt[1:-1].astype(np.longdouble)-T[1:-1]))
        supply=np.longdouble(dt)*(np.longdouble(Q[-1])-Q[0]+np.sum(S[1:-1].astype(np.longdouble)))
        bound=8*np.finfo(float).eps*np.sum(C[1:-1].astype(np.longdouble)*(np.abs(T[1:-1])+np.abs(nxt[1:-1])))
        if abs(change-supply)>bound:raise ValueError('energy ledger outside roundoff bound')
        ledger.append([float(change),float(supply),float(change-supply),float(bound)])
        flux.append(Q);histories.append(nxt.copy());T=nxt
    return dict(T=T,history=np.array(histories),flux=np.array(flux),ledger=np.array(ledger),C=C,S=S,g=g,edges=edges,CFL_s=limit,dt_s=dt)
