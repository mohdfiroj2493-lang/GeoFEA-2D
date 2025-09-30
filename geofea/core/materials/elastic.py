
import numpy as np
class LinearElastic:
    def __init__(self, E_ksi: float, nu: float, plane_stress: bool=False):
        self.E=E_ksi; self.nu=nu; self.plane_stress=plane_stress
    def D(self):
        E,nu=self.E,self.nu
        if self.plane_stress:
            c=E/(1-nu**2); return c*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
        else:
            c=E/((1+nu)*(1-2*nu)); return c*np.array([[1-nu,nu,0],[nu,1-nu,0],[0,0,(1-2*nu)/2]])
