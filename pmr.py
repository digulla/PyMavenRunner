#!pipenv run python
# -*- coding: utf-8 -*-

from pmr.ui import MainWindow

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    mainWindow = MainWindow()
    mainWindow.show()

    app.exec_()
