#!pipenv run python
# -*- coding: utf-8 -*-

from pmr.ui import MainWindow
import pmr

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication

    app = QApplication(sys.argv)
    QCoreApplication.setOrganizationName('de.pdark')
    QCoreApplication.setApplicationName('PyMavenRunner')
    QCoreApplication.setApplicationVersion(pmr.VERSION)

    mainWindow = MainWindow(app)
    mainWindow.show()

    app.exec_()
