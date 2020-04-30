#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import QtPreferences, CustomPatternDialog
from pathlib import Path

rootFolder = Path(__file__).parent.parent.resolve()

def test_create_dialog(qtbot):
	project = Project(rootFolder / 'it' / 'multi-module-project')
	preferences = ProjectPreferences(project)
	preferences.load()
	qtPrefs = QtPreferences()
	dialog = CustomPatternDialog(qtPrefs, preferences.customPatternPreferences, None)

	assert [dialog.patternTable.rowCount(), dialog.testResults.model().rowCount(0)] == [6, 13]
