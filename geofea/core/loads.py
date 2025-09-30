
import numpy as np

def boundary_edges(elems):
    from collections import defaultdict
    count = defaultdict(int)
    for tri in elems:
        for a,b in [(tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])]:
            a2,b2=(a,b) if a<b else (b,a); count[(a2,b2)]+=1
    return np.array([k for k,v in count.items() if v==1], dtype=int)

def point_to_segment_distance(p,a,b):
    ap=p-a; ab=b-a; ab2=ab.dot(ab)+1e-30; t=max(0,min(1,ap.dot(ab)/ab2)); proj=a+t*ab; return float(np.linalg.norm(p-proj))

def edges_near_polyline(nodes, edges, polyline, tol_in=2.0):
    if len(polyline)<2: return np.array([],dtype=int)
    P=np.array(polyline,float); mids=(nodes[edges[:,0]]+nodes[edges[:,1]])/2.0; sel=[]
    for i,m in enumerate(mids):
        dmin=1e18
        for j in range(len(P)-1):
            a=P[j]; b=P[j+1]; d=point_to_segment_distance(m,a,b); dmin=min(dmin,d)
        if dmin<=tol_in: sel.append(i)
    return np.array(sel,dtype=int)

def assemble_line_traction(nodes, edges, edges_idx, tx_kip_ft, ty_kip_ft):
    qx=tx_kip_ft/12.0; qy=ty_kip_ft/12.0  # kip/ft -> kip/in
    F=np.zeros(2*nodes.shape[0])
    for i in edges_idx:
        a,b=edges[i]; pa=nodes[a]; pb=nodes[b]; L=float(np.linalg.norm(pb-pa))
        Fx=qx*L/2.0; Fy=qy*L/2.0
        F[2*a]+=Fx; F[2*b]+=Fx; F[2*a+1]+=Fy; F[2*b+1]+=Fy
    return F

def assemble_point_load(nodes, pt, Fx_kip, Fy_kip):
    dif=nodes-np.array(pt,float); i=int(np.argmin(np.sum(dif*dif,axis=1)))
    F=np.zeros(2*nodes.shape[0]); F[2*i]+=Fx_kip; F[2*i+1]+=Fy_kip
    return F,i
