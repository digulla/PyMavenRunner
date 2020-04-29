#!python3
# -*- coding: utf-8 -*-

from pmr.ui import QtPreferences

def test_create_qt_prefs(qtbot):
    prefs = QtPreferences()

    assert prefs.defaultTextColor is not None
