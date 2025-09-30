
from __future__ import annotations
from PySide6 import QtCore
from matplotlib.lines import Line2D

class LoadSketchMode: NONE=0; LINE=1; POINT=2

class LoadSketcher(QtCore.QObject):
    def __init__(self, ax, snap=True, grid=12.0):
        super().__init__(); self.ax=ax; self.snap=snap; self.grid=grid
        self.mode=LoadSketchMode.NONE; self._pts=[]; self._rubber=None
        c=ax.figure.canvas
        c.mpl_connect('button_press_event', self._press)
        c.mpl_connect('motion_notify_event', self._move)
        c.mpl_connect('key_press_event', self._key)
    def set_mode(self, m): self.mode=m; self._clear()
    def on_line_finished(self, cb): self._line_cb=cb
    def on_point_finished(self, cb): self._pt_cb=cb
    def _snap(self,x,y): 
        return (round(x/self.grid)*self.grid, round(y/self.grid)*self.grid) if self.snap else (x,y)
    def _press(self, e):
        if e.inaxes!=self.ax: return
        x,y=self._snap(e.xdata,e.ydata)
        if self.mode==LoadSketchMode.LINE:
            if e.button==1: self._pts.append((x,y)); self._update((x,y))
            elif e.button==3 and len(self._pts)>=2:
                if hasattr(self,'_line_cb'): self._line_cb(list(self._pts)); self._pts=[]; self._clear()
        elif self.mode==LoadSketchMode.POINT and e.button==1:
            if hasattr(self,'_pt_cb'): self._pt_cb((x,y))
    def _move(self, e):
        if e.inaxes!=self.ax or self.mode!=LoadSketchMode.LINE or not self._pts: return
        x,y=self._snap(e.xdata,e.ydata); self._update((x,y),True)
    def _key(self, e):
        if e.key in ('escape','esc'): self._pts=[]; self._clear()
        if self.mode==LoadSketchMode.LINE and e.key in ('enter','return') and len(self._pts)>=2:
            if hasattr(self,'_line_cb'): self._line_cb(list(self._pts)); self._pts=[]; self._clear()
    def _clear(self):
        if self._rubber is not None:
            try: self._rubber.remove()
            except Exception: pass
        self._rubber=None; self.ax.figure.canvas.draw_idle()
    def _update(self, xy, preview=False):
        xs=[p[0] for p in self._pts]; ys=[p[1] for p in self._pts]
        if preview: xs=xs+[xy[0]]; ys=ys+[xy[1]]
        if self._rubber is None or not isinstance(self._rubber, Line2D):
            self._rubber=Line2D(xs,ys,linestyle='-',marker='o',color='crimson'); self.ax.add_line(self._rubber)
        else: self._rubber.set_data(xs,ys)
        self.ax.figure.canvas.draw_idle()
