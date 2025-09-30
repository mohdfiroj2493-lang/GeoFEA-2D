
from PySide6 import QtCore, QtWidgets

class ModelTree(QtWidgets.QTreeWidget):
    def __init__(self):
        super().__init__()
        self.setHeaderHidden(True)
        self.boundaries = QtWidgets.QTreeWidgetItem(self, ["Boundaries"])
        self.external   = QtWidgets.QTreeWidgetItem(self.boundaries, ["External"])
        self.materials  = QtWidgets.QTreeWidgetItem(self, ["Materials"])
        self.loading    = QtWidgets.QTreeWidgetItem(self, ["Loading"])
        self.expandAll()
    def add_region(self, name): QtWidgets.QTreeWidgetItem(self.external,[name]); self.expandAll()
    def add_load(self, desc):  QtWidgets.QTreeWidgetItem(self.loading,[desc]); self.expandAll()

class DisplayOptions(QtWidgets.QWidget):
    toggled = QtCore.Signal(dict)
    def __init__(self):
        super().__init__()
        self.chk_nodes = QtWidgets.QCheckBox("Node Numbers")
        self.chk_elems = QtWidgets.QCheckBox("Element Numbers")
        self.chk_mesh  = QtWidgets.QCheckBox("Discretizations with mesh"); self.chk_mesh.setChecked(True)
        lay=QtWidgets.QVBoxLayout(self)
        lay.addWidget(self.chk_nodes); lay.addWidget(self.chk_elems); lay.addWidget(self.chk_mesh); lay.addStretch(1)
        for c in (self.chk_nodes,self.chk_elems,self.chk_mesh): c.stateChanged.connect(self._emit)
    def _emit(self,*_):
        self.toggled.emit({"nodes":self.chk_nodes.isChecked(),"elems":self.chk_elems.isChecked(),"mesh":self.chk_mesh.isChecked()})
