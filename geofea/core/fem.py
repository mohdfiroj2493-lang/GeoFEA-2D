
import numpy as np

def tri_B_matrix(xy):
    x1,y1=xy[0]; x2,y2=xy[1]; x3,y3=xy[2]
    A=0.5*((x2-x1)*(y3-y1)-(x3-x1)*(y2-y1))
    if np.isclose(A,0): raise ValueError('Degenerate triangle')
    b1=y2-y3; b2=y3-y1; b3=y1-y2
    c1=x3-x2; c2=x1-x3; c3=x2-x1
    B=(1/(2*A))*np.array([[b1,0,b2,0,b3,0],[0,c1,0,c2,0,c3],[c1,b1,c2,b2,c3,b3]])
    return B, abs(A)

def assemble_K_linear(nodes, elems, D, t_in):
    n=nodes.shape[0]; K=np.zeros((2*n,2*n))
    for tri in elems:
        xy=nodes[tri]; B,A=tri_B_matrix(xy); ke=t_in*A*(B.T@D@B)
        dof=[2*tri[0],2*tri[0]+1,2*tri[1],2*tri[1]+1,2*tri[2],2*tri[2]+1]
        for i in range(6):
            for j in range(6):
                K[dof[i],dof[j]]+=ke[i,j]
    return K

def strain_from_u(nodes, tri, u):
    xy=nodes[tri]; B,A=tri_B_matrix(xy)
    dof=[2*tri[0],2*tri[0]+1,2*tri[1],2*tri[1]+1,2*tri[2],2*tri[2]+1]
    ue=u[dof]; eps=B@ue; return eps, B, A
