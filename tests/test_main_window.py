#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import MainWindow

def test_create_MainWindow(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    
