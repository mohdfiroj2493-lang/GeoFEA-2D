
import numpy as np

def mesh_polygon(vertices, max_area=None, quality=30):
    """Constrained Delaunay via `triangle` if available; structured fallback otherwise."""
    try:
        import triangle as tr
    except Exception:
        tr = None
    poly = np.array(vertices, dtype=float)
    if tr is None:
        # Fallback: structured mesh + inside cull
        x0,y0 = poly.min(axis=0); x1,y1 = poly.max(axis=0)
        nx=ny=60
        xs=np.linspace(x0,x1,nx+1); ys=np.linspace(y0,y1,ny+1)
        X,Y=np.meshgrid(xs,ys); nodes=np.column_stack([X.ravel(),Y.ravel()])
        def nid(i,j): return j*(nx+1)+i
        elems=[]
        for j in range(ny):
            for i in range(nx):
                n1=nid(i,j); n2=nid(i+1,j); n3=nid(i,j+1); n4=nid(i+1,j+1)
                elems.append([n1,n2,n4]); elems.append([n1,n4,n3])
        from matplotlib.path import Path
        P=Path(poly); cent=nodes[np.array(elems)].mean(axis=1)
        mask=P.contains_points(cent)
        tris=np.array(elems, dtype=int)[mask]
        return nodes, tris
    # Triangle path
    n=len(poly)
    segs=np.column_stack([np.arange(n), np.roll(np.arange(n), -1)])
    A={'vertices':poly, 'segments':segs}
    opts='pq'
    if max_area is not None: opts+=f'a{float(max_area)}'
    T=tr.triangulate(A, opts)
    return T['vertices'], T['triangles']
