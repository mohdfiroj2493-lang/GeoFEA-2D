
from PySide6 import QtWidgets
from geofea.ui.main_window import MainWindow
if __name__ == '__main__':
    app = QtWidgets.QApplication([])
    w = MainWindow()
    w.show()
    app.exec()
