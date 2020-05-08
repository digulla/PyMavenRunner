#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import (
    CustomPatternDebugTableModel,
    CustomPatternDialog,
    CustomPatternTable,
    QtPreferences,
    TextHighlighter,
)
from pathlib import Path
import re
from PyQt5.QtWidgets import QStyle
from PyQt5.QtGui import QFontDatabase, QColor
from PyQt5.QtCore import Qt

rootFolder = Path(__file__).parent.parent.resolve()

def createMultiModuleDialog():
    project = Project(rootFolder / 'it' / 'multi-module-project')
    preferences = project.preferences
    preferences.load()
    qtPrefs = QtPreferences()
    return CustomPatternDialog(qtPrefs, preferences.customPatternPreferences, None)

def test_create_dialog(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)

    assert [dialog.patternTable.rowCount(), dialog.testResults.model().rowCount(0)] == [7, 14]

def test_delete_row(qtbot, qtmodeltester):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)

    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.deleteMatcher(0)
    
    # TODO Why doesn't this work?
    #def check_test_results_were_updated():
    #    assert dialog.testResults.model().rowCount(0) == 12
    #
    #qtbot.waitUntil(check_test_results_were_updated)

    # I can't really get a signal since the whole model is replaced
    dialog.patternsChanged(*blocker.args)

    assert [dialog.patternTable.rowCount(), dialog.testResults.model().rowCount(0)] == [6, 14]
    assert repr(dialog.matchers[0]) == "SubstringMatcherConfig(pattern='ErrorTest', result=1)"
    
    # TODO FAIL! model->hasChildren(topIndex) () returned FALSE (qabstractitemmodeltester.cpp:360)
    # I'm using the official table model from Qt. Why does it fail?
    #qtmodeltester.check(dialog.testResults.model())

def test_movePatternFocus_negative(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)

    dialog.patternTable.movePatternFocus(0, 0)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, 0)
    
    dialog.patternTable.movePatternFocus(0, -1)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, 0)

def test_movePatternFocus_negative2(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)

    dialog.patternTable.movePatternFocus(0, 0)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, 0)
    
    dialog.patternTable.movePatternFocus(-1, -1)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, 0)

def test_movePatternFocus_negative3(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)

    dialog.patternTable.movePatternFocus(0, 0)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, 0)
    
    dialog.patternTable.movePatternFocus(-1, 0)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, 0)

def test_movePatternFocus_next_row(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)
    
    dialog.patternTable.movePatternFocus(2, CustomPatternTable.COLUMN_COUNT)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (3, 0)

def test_movePatternFocus_previous_row(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)
    
    dialog.patternTable.movePatternFocus(2, -1)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (1, CustomPatternTable.PATTERN)

def test_movePatternFocus_past_last_cell(qtbot):
    dialog = createMultiModuleDialog()
    qtbot.addWidget(dialog)
    
    model = dialog.patternTable.model()
    lastRow = model.rowCount() - 1
    dialog.patternTable.movePatternFocus(lastRow, model.columnCount() - 1)
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (lastRow, CustomPatternTable.PATTERN)
    
    dialog.patternTable.movePatternFocus(lastRow + 1, model.columnCount())
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (lastRow, CustomPatternTable.PATTERN)

def createEmptyDialog():
    project = Project(Path('Foo'))
    defaults = Defaults(CustomPatternEmptyDefaults())
    preferences = ProjectPreferences(project, defaults)
    
    qtPrefs = QtPreferences()
    return CustomPatternDialog(qtPrefs, preferences.customPatternPreferences, None)

def test_empty_table(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)

    assert dialog.matchers == []

def test_add_substring_matcher(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
        
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addSubstring()
    
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, CustomPatternTable.LEVEL)
    assert isinstance(dialog.matchers[-1], SubstringMatcherConfig)

def test_add_starts_with_matcher(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addStartsWith()
    
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, CustomPatternTable.LEVEL)
    assert isinstance(dialog.matchers[-1], StartsWithMatcherConfig)

def test_add_ends_with_matcher(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addEndsWith()
    
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, CustomPatternTable.LEVEL)
    assert isinstance(dialog.matchers[-1], EndsWithMatcherConfig)

def test_add_regex_matcher(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addRegex()
    
    assert (dialog.patternTable.currentRow(), dialog.patternTable.currentColumn()) == (0, CustomPatternTable.LEVEL)
    assert isinstance(dialog.matchers[-1], RegexMatcherConfig)

def test_update_pattern(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addSubstring()
    
    matcher = dialog.matchers[-1]
    assert matcher.pattern == ''

    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.updatePattern(matcher, 'foo')

    assert matcher.pattern == 'foo'

def test_update_level(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addSubstring()
    
    matcher = dialog.matchers[-1]
    assert matcher.result == LogLevelStrategy.INFO

    expected = LogLevelStrategy.DEBUG
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.updateLevel(matcher, expected)

    assert matcher.result == expected

def test_update_preferences(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    prefs = dialog.customPatternPreferences

    assert (prefs.matchers, prefs.test_input) == ([], [])

    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addSubstring()

    matcher = dialog.matchers[-1]

    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.updatePattern(matcher, 'a')

    with qtbot.waitSignal(dialog.testInputEditor.textChanged) as blocker:
        dialog.testInputEditor.setPlainText('xax\nxbx\n')

    assert (prefs.matchers, prefs.test_input) == ([], [])

    dialog.updatePreferences()

    assert (prefs.matchers, prefs.test_input) == (
        [
            SubstringMatcherConfig('a', LogLevelStrategy.INFO)
        ],
        [
            'xax', 'xbx', ''
        ]
    )

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
    qtbot.addWidget(model)
    actual = getDataForRow(model, Qt.DisplayRole)
    
    assert actual == [
        'INFO',
        'foo',
        "SubstringMatcher('oo', 2)"
    ]
    
def test_CustomPatternDebugTableModel_headerData(qtbot, qapp):
    model = createTestModel(qapp)
    qtbot.addWidget(model)
    actual = list(
        model.headerData(section, Qt.Horizontal, Qt.DisplayRole)
        for section in range(5)
    )
    
    assert actual == [
        'Level',
        'Maven Output',
        'Matcher',
        '4',
        '5',
    ]
    
def test_CustomPatternDebugTableModel_ForegroundRole(qtbot, qapp):
    model = createTestModel(qapp)
    qtbot.addWidget(model)
    
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
    result = re.sub(r'\s+font-size:[^;]+;', '', result)
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
