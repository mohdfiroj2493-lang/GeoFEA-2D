
from __future__ import annotations
from PySide6 import QtCore
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Circle

class SketchMode: SELECT=0; POLY=1; RECT=2; CIRCLE=3

class GeometrySketcher(QtCore.QObject):
    """RS2-style interactive sketcher with SNAP/GRID/ORTHO and HUD."""
    polygonFinished = QtCore.Signal(list)

    def __init__(self, ax, snap=True, grid=12.0, show_grid=True, ortho=False):
        super().__init__()
        self.ax=ax; self.snap=snap; self.grid=grid; self.show_grid=show_grid; self.ortho=ortho
        self.mode=SketchMode.SELECT
        self._pts=[]; self._rubber=None; self._press=None; self._hud=None

        c=ax.figure.canvas
        c.setMouseTracking(True)
        c.setFocusPolicy(QtCore.Qt.StrongFocus)
        c.mpl_connect('button_press_event', self._press_ev)
        c.mpl_connect('motion_notify_event', self._move_ev)
        c.mpl_connect('button_release_event', self._release_ev)
        c.mpl_connect('key_press_event', self._key_ev)

        if show_grid: self.draw_grid()

    def on_polygon_finished(self, cb): self.polygonFinished.connect(cb)

    def set_flags(self, snap=None, grid=None, ortho=None, show_grid=None):
        if snap is not None: self.snap=snap
        if ortho is not None: self.ortho=ortho
        if show_grid is not None:
            self.show_grid=show_grid
            self.ax.clear()
            if self.show_grid: self.draw_grid()
            self.ax.figure.canvas.draw_idle()

    def set_mode(self, mode):
        self.mode=mode; self._clear_temp()
        cursor = QtCore.Qt.CrossCursor if mode in (SketchMode.POLY,SketchMode.RECT,SketchMode.CIRCLE) else QtCore.Qt.ArrowCursor
        self.ax.figure.canvas.setCursor(cursor)

    def draw_grid(self, xlim=(0, 480), ylim=(0, 300)):
        self.ax.set_xlim(*xlim); self.ax.set_ylim(*ylim); self.ax.set_aspect('equal','box')
        if not self.show_grid: return
        xs=np.arange(xlim[0], xlim[1]+self.grid, self.grid)
        ys=np.arange(ylim[0], ylim[1]+self.grid, self.grid)
        for x in xs: self.ax.axvline(x, color=(0.92,0.92,0.92), lw=0.3, zorder=0)
        for y in ys: self.ax.axhline(y, color=(0.92,0.92,0.92), lw=0.3, zorder=0)

    # ---------- events ----------
    def _snap_xy(self, x, y):
        if self.snap:
            g=self.grid; x=round(x/g)*g; y=round(y/g)*g
        if self.ortho and self._pts:
            lx,ly=self._pts[-1]
            if abs(x-lx) < abs(y-ly): x=lx
            else: y=ly
        return x,y

    def _press_ev(self, ev):
        if ev.inaxes!=self.ax: return
        x,y=self._snap_xy(ev.xdata, ev.ydata)
        if self.mode==SketchMode.POLY:
            if ev.button==1: self._pts.append((x,y)); self._update_poly((x,y))
            elif ev.button==3: self._finish_poly()
        elif self.mode==SketchMode.RECT and ev.button==1:
            self._press=(x,y); self._update_rect((x,y))
        elif self.mode==SketchMode.CIRCLE and ev.button==1:
            self._press=(x,y); self._update_circle((x,y))

    def _move_ev(self, ev):
        if ev.inaxes!=self.ax: return
        x,y=self._snap_xy(ev.xdata, ev.ydata)
        if self.mode==SketchMode.POLY and self._pts:
            self._update_poly((x,y), preview=True)
        elif self.mode==SketchMode.RECT and self._press is not None:
            self._update_rect((x,y), preview=True)
        elif self.mode==SketchMode.CIRCLE and self._press is not None:
            self._update_circle((x,y), preview=True)

    def _release_ev(self, ev):
        if ev.inaxes!=self.ax or ev.button!=1: return
        x,y=self._snap_xy(ev.xdata, ev.ydata)
        if self.mode==SketchMode.RECT and self._press is not None:
            self._update_rect((x,y)); self._emit_rect()
        elif self.mode==SketchMode.CIRCLE and self._press is not None:
            self._update_circle((x,y)); self._emit_circle()

    def _key_ev(self, ev):
        if ev.key in ('escape','esc'): self._pts.clear(); self._clear_temp()
        if self.mode==SketchMode.POLY and ev.key in ('enter','return'): self._finish_poly()

    # ---------- helpers ----------
    def _clear_temp(self):
        for art in (self._rubber, self._hud):
            if art is not None:
                try: art.remove()
                except Exception: pass
        self._rubber=None; self._hud=None; self._press=None
        self.ax.figure.canvas.draw_idle()

    def _update_poly(self, xy, preview=False):
        xs=[p[0] for p in self._pts]; ys=[p[1] for p in self._pts]
        if preview: xs=xs+[xy[0]]; ys=ys+[xy[1]]
        if self._rubber is None or not isinstance(self._rubber, Line2D):
            self._rubber=Line2D(xs, ys, linestyle='-', marker='o', color='C0'); self.ax.add_line(self._rubber)
        else:
            self._rubber.set_data(xs, ys)
        # HUD
        if self._pts:
            x0,y0=self._pts[-1]; x1,y1=xy
            L=((x1-x0)**2+(y1-y0)**2)**0.5; ang=np.degrees(np.arctan2(y1-y0, x1-x0))
            txt=f"{L/12:.2f} ft @ {ang:.1f}°"
            if self._hud is None:
                self._hud=self.ax.text((x0+x1)/2,(y0+y1)/2,txt, color='crimson', fontsize=8)
            else:
                self._hud.set_position(((x0+x1)/2,(y0+y1)/2)); self._hud.set_text(txt)
        self.ax.figure.canvas.draw_idle()

    def _update_rect(self, xy, preview=False):
        x0,y0=self._press; x1,y1=xy; x=min(x0,x1); y=min(y0,y1); w=abs(x1-x0); h=abs(y1-y0)
        if self._rubber is None or not isinstance(self._rubber, Rectangle):
            self._rubber=Rectangle((x,y), w, h, fill=False, edgecolor='C1'); self.ax.add_patch(self._rubber)
        else:
            self._rubber.set_xy((x,y)); self._rubber.set_width(w); self._rubber.set_height(h)
        self.ax.figure.canvas.draw_idle()

    def _update_circle(self, xy, preview=False):
        x0,y0=self._press; x1,y1=xy; r=((x1-x0)**2+(y1-y0)**2)**0.5
        if self._rubber is None or not isinstance(self._rubber, Circle):
            self._rubber=Circle((x0,y0), r, fill=False, edgecolor='C2'); self.ax.add_patch(self._rubber)
        else:
            self._rubber.center=(x0,y0); self._rubber.set_radius(r)
        self.ax.figure.canvas.draw_idle()

    def _finish_poly(self):
        if len(self._pts)>=3:
            self.polygonFinished.emit(list(self._pts))
        self._pts.clear(); self._clear_temp()

    def _emit_rect(self):
        x,y=self._rubber.get_xy(); w=self._rubber.get_width(); h=self._rubber.get_height()
        self.polygonFinished.emit([(x,y),(x+w,y),(x+w,y+h),(x,y+h)])
        self._clear_temp()

    def _emit_circle(self):
        x0,y0=self._press; r=self._rubber.get_radius()
        th=np.linspace(0,2*np.pi,64,endpoint=False)
        self.polygonFinished.emit([(x0+r*np.cos(t), y0+r*np.sin(t)) for t in th])
        self._clear_temp()
