#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import QtPreferences, LogView
from pathlib import Path
from PyQt5.QtGui import QTextTable, QTextTableCell

def createLogView():
    prefs = QtPreferences()
    view = LogView(prefs)
    return view

class Dumper:
    def dump(self, document):
        withoutRootFrame = self.dumpFrame(document.rootFrame())[1:]
        # Strip empty blocks at end
        while self.lastBlockIsEmpty(withoutRootFrame):
            del withoutRootFrame[-1]

        return withoutRootFrame

    def lastBlockIsEmpty(self, blocks):
        if len(blocks) == 0:
            return False

        lastBlock = blocks[-1]
        return lastBlock[0].startswith('#BLOCK') and len(lastBlock) == 1

    def dumpFrame(self, frame, result=None):
        if isinstance(frame, QTextTable):
            return self.dumpTable(frame)

        if result is None:
            result = ['#FRAME']

        it = frame.begin()
        while not it.atEnd():
            childFrame = it.currentFrame()
            if childFrame is None:
                childBlock = it.currentBlock()
                if childBlock.isValid():
                    result.append(self.dumpBlock(childBlock))
            else:
                result.append(self.dumpFrame(childFrame))

            it += 1

        return result

    def dumpTable(self, table):
        result = ["#TABLE"]

        # This complicated code is necessary because PyQt5 doesn't support QTextTableCell.begin()
        it = table.begin()
        row = 0
        column = 0
        while not it.atEnd():
            childFrame = it.currentFrame()
            if childFrame is None:
                childBlock = it.currentBlock()
                if childBlock.isValid():
                    result.append(self.dumpCell(table, childBlock, row, column))

                    column += 1
                    if column == table.columns():
                        column = 0
                        row += 1
            else:
                result.append(self.dumpFrame(childFrame))

            it += 1

        return result

    def dumpCell(self, table, block, rowIndex, columnIndex):
        cell = table.cellAt(rowIndex, columnIndex)
        cellFormatIndex = cell.tableCellFormatIndex()
        result = [f'#CELL{rowIndex}:{columnIndex}:F{cellFormatIndex}']

        result.append(self.dumpBlock(block))
        return result

    def dumpBlock(self, block):
        blockFormatIndex = block.blockFormatIndex()
        blockFormat = '' if blockFormatIndex == 1 else f',BF:{blockFormatIndex}'
        charFormatIndex = block.charFormatIndex()
        charFormat = '' if charFormatIndex == 0 else f',CF:{charFormatIndex}'

        result = [f'#BLOCK{charFormat}{blockFormat}']

        it = block.begin()
        while not it.atEnd():
            fragment = it.fragment()
            if fragment.isValid():
                result.append(self.dumpFragment(fragment))

            it += 1

        return result

    def dumpFragment(self, fragment):
        charFormatIndex = fragment.charFormatIndex()
        text = fragment.text()
        #print(repr(fragment), charFormatIndex, repr(text))
        return f'F{charFormatIndex}:{text}'

def dump(view):
    view.flushUpdates()
    return Dumper().dump(view.document())

def test_init(qtbot):
    view = createLogView()
    qtbot.addWidget(view)

    actual = dump(view)
    assert actual == [['#BLOCK', 'F0:Ready.']]

def test_clear(qtbot):
    view = createLogView()
    qtbot.addWidget(view)
    view.clear()

    actual = dump(view)
    assert actual == []

def test_maven_started(qtbot):
    view = createLogView()
    qtbot.addWidget(view)

    project = Project(Path('Foo'))
    args = ['mvn', '-b', 'clean', 'install']
    view.mavenStarted(project, args)

    actual = dump(view)
    assert actual == [['#BLOCK', 'F0:Started Maven in Foo: mvn -b clean install']]

def test_maven_module(qtbot):
    view = createLogView()
    qtbot.addWidget(view)
    view.clear()

    view.mavenModule('IT1 Simple Maven Project 1.0')

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:IT1 Simple Maven Project 1.0']]

def test_maven_plugin(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.mavenPlugin('maven-clean-plugin:2.5:clean (default-clean) @ IT1')

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:--- maven-clean-plugin:2.5:clean (default-clean) @ IT1 ---']]

def test_unknown_output(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.testOutput('foo')

    actual = dump(view)
    assert actual == [['#BLOCK', 'F0:foo']]

def test_warning(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.warning('foo2')

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:foo2']]

def test_error(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.error('foo3')

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:foo3']]

def test_tests_started(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.testsStarted()

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:TESTS']]

def test_started_test(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.startedTest('foo4')

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:foo4']]

def test_finished_test(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    name, numberOfTests, failures, errors, skipped, duration = 'success', 5, 0, 0, 0, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    name, numberOfTests, failures, errors, skipped, duration = 'skipped', 5, 0, 0, 1, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    name, numberOfTests, failures, errors, skipped, duration = 'errors', 5, 0, 1, 0, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    name, numberOfTests, failures, errors, skipped, duration = 'failures', 5, 1, 0, 0, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    name, numberOfTests, failures, errors, skipped, duration = 'errors and failures', 5, 1, 1, 0, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    name, numberOfTests, failures, errors, skipped, duration = 'skipped and errors', 5, 0, 1, 1, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    name, numberOfTests, failures, errors, skipped, duration = 'skipped and failures', 5, 1, 0, 1, '1 s'
    view.finishedTest(name, numberOfTests, failures, errors, skipped, duration)

    actual = dump(view)
    assert actual == [
        ['#BLOCK', 'F2:Tests run: 5 Failures: 0 Errors: 0 Skipped: 0 Time elapsed: 1 s'],
        ['#BLOCK,CF:2', 'F3:Tests run: 5 Failures: 0 Errors: 0 Skipped: 1 Time elapsed: 1 s'],
        ['#BLOCK,CF:3', 'F4:Tests run: 5 Failures: 0 Errors: 1 Skipped: 0 Time elapsed: 1 s'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 1 Errors: 0 Skipped: 0 Time elapsed: 1 s'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 1 Errors: 1 Skipped: 0 Time elapsed: 1 s'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 0 Errors: 1 Skipped: 1 Time elapsed: 1 s'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 1 Errors: 0 Skipped: 1 Time elapsed: 1 s'],
    ]

def test_tests_finished(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    name, numberOfTests, failures, errors, skipped = 'success', 5, 0, 0, 0
    view.testsFinished(numberOfTests, failures, errors, skipped)

    name, numberOfTests, failures, errors, skipped = 'skipped', 5, 0, 0, 1
    view.testsFinished(numberOfTests, failures, errors, skipped)

    name, numberOfTests, failures, errors, skipped = 'errors', 5, 0, 1, 0
    view.testsFinished(numberOfTests, failures, errors, skipped)

    name, numberOfTests, failures, errors, skipped = 'failures', 5, 1, 0, 0
    view.testsFinished(numberOfTests, failures, errors, skipped)

    name, numberOfTests, failures, errors, skipped = 'errors and failures', 5, 1, 1, 0
    view.testsFinished(numberOfTests, failures, errors, skipped)

    name, numberOfTests, failures, errors, skipped = 'skipped and errors', 5, 0, 1, 1
    view.testsFinished(numberOfTests, failures, errors, skipped)

    name, numberOfTests, failures, errors, skipped = 'skipped and failures', 5, 1, 0, 1
    view.testsFinished(numberOfTests, failures, errors, skipped)

    actual = dump(view)
    assert actual == [
        ['#BLOCK', 'F2:Tests run: 5 Failures: 0 Errors: 0 Skipped: 0'],
        ['#BLOCK,CF:2', 'F3:Tests run: 5 Failures: 0 Errors: 0 Skipped: 1'],
        ['#BLOCK,CF:3', 'F4:Tests run: 5 Failures: 0 Errors: 1 Skipped: 0'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 1 Errors: 0 Skipped: 0'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 1 Errors: 1 Skipped: 0'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 0 Errors: 1 Skipped: 1'],
        ['#BLOCK,CF:4', 'F4:Tests run: 5 Failures: 1 Errors: 0 Skipped: 1'],
    ]

def test_tests_finished_ok(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.mavenFinished(0)

    actual = dump(view)
    assert actual == [['#BLOCK', 'F0:Maven terminated with 0']]

def test_tests_finished_error(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.mavenFinished(1)

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:Maven terminated with 1']]

def test_reactor_build_order_single_project(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.reactorBuildOrder('foo', '')

    actual = dump(view)
    assert actual == [
        ['#BLOCK'],
        ['#TABLE', 
            ['#CELL0:0:F3', ['#BLOCK,CF:3', 'F0:foo']],
            ['#CELL0:1:F3', ['#BLOCK,CF:3']],
        ]
    ]

def test_reactor_build_order_single_project_with_packaging(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.reactorBuildOrder('foo', 'jar')

    actual = dump(view)
    assert actual == [
        ['#BLOCK'],
        ['#TABLE', 
            ['#CELL0:0:F3', ['#BLOCK,CF:3', 'F0:foo']],
            ['#CELL0:1:F3', ['#BLOCK,CF:3', 'F0:jar']],
        ]
    ]

def test_reactor_build_order(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.reactorBuildOrder('parent', 'pom')
    view.reactorBuildOrder('foo', 'jar')

    actual = dump(view)
    assert actual == [
        ['#BLOCK'],
        ['#TABLE', 
            ['#CELL0:0:F3', ['#BLOCK,CF:3', 'F0:parent']],
            ['#CELL0:1:F3', ['#BLOCK,CF:3', 'F0:pom']],
            ['#CELL1:0:F3', ['#BLOCK,CF:3', 'F0:foo']],
            ['#CELL1:1:F3', ['#BLOCK,CF:3', 'F0:jar']]
        ]
    ]

def test_reactor_summary(qtbot):
    view = createLogView()
    view.clear()
    view.reactorSummary('root', 'SUCCESS', '1 s')
    view.reactorSummary('parent', 'FAILURE', '1 s')
    view.reactorSummary('foo', 'SKIPPED', '')

    actual = dump(view)
    assert actual == [
        ['#BLOCK'],
        ['#TABLE', 
            ['#CELL0:0:F3', ['#BLOCK,CF:3', 'F0:root']],
            ['#CELL0:1:F3', ['#BLOCK,CF:3,BF:5', 'F0:SUCCESS']],
            ['#CELL0:2:F3', ['#BLOCK,CF:3,BF:6', 'F0:1 s']],
            ['#CELL1:0:F3', ['#BLOCK,CF:3', 'F0:parent']],
            ['#CELL1:1:F3', ['#BLOCK,CF:3,BF:7', 'F0:FAILURE']],
            ['#CELL1:2:F3', ['#BLOCK,CF:3,BF:6', 'F0:1 s']],
            ['#CELL2:0:F3', ['#BLOCK,CF:3', 'F0:foo']],
            ['#CELL2:1:F3', ['#BLOCK,CF:3,BF:8', 'F0:SKIPPED']],
            ['#CELL2:2:F3', ['#BLOCK,CF:3,BF:6']],
        ]
    ]

def test_hr(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.appendLine('before')
    view.horizontalLine()
    view.appendLine('after')

    # TODO The dumper doesn't find the attribute which makes the horizontal line appear...
    actual = dump(view)
    assert actual == [['#BLOCK', 'F0:before'], ['#BLOCK'], ['#BLOCK,BF:2'], ['#BLOCK', 'F0:after']]

def test_dependencyTree(qtbot):
    view = createLogView()
    view.clear()
    qtbot.addWidget(view)

    view.dependencyTree('parent')
    view.dependencyTree('+- foo')

    print(view.pendingUpdates)

    actual = dump(view)
    assert actual == [['#BLOCK', 'F2:parent'], ['#BLOCK,CF:2', 'F2:+- foo']]

def test_scrolling(qtbot):
    view = createLogView()
    qtbot.addWidget(view)

    view.scrollToPosition(0)
    
    cursor = view.textCursor()
    assert [cursor.selectionStart(), cursor.selectionEnd()] == [0, 6]
