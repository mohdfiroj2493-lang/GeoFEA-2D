
# geofea/ui/main_window.py
from __future__ import annotations
from PySide6 import QtCore, QtGui, QtWidgets
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from geofea.core.units import ft_to_in, kip_per_ft_to_kip_per_in
from geofea.core.mesh import rect_mesh_imperial
from geofea.core.fem import assemble_K, apply_dirichlet
from geofea.core.materials.elastic import LinearElastic

class MplCanvas(FigureCanvas):
    def __init__(self):
        self.fig = plt.Figure()
        super().__init__(self.fig)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_aspect('equal', adjustable='box')

    def clear(self):
        self.ax.clear()
        self.ax.set_aspect('equal', adjustable='box')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GeoFEA-2D — Imperial (MVP)")
        self.resize(1200, 800)

        self.canvas = MplCanvas()
        self.setCentralWidget(self.canvas)

        self._build_inspector()
        self._build_toolbar()

        self.nodes = None; self.elems = None
        self.u = None

        self.draw_geometry()

    def _build_toolbar(self):
        tb = self.addToolBar("Main")
        a_mesh = QtGui.QAction("Mesh", self); a_mesh.triggered.connect(self.generate_mesh)
        a_solve = QtGui.QAction("Solve", self); a_solve.triggered.connect(self.solve)
        tb.addAction(a_mesh); tb.addAction(a_solve)

    def _build_inspector(self):
        dock = QtWidgets.QDockWidget("Inspector", self)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
        w = QtWidgets.QWidget(); f = QtWidgets.QFormLayout(w)

        # Geometry in feet (imperial UI)
        self.Lx_ft = QtWidgets.QDoubleSpinBox(); self.Lx_ft.setRange(0.1, 1e5); self.Lx_ft.setValue(10.0)
        self.Ly_ft = QtWidgets.QDoubleSpinBox(); self.Ly_ft.setRange(0.1, 1e5); self.Ly_ft.setValue(5.0)
        self.nx = QtWidgets.QSpinBox(); self.nx.setRange(1, 500); self.nx.setValue(40)
        self.ny = QtWidgets.QSpinBox(); self.ny.setRange(1, 500); self.ny.setValue(20)

        # Material in ksi (kip/in^2)
        self.E_ksi = QtWidgets.QDoubleSpinBox(); self.E_ksi.setRange(0.001, 5e3); self.E_ksi.setValue(30.0)
        self.nu = QtWidgets.QDoubleSpinBox(); self.nu.setRange(0.0, 0.49); self.nu.setSingleStep(0.01); self.nu.setValue(0.2)
        self.t_in = QtWidgets.QDoubleSpinBox(); self.t_in.setRange(0.001, 100.0); self.t_in.setValue(1.0)
        self.cb_plane = QtWidgets.QComboBox(); self.cb_plane.addItems(["Plane stress","Plane strain"]); self.cb_plane.setCurrentIndex(1)

        # BCs per edge (roller/fixed/free)
        def mkbc(): cb = QtWidgets.QComboBox(); cb.addItems(["free","roller","fixed"]); return cb
        self.bc_left = mkbc(); self.bc_right = mkbc(); self.bc_bottom = mkbc(); self.bc_top = mkbc()
        self.bc_bottom.setCurrentText("fixed")
        self.bc_left.setCurrentText("roller")

        # Traction on right edge in kip/ft (converted to kip/in)
        self.tr_on = QtWidgets.QCheckBox("Traction on Right")
        self.tx_kip_per_ft = QtWidgets.QDoubleSpinBox(); self.tx_kip_per_ft.setRange(-1e6, 1e6); self.tx_kip_per_ft.setValue(1.0)
        self.ty_kip_per_ft = QtWidgets.QDoubleSpinBox(); self.ty_kip_per_ft.setRange(-1e6, 1e6); self.ty_kip_per_ft.setValue(0.0)

        # Buttons
        btn_mesh = QtWidgets.QPushButton("Generate Mesh"); btn_mesh.clicked.connect(self.generate_mesh)
        btn_solve = QtWidgets.QPushButton("Solve"); btn_solve.clicked.connect(self.solve)

        f.addRow("Length Lx (ft)", self.Lx_ft)
        f.addRow("Height Ly (ft)", self.Ly_ft)
        f.addRow("Mesh nx", self.nx); f.addRow("Mesh ny", self.ny)
        f.addRow("E (ksi)", self.E_ksi); f.addRow("nu", self.nu); f.addRow("Thickness t (in)", self.t_in)
        f.addRow("Kinematics", self.cb_plane)
        f.addRow("Left BC", self.bc_left); f.addRow("Right BC", self.bc_right)
        f.addRow("Bottom BC", self.bc_bottom); f.addRow("Top BC", self.bc_top)
        f.addRow(self.tr_on)
        f.addRow("σx (kip/ft)", self.tx_kip_per_ft); f.addRow("σy (kip/ft)", self.ty_kip_per_ft)
        f.addRow(btn_mesh); f.addRow(btn_solve)
        dock.setWidget(w)

    def draw_geometry(self):
        self.canvas.clear()
        Lx_in = ft_to_in(self.Lx_ft.value()); Ly_in = ft_to_in(self.Ly_ft.value())
        self.canvas.ax.plot([0,Lx_in,Lx_in,0,0], [0,0,Ly_in,Ly_in,0], "-")
        self.canvas.ax.set_title("Geometry (in)")
        self.canvas.ax.set_xlabel("x (in)"); self.canvas.ax.set_ylabel("y (in)")
        self.canvas.ax.autoscale(); self.canvas.draw()

    def generate_mesh(self):
        Lx_in = ft_to_in(self.Lx_ft.value()); Ly_in = ft_to_in(self.Ly_ft.value())
        m = rect_mesh_imperial(int(self.nx.value()), int(self.ny.value()), Lx_in, Ly_in, 0.0, 0.0)
        self.nodes, self.elems = m.nodes, m.elems

        self.canvas.clear()
        for tri in self.elems:
            xy = self.nodes[tri]
            self.canvas.ax.fill(xy[[0,1,2,0],0], xy[[0,1,2,0],1], fill=False, linewidth=0.2)
        self.canvas.ax.set_title("Mesh")
        self.canvas.ax.set_xlabel("x (in)"); self.canvas.ax.set_ylabel("y (in)")
        self.canvas.ax.autoscale(); self.canvas.draw()

    def _edge_node_indices(self, side:str):
        x = self.nodes[:,0]; y = self.nodes[:,1]
        Lx_in = ft_to_in(self.Lx_ft.value()); Ly_in = ft_to_in(self.Ly_ft.value())
        if side=='left': return np.where(np.isclose(x, 0.0))[0]
        if side=='right': return np.where(np.isclose(x, Lx_in))[0]
        if side=='bottom': return np.where(np.isclose(y, 0.0))[0]
        if side=='top': return np.where(np.isclose(y, Ly_in))[0]
        return np.array([], dtype=int)

    def solve(self):
        if self.nodes is None: self.generate_mesh()
        # Material
        mat = LinearElastic(self.E_ksi.value(), self.nu.value(), plane_stress=(self.cb_plane.currentIndex()==0))
        D = mat.D()

        # Assemble
        K = assemble_K(self.nodes, self.elems, D, float(self.t_in.value()))
        F = np.zeros(2*self.nodes.shape[0])

        # Traction on right edge: inputs in kip/ft -> nodal forces kip
        if self.tr_on.isChecked():
            seg_len_in = ft_to_in(self.Ly_ft.value()) / float(self.ny.value())
            fx = kip_per_ft_to_kip_per_in(self.tx_kip_per_ft.value()) * seg_len_in / 2.0
            fy = kip_per_ft_to_kip_per_in(self.ty_kip_per_ft.value()) * seg_len_in / 2.0
            idx = self._edge_node_indices('right')
            srt = idx[np.argsort(self.nodes[idx,1])]
            for i in range(len(srt)-1):
                a,b = srt[i], srt[i+1]
                F[2*a] += fx; F[2*a+1] += fy
                F[2*b] += fx; F[2*b+1] += fy

        # Dirichlet BCs
        fixed = {}
        def apply_side(side, mode):
            idx = self._edge_node_indices(side)
            for n in idx:
                if mode=='fixed':
                    fixed[2*n]=0.0; fixed[2*n+1]=0.0
                elif mode=='roller':
                    if side in ('left','right'): fixed[2*n]=0.0
                    else: fixed[2*n+1]=0.0
        apply_side('left', self.bc_left.currentText())
        apply_side('right', self.bc_right.currentText())
        apply_side('bottom', self.bc_bottom.currentText())
        apply_side('top', self.bc_top.currentText())
        if len(fixed)==0: fixed[0]=0.0; fixed[1]=0.0

        from geofea.core.fem import apply_dirichlet
        Kc, Fc = apply_dirichlet(K, F, fixed)

        # Solve
        u = np.linalg.solve(Kc, Fc)
        self.u = u

        # Plot deformed
        self.canvas.clear()
        for tri in self.elems:
            xy = self.nodes[tri]
            self.canvas.ax.fill(xy[[0,1,2,0],0], xy[[0,1,2,0],1], fill=False, linewidth=0.2)
        scale = 100.0
        def_nodes = self.nodes + scale * u.reshape(-1,2)
        vmin, vmax = 0.0, 1.0
        for tri in self.elems:
            xy = def_nodes[tri]
            poly = plt.Polygon(xy, closed=True, fill=True, alpha=0.5)
            self.canvas.ax.add_patch(poly)
        self.canvas.ax.set_title(f'Deformed (scale {scale:g})')
        self.canvas.ax.set_xlabel("x (in)"); self.canvas.ax.set_ylabel("y (in)")
        self.canvas.ax.autoscale(); self.canvas.draw()

        max_u = float(np.linalg.norm(u.reshape(-1,2), axis=1).max())
        self.statusBar().showMessage(f"Solved. Max |u| = {max_u:.3e} in.")
