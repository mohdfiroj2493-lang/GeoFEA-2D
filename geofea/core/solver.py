
import numpy as np
from geofea.core.fem import assemble_K_linear
from geofea.core.materials.elastic import LinearElastic

def _apply_dirichlet(K, F, fixed):
    K=K.copy(); F=F.copy()
    for dof,val in fixed.items():
        K[dof,:]=0; K[:,dof]=0; K[dof,dof]=1; F[dof]=val
    return K,F

def solve_linear(nodes, elems, E_ksi, nu, t_in, F_ext, fixed):
    D=LinearElastic(E_ksi,nu,False).D()
    K=assemble_K_linear(nodes, elems, D, t_in)
    Kc,Fc=_apply_dirichlet(K,F_ext,fixed)
    return np.linalg.solve(Kc,Fc)
