
from PySide6 import QtCore, QtWidgets
import numpy as np, matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas

from geofea.core.geometry import GeometryModel
from geofea.core.mesher_triangle import mesh_polygon
from geofea.core.loads import boundary_edges, edges_near_polyline, assemble_line_traction, assemble_point_load
from geofea.core.solver import solve_linear
from geofea.ui.geom_draw_tool import GeometrySketcher, SketchMode
from geofea.ui.load_tool import LoadSketcher, LoadSketchMode
from geofea.ui.ribbon import Ribbon
from geofea.ui.panels import ModelTree, DisplayOptions

class MplCanvas(FigureCanvas):
    def __init__(self):
        fig = plt.Figure()
        super().__init__(fig)
        self.ax = fig.add_subplot(111)
        self.ax.set_aspect('equal','box')

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('GeoFEA — RS2-style UI')
        self.resize(1700, 1000)

        # Central canvas
        self.canvas = MplCanvas()
        self.setCentralWidget(self.canvas)

        # Initialize workspace (inches)
        self.canvas.ax.clear()
        self.canvas.ax.set_aspect('equal','box')
        self.canvas.ax.set_title('CAD View')

        # Ribbon
        self.ribbon = Ribbon()
        tb = QtWidgets.QToolBar(); tb.setMovable(False); tb.addWidget(self.ribbon)
        self.addToolBar(QtCore.Qt.TopToolBarArea, tb)

        # Left docks
        self.tree = ModelTree(); dock_tree = QtWidgets.QDockWidget('Model Items'); dock_tree.setWidget(self.tree)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_tree)
        self.disp = DisplayOptions(); dock_disp = QtWidgets.QDockWidget('Display Options'); dock_disp.setWidget(self.disp)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, dock_disp)
        self.tabifyDockWidget(dock_tree, dock_disp); dock_tree.raise_()

        # Status toggles
        self.chk_snap  = QtWidgets.QCheckBox('SNAP');  self.chk_snap.setChecked(True)
        self.chk_grid  = QtWidgets.QCheckBox('GRID');  self.chk_grid.setChecked(True)
        self.chk_ortho = QtWidgets.QCheckBox('ORTHO')
        self.chk_osnap = QtWidgets.QCheckBox('OSNAP')
        for w in (self.chk_snap,self.chk_grid,self.chk_ortho,self.chk_osnap):
            w.stateChanged.connect(self._update_flags)
            self.statusBar().addPermanentWidget(w)
        self.lbl_xy = QtWidgets.QLabel(''); self.statusBar().addPermanentWidget(self.lbl_xy)

        # Model & tools
        self.geom = GeometryModel(); self.nodes=None; self.elems=None; self.loads=[]
        self.gsk = GeometrySketcher(self.canvas.ax, snap=True, grid=12.0, show_grid=True, ortho=False)
        self.gsk.on_polygon_finished(self._poly_done)
        self.lsk = LoadSketcher(self.canvas.ax, snap=True, grid=12.0); self.lsk.on_line_finished(self._line_done); self.lsk.on_point_finished(self._point_done)
        self.canvas.mpl_connect('motion_notify_event', self._mouse_xy)

        # Ribbon content
        self._setup_geometry_page(); self._setup_loading_page(); self._setup_mesh_page()
        self._update_flags(); self._redraw()

    # -------- Ribbon pages --------
    def _setup_geometry_page(self):
        L = self.ribbon.page('Geometry')
        btn_poly = QtWidgets.QPushButton('Polygon'); btn_poly.clicked.connect(lambda: self._set_geom_mode(SketchMode.POLY))
        btn_rect = QtWidgets.QPushButton('Rectangle'); btn_rect.clicked.connect(lambda: self._set_geom_mode(SketchMode.RECT))
        btn_circle = QtWidgets.QPushButton('Circle'); btn_circle.clicked.connect(lambda: self._set_geom_mode(SketchMode.CIRCLE))
        for w in (btn_poly, btn_rect, btn_circle): L.insertWidget(0, w)

    def _setup_loading_page(self):
        L = self.ribbon.page('Loading')
        self.tx = QtWidgets.QDoubleSpinBox(); self.tx.setRange(-1e6,1e6); self.tx.setSuffix(' kip/ft'); self.tx.setValue(1.0)
        self.ty = QtWidgets.QDoubleSpinBox(); self.ty.setRange(-1e6,1e6); self.ty.setSuffix(' kip/ft'); self.ty.setValue(0.0)
        self.Fx = QtWidgets.QDoubleSpinBox(); self.Fx.setRange(-1e6,1e6); self.Fx.setSuffix(' kip'); self.Fx.setValue(0.0)
        self.Fy = QtWidgets.QDoubleSpinBox(); self.Fy.setRange(-1e6,1e6); self.Fy.setSuffix(' kip'); self.Fy.setValue(-1.0)
        btn_line = QtWidgets.QPushButton('Line load'); btn_line.clicked.connect(lambda: self._set_load_mode(LoadSketchMode.LINE))
        btn_point = QtWidgets.QPushButton('Point load'); btn_point.clicked.connect(lambda: self._set_load_mode(LoadSketchMode.POINT))
        for w in (btn_line, QtWidgets.QLabel('τx:'), self.tx, QtWidgets.QLabel('τy:'), self.ty,
                  btn_point, QtWidgets.QLabel('Fx:'), self.Fx, QtWidgets.QLabel('Fy:'), self.Fy):
            L.insertWidget(0, w)

    def _setup_mesh_page(self):
        L = self.ribbon.page('Mesh')
        self.max_area = QtWidgets.QDoubleSpinBox(); self.max_area.setRange(1e-3,1e9); self.max_area.setValue(25.0)
        btn_mesh = QtWidgets.QPushButton('Generate mesh'); btn_mesh.clicked.connect(self.mesh_model)
        btn_solve = QtWidgets.QPushButton('Solve'); btn_solve.clicked.connect(self.solve_model)
        for w in (QtWidgets.QLabel('Max area (in²):'), self.max_area, btn_mesh, btn_solve): L.insertWidget(0, w)

    # -------- Modes & flags --------
    def _set_geom_mode(self, m): self.gsk.set_mode(m); self.lsk.set_mode(LoadSketchMode.NONE)
    def _set_load_mode(self, m): self.lsk.set_mode(m); self.gsk.set_mode(SketchMode.SELECT)
    def _update_flags(self):
        self.gsk.set_flags(snap=self.chk_snap.isChecked(), show_grid=self.chk_grid.isChecked(), ortho=self.chk_ortho.isChecked())
        self.lsk.snap = self.chk_snap.isChecked()
        self._redraw()

    # -------- Sketch callbacks --------
    def _poly_done(self, pts):
        name=f'Region{len(self.geom.regions)+1}'; self.geom.add_polygon(name, pts, material='Elastic')
        self.tree.add_region(name); self._redraw(overdraw_loads=True); self._fit_view(); self.canvas.draw()

    def _line_done(self, pts):
        self.loads.append({'type':'line','poly':pts,'tx':self.tx.value(),'ty':self.ty.value()})
        self.tree.add_load(f'Line: {len(pts)} pts'); self._redraw(overdraw_loads=True)

    def _point_done(self, pt):
        self.loads.append({'type':'point','pt':pt,'Fx':self.Fx.value(),'Fy':self.Fy.value()})
        self.tree.add_load(f'Point: {pt[0]:.1f},{pt[1]:.1f}'); self._redraw(overdraw_loads=True)

    # -------- View helpers --------
    def _mouse_xy(self, e):
        if e.inaxes==self.canvas.ax: self.statusBar().showMessage(f'{e.xdata:8.3f}, {e.ydata:8.3f}')

    def _fit_view(self, margin=24.0):
        xs=[]; ys=[]
        for r in self.geom.regions:
            xs += [p[0] for p in r.outer]; ys += [p[1] for p in r.outer]
        if xs and ys:
            x0,x1=min(xs)-margin, max(xs)+margin
            y0,y1=min(ys)-margin, max(ys)+margin
            self.canvas.ax.set_xlim(x0,x1); self.canvas.ax.set_ylim(y0,y1)

    def _redraw(self, overdraw_loads=False):
        ax=self.canvas.ax; ax.clear()
        for r in self.geom.regions:
            pts=r.outer+[r.outer[0]]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color='purple', lw=1.5)
        if self.nodes is not None:
            for tri in self.elems:
                xy=self.nodes[tri]
                ax.plot([xy[0,0],xy[1,0],xy[2,0],xy[0,0]], [xy[0,1],xy[1,1],xy[2,1],xy[0,1]], '-', lw=0.25, color='0.4')
        if overdraw_loads or self.nodes is None:
            for L in self.loads:
                if L['type']=='line':
                    xs=[p[0] for p in L['poly']]; ys=[p[1] for p in L['poly']]
                    ax.plot(xs, ys, '-o', color='crimson', lw=1.2)
                else:
                    ax.plot([L['pt'][0]],[L['pt'][1]], marker='v', color='crimson')
        ax.set_title('CAD View'); self.canvas.draw()

    # -------- Mesh & Solve --------
    def mesh_model(self):
        if not self.geom.regions:
            QtWidgets.QMessageBox.warning(self,'Mesh','Draw a region first.'); return
        poly=self.geom.regions[0].outer
        self.nodes, self.elems = mesh_polygon(poly, max_area=self.max_area.value(), quality=30)
        self._redraw(); self._fit_view(); self.canvas.draw()

    def solve_model(self):
        if self.nodes is None: self.mesh_model()
        F=np.zeros(2*self.nodes.shape[0]); edges=boundary_edges(self.elems)
        for L in self.loads:
            if L['type']=='line':
                idx=edges_near_polyline(self.nodes, edges, L['poly'], tol_in=3.0)
                F+=assemble_line_traction(self.nodes, edges, idx, L['tx'], L['ty'])
            else:
                Fp,_=assemble_point_load(self.nodes, L['pt'], L['Fx'], L['Fy']); F+=Fp
        fixed={}; x=self.nodes[:,0]; y=self.nodes[:,1]
        for n in np.where(np.isclose(y,y.min()))[0]: fixed[2*n+1]=0.0
        for n in np.where(np.isclose(x,x.min()))[0]: fixed[2*n]=0.0
        u=solve_linear(self.nodes, self.elems, 30.0, 0.2, 1.0, F, fixed)
        scale=30.0; def_nodes=self.nodes+scale*u.reshape(-1,2)
        self._redraw()
        for tri in self.elems:
            xy=def_nodes[tri]; self.canvas.ax.fill(xy[:,0],xy[:,1], alpha=0.4, color='C0')
        self.canvas.draw()
