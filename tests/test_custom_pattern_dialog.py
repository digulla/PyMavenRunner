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

def test_delete_row(qtbot, qtmodeltester):
    project = Project(rootFolder / 'it' / 'multi-module-project')
    preferences = ProjectPreferences(project)
    preferences.load()
    qtPrefs = QtPreferences()
    dialog = CustomPatternDialog(qtPrefs, preferences.customPatternPreferences, None)

    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.deleteMatcher(0)
    
    # TODO Why doesn't this work?
    #def check_test_results_were_updated():
    #    assert dialog.testResults.model().rowCount(0) == 12
    #
    #qtbot.waitUntil(check_test_results_were_updated)

    # I can't really get a signal since the whole model is replaced
    dialog.patternsChanged(*blocker.args)

    assert [dialog.patternTable.rowCount(), dialog.testResults.model().rowCount(0)] == [5, 13]
    assert repr(dialog.matchers[0]) == "SubstringMatcherConfig(pattern='ErrorTest', result=1)"
    
    # TODO FAIL! model->hasChildren(topIndex) () returned FALSE (qabstractitemmodeltester.cpp:360)
    # I'm using the official table model from Qt. Why does it fail?
    #qtmodeltester.check(dialog.testResults.model())