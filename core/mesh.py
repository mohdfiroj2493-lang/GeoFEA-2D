
# geofea/core/mesh.py
from __future__ import annotations
import numpy as np
from dataclasses import dataclass

@dataclass
class Mesh:
    nodes: np.ndarray  # (N,2) in inches
    elems: np.ndarray  # (M,3) triangle indices (0-based)

def rect_mesh_imperial(nx:int, ny:int, Lx_in:float, Ly_in:float, x0_in:float=0.0, y0_in:float=0.0) -> Mesh:
    xs = np.linspace(x0_in, x0_in+Lx_in, nx+1)
    ys = np.linspace(y0_in, y0_in+Ly_in, ny+1)
    X, Y = np.meshgrid(xs, ys)
    nodes = np.column_stack([X.ravel(), Y.ravel()]).astype(float)

    def nid(i,j): return j*(nx+1)+i

    elems = []
    for j in range(ny):
        for i in range(nx):
            n1 = nid(i, j)
            n2 = nid(i+1, j)
            n3 = nid(i, j+1)
            n4 = nid(i+1, j+1)
            elems.append([n1, n2, n4])
            elems.append([n1, n4, n3])
    return Mesh(nodes=nodes, elems=np.array(elems, dtype=int))
