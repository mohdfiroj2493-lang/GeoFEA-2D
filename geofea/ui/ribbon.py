
from PySide6 import QtWidgets

class Ribbon(QtWidgets.QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setTabPosition(QtWidgets.QTabWidget.North)
        self.setDocumentMode(True)
        self.pages = {}
        for name in ["Geometry","Materials & Staging","Loading","Mesh","Support","Groundwater","Restraints"]:
            w = QtWidgets.QWidget()
            l = QtWidgets.QHBoxLayout(w)
            l.setContentsMargins(6,6,6,6)
            l.addStretch(1)
            self.addTab(w, name)
            self.pages[name]=l
    def page(self, name): return self.pages[name]
