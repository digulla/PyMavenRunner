#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import (
    CustomPatternDebugTableModel,
    CustomPatternDialog,
    QtPreferences,
    TextHighlighter,
)
from pathlib import Path
import re
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QFontDatabase, QColor
from PyQt5.QtCore import Qt

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

def createTestModel(qapp):
    qtPrefs = QtPreferences()
    style = qapp.style()
    matcher = SubstringMatcher('oo', LogLevelStrategy.INFO)
    results = [
        LogLevelDebugResult('foo', matcher, matcher.result, 1, 3)
    ]
    return CustomPatternDebugTableModel(qtPrefs, style, results)

def getDataForRow(model, role, row=0):
    return list(
        model.data(
            model.createIndex(0, i),
            role
        )
        for i in range(model.columnCount(0))
    )

def test_CustomPatternDebugTableModel_DisplayRole(qtbot, qapp):
    model = createTestModel(qapp)
    actual = getDataForRow(model, Qt.DisplayRole)
    
    assert actual == [
        'INFO',
        'foo',
        "SubstringMatcher('oo', 2)"
    ]
    
def test_CustomPatternDebugTableModel_ForegroundRole(qtbot, qapp):
    model = createTestModel(qapp)
    
    expected = [
        model.colors[LogLevelStrategy.INFO],
        None,
        None,
    ]
    
    actual = getDataForRow(model, Qt.ForegroundRole)
    assert actual == expected
    actual = getDataForRow(model, Qt.DecorationRole)
    assert actual == expected

def toHtml(highlighter):
    result = highlighter.doc.toHtml()
    pos = result.index('<span ')
    pos2 = result.index('</p>')
    result = result[pos:pos2]
    
    result = re.sub(r'\s+font-family:["\'][^"\']+["\'];', '', result)
    result = result.replace(' style=""', '')
    return result

def test_highlighter_apply_highlight_middle(qtbot):
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    tool = TextHighlighter(font)
    
    matcher = SubstringMatcher('oo', LogLevelStrategy.INFO)
    item = LogLevelDebugResult('foobar', matcher, matcher.result, 1, 3)

    tool.setText(item.line)
    tool.apply_highlight(item, QColor(Qt.white), QColor(Qt.black))
    
    actual = toHtml(tool)
    assert actual == '<span>f</span><span style=" color:#ffffff; background-color:#000000;">oo</span><span>bar</span>'

def test_highlighter_apply_highlight_start(qtbot):
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    tool = TextHighlighter(font)
    
    matcher = SubstringMatcher('fo', LogLevelStrategy.INFO)
    item = LogLevelDebugResult('foo', matcher, matcher.result, 0, 2)

    tool.setText(item.line)
    tool.apply_highlight(item, QColor(Qt.white), QColor(Qt.black))
    
    actual = toHtml(tool)
    assert actual == '<span style=" color:#ffffff; background-color:#000000;">fo</span><span>o</span>'

def test_highlighter_apply_highlight_end(qtbot):
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    tool = TextHighlighter(font)
    
    matcher = SubstringMatcher('oo', LogLevelStrategy.INFO)
    item = LogLevelDebugResult('foo', matcher, matcher.result, 1, 3)

    tool.setText(item.line)
    tool.apply_highlight(item, QColor(Qt.white), QColor(Qt.black))
    
    actual = toHtml(tool)
    assert actual == '<span>f</span><span style=" color:#ffffff; background-color:#000000;">oo</span>'

def test_highlighter_apply_highlight_full(qtbot):
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    tool = TextHighlighter(font)
    
    matcher = SubstringMatcher('foo', LogLevelStrategy.INFO)
    item = LogLevelDebugResult('foo', matcher, matcher.result, 0, 3)

    tool.setText(item.line)
    tool.apply_highlight(item, QColor(Qt.white), QColor(Qt.black))
    
    actual = toHtml(tool)
    assert actual == '<span style=" color:#ffffff; background-color:#000000;">foo</span>'

def test_highlighter_apply_highlight_no_match(qtbot):
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    tool = TextHighlighter(font)
    
    item = LogLevelDebugResult('foo')

    tool.setText(item.line)
    tool.apply_highlight(item, QColor(Qt.white), QColor(Qt.black))
    
    actual = toHtml(tool)
    assert actual == '<span>foo</span>'

def test_highlighter_sizeHint(qtbot):
    font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
    tool = TextHighlighter(font)

    size = tool.sizeHint(' ')
    assert size.width() > 0 and size.height() > 0
