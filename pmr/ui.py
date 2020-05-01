#!python3
# -*- coding: utf-8 -*-

try:
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QDialogButtonBox,
        QCheckBox,
        QComboBox,
        QDialog,
        QErrorMessage,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QHeaderView,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMenu,
        QPlainTextEdit,
        QPushButton,
        QShortcut,
        QSizePolicy,
        QSplitter,
        QStyle,
        QStyledItemDelegate,
        QTableView,
        QTableWidget,
        QTableWidgetItem,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
        QWidget,
    )
    from PyQt5.QtGui import (
        QBrush,
        QColor,
        QFont,
        QFontDatabase,
        QHoverEvent,
        QMouseEvent,
        QPalette,
        QTextCharFormat,
        QTextCursor,
        QTextFormat,
        QTextFrameFormat,
        QTextTableFormat,
    )
    from PyQt5.QtCore import (
        pyqtSignal,
        QAbstractTableModel,
        QItemSelectionModel,
        QObject,
        QPoint,
        QSettings,
        QSize,
        Qt,
        QThread,
        QTimer,
    )
    from PyQt5 import QtCore, QtGui, QtWidgets
except:
    # Cygwin
    print("Please install python3-pyqt and python3-sip")
    raise

from pathlib import Path
import datetime
import os
import re
import subprocess
import tempfile
import time
import traceback
import pmr
from pmr.logging import FileLogger
from pmr.tools import OsSpecificInfo
from pmr.model import (
    CustomPatternPreferences,
    LogLevelStrategy,
    LogLevelStrategyDebugger,
    LogLevelStrategyFactory,
    Project,
    ProjectPreferences,
    RegexMatcher,
    RegexMatcherConfig,
    StartsWithMatcher,
    StartsWithMatcherConfig,
    SubstringMatcher,
    SubstringMatcherConfig,
)

class QtPreferences:
    def __init__(self):
        self.defaultTextColor = Qt.black
        self.defaultBackgroundColor = Qt.white
        self.infoColor = Qt.gray
        self.errorColor = Qt.darkRed
        self.errorBackgroundColor = Qt.red
        self.warningColor = Qt.darkYellow
        self.debugColor = Qt.gray
        self.successBackgroundColor = QColor('lime')
        self.failureBackgroundColor = Qt.red
        self.skippedBackgroundColor = Qt.gray

class CustomPatternEditTableModel:
    DELETE, TYPE, LEVEL, PATTERN, COLUMN_COUNT = range(5)

class LevelEditor(QComboBox):
    levelChanged = pyqtSignal(int) # level

    def __init__(self, choices, parent=None):
        super().__init__(parent)

        self.choices = choices

        for text, value in self.choices:
            self.addItem(text, value)

        self.currentIndexChanged[int].connect(
            lambda index: self.levelChanged.emit(self.currentData())
        )

    def setLevel(self, level):
        index = list(it[1] for it in self.choices).index(level)
        self.setCurrentIndex(index)

class PatternEditor(QLineEdit):
    focusPreviousWidget = pyqtSignal()
    focusNextWidget = pyqtSignal()
    accept = pyqtSignal()

    def keyPressEvent(self, event):
        pos = self.cursorPosition()
        if event.key() == Qt.Key_Left and pos == 0:
            self.focusPreviousWidget.emit()
        elif event.key() == Qt.Key_Right and pos == len(self.text()):
            self.focusNextWidget.emit()
        elif event.key() in (Qt.Key_Enter, Qt.Key_Return) and event.modifiers() == Qt.ControlModifier:
            self.accept.emit()
        else:
            super().keyPressEvent(event)

class CustomPatternDebugTableModel(QAbstractTableModel):
    def __init__(self, preferences, style, results):
        super().__init__()
        self.results = tuple(results)
        self.style = style
        self.prefs = preferences

        self.unknownIcon = self.style.standardIcon(QStyle.SP_MessageBoxInformation)

        self.colors = {
            LogLevelStrategy.ERROR: QColor(self.prefs.errorColor),
            LogLevelStrategy.WARNING: QColor(self.prefs.warningColor),
            LogLevelStrategy.DEBUG: QColor(self.prefs.debugColor),
            LogLevelStrategy.INFO: QColor(self.prefs.defaultTextColor),
            LogLevelStrategy.UNKNOWN: self.unknownIcon,
        }

    def data(self, index, role):
        if role == Qt.DisplayRole:
            item = self.results[index.row()]

            if index.column() == 0:
                return item.level
            elif index.column() == 1:
                return item.line
            else:
                return repr(item.matcher)
        elif role in (Qt.ForegroundRole, Qt.DecorationRole):
            if index.column() == 0:
                item = self.results[index.row()]
                return self.colors.get(item.result)

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0:
                    return 'Level'
                elif section == 1:
                    return 'Maven Output'
                elif section == 2:
                    return 'Matcher'
                else:
                    return str(section)

    def rowCount(self, index):
        return len(self.results)

    def columnCount(self, index):
        return 3

# Copied from https://stackoverflow.com/questions/53353450/how-to-highlight-a-words-in-qtablewidget-from-a-searchlist
class TextHighlighter:
    def __init__(self, font, parent=None):
        self.font = font
        
        self.doc = QtGui.QTextDocument(parent)

    def setText(self, text):
        self.doc.setPlainText(text)

    def draw(self, painter, context):
        self.doc.documentLayout().draw(painter, context)        

    def sizeHint(self, text):
        self.doc.setPlainText(text)

        fmtFont = QtGui.QTextCharFormat()
        fmtFont.setFont(self.font)
        cursor = QtGui.QTextCursor(self.doc)
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        cursor.mergeCharFormat(fmtFont)
        cursor.endEditBlock()
        
        return self.doc.size()

    def apply_highlight(self, item, textColor, bgColor):
        fmtFont = QtGui.QTextCharFormat()
        fmtFont.setFont(self.font)

        fmtHighlight = QtGui.QTextCharFormat()
        fmtHighlight.setForeground(textColor)
        fmtHighlight.setBackground(QBrush(bgColor))
        fmtHighlight.setFont(self.font)

        cursor = QtGui.QTextCursor(self.doc)
        cursor.beginEditBlock()
        cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        cursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        cursor.mergeCharFormat(fmtFont)

        if item.matcher is not None:
            cursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
            if item.start > 0:
                cursor.movePosition(QTextCursor.Right, QTextCursor.MoveAnchor, item.start)
            n = item.end - item.start
            cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, n)
            cursor.mergeCharFormat(fmtHighlight)

        cursor.endEditBlock()

class HighlightDelegate(QStyledItemDelegate):
    def __init__(self, tableWidget, parent=None):
        super(HighlightDelegate, self).__init__(parent)
        
        self.tableWidget = tableWidget
        
        font = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.highlighter = TextHighlighter(font, self)

    def paint(self, painter, option, index):
        painter.save()
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        self.highlighter.setText(options.text)
        options.text = ""

        style = QtWidgets.QApplication.style() if options.widget is None \
            else options.widget.style()
        style.drawControl(QtWidgets.QStyle.CE_ItemViewItem, options, painter)

        textColor = option.palette.color(
            QtGui.QPalette.Active, QtGui.QPalette.HighlightedText)
        bgColor = option.palette.color(
            QtGui.QPalette.Active, QtGui.QPalette.Highlight)

        row = index.row()
        item = self.tableWidget.model().results[row]

        self.highlighter.apply_highlight(item, textColor, bgColor)

        textRect = self.calcTextRect(options, style, index)

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()
        if option.state & QtWidgets.QStyle.State_Selected:
            ctx.palette.setColor(QtGui.QPalette.Text, textColor)
        else:
            ctx.palette.setColor(QtGui.QPalette.Text, option.palette.color(
                QtGui.QPalette.Active, QtGui.QPalette.Text))

        painter.translate(textRect.topLeft())
        painter.setClipRect(textRect.translated(-textRect.topLeft()))
        self.highlighter.draw(painter, ctx)

        painter.restore()

    def calcTextRect(self, options, style, index):
        textRect = style.subElementRect(
            QtWidgets.QStyle.SE_ItemViewItemText, options)

        if index.column() != 0:
            textRect.adjust(5, 0, 0, 0)

        the_constant = 4
        margin = (options.rect.height() - options.fontMetrics.height()) // 2
        margin = margin - the_constant
        textRect.setTop(textRect.top() + margin)
        return textRect

    def sizeHint(self, option, index):
        options = QtWidgets.QStyleOptionViewItem(option)
        self.initStyleOption(options, index)
        
        size = self.highlighter.sizeHint(options.text)
        
        style = QtWidgets.QApplication.style() if options.widget is None \
            else options.widget.style()
        textRect = self.calcTextRect(options, style, index)
        return QtCore.QSize(size.width() + 2 * textRect.left(), size.height())

class DragAndDropCursorEventFilter(QObject):
    def __init__(self):
        super().__init__()

    def eventFilter(self, obj, event):
        #print(obj, event)
        if isinstance(event, QHoverEvent):
            pos = event.pos()
            index = obj.logicalIndexAt(pos)
            #print(index)
            if index >= 0:
                obj.setCursor(Qt.SplitVCursor)
            else:
                obj.setCursor(Qt.ArrowCursor)

        return super().eventFilter(obj, event)

class CustomPatternTable(QTableWidget):
    patternsChanged = pyqtSignal(tuple)
    accept = pyqtSignal()

    def __init__(self, matchers, parent=None):
        super().__init__(len(matchers), CustomPatternEditTableModel.COLUMN_COUNT, parent=parent)

        self.matchers = matchers

        self.translation = {
            SubstringMatcherConfig: 'Substring',
            RegexMatcherConfig: 'Regular Expression',
        }
        self.levelChoices = list(
            [LogLevelStrategy.LEVEL_NAMES[it], it]
            for it in LogLevelStrategy.LEVELS
        )
        self.fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        self.dragIcon = self.style().standardIcon(QStyle.SP_FileDialogDetailedView)
        self.patternEditors = []

        self.verticalHeader().setSectionsMovable(True)
        self.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.verticalHeader().sectionMoved.connect(self.emitPatternsChanged)
        self.setDragDropMode(QTableView.InternalMove) # TODO Is this necessary?
        self.setDropIndicatorShown(True)

        self.setHorizontalHeaderItem(CustomPatternEditTableModel.DELETE, QTableWidgetItem(''))
        self.setHorizontalHeaderItem(CustomPatternEditTableModel.TYPE, QTableWidgetItem('Type'))
        self.setHorizontalHeaderItem(CustomPatternEditTableModel.LEVEL, QTableWidgetItem('Level'))
        self.setHorizontalHeaderItem(CustomPatternEditTableModel.PATTERN, QTableWidgetItem('Pattern'))

        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.verticalHeader().setCursor(Qt.SplitVCursor)
        self._dragAndDropFilter = DragAndDropCursorEventFilter()
        self.verticalHeader().installEventFilter(self._dragAndDropFilter)

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        addSubstring = menu.addAction("Add Substring Matcher")
        addStartsWith = menu.addAction("Add Starts-With Matcher")
        addRegex = menu.addAction("Add Regex Matcher")
        action = menu.exec_(self.mapToGlobal(event.pos()))

        matcher = None
        if action == addSubstring:
            matcher = SubstringMatcherConfig('', LogLevelStrategy.INFO)
        elif action == addStartsWith:
            matcher = StartsWithMatcherConfig('', LogLevelStrategy.INFO)
        elif action == addRegex:
            matcher = RegexMatcherConfig('', LogLevelStrategy.INFO)

        if matcher is None:
            return

        row = self.rowCount()
        self.setRowCount(row + 1)

        self.matchers.append(matcher)
        self.createPatternEditors(row, matcher)

        self.movePatternFocus(row, CustomPatternEditTableModel.LEVEL)

    def createWidgets(self):
        for row, matcher in enumerate(self.matchers):
            rowEditors = self.createPatternEditors(row, matcher)
            self.patternEditors.append(rowEditors)

    def createPatternEditors(self, row, matcher):
        rowEditors = []

        #label = f"={row:02d}"
        dragDropWidget = QTableWidgetItem(self.dragIcon, '')
        dragDropWidget.setToolTip('Drag & drop to change order of matchers')
        self.setVerticalHeaderItem(row, dragDropWidget)
        rowEditors.append(dragDropWidget)

        deleteButton = QPushButton('-')
        deleteButton.setToolTip('Delete the current row')
        self.setCellWidget(row, CustomPatternEditTableModel.DELETE, deleteButton)
        deleteButton.clicked.connect(lambda checked, row=row: self.deleteMatcher(row))
        # TODO This button is way to big. How to make it smaller?
        deleteButton.setStyleSheet('min-width: 35px;')
        rowEditors.append(deleteButton)

        type = self.translation.get(matcher.__class__, matcher.__class__.__name__)
        item = QTableWidgetItem(type)
        item.setFlags(QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable)
        self.setItem(row, CustomPatternEditTableModel.TYPE, item)
        rowEditors.append(item)

        editor = self.createLevelEditor(row, matcher, self.levelChoices)
        self.setCellWidget(row, CustomPatternEditTableModel.LEVEL, editor)
        rowEditors.append(editor)

        editor = self.createPatternCellEditor(row, CustomPatternEditTableModel.PATTERN, matcher)
        self.setCellWidget(row, CustomPatternEditTableModel.PATTERN, editor)
        rowEditors.append(editor)

        return rowEditors

    def deleteMatcher(self, row):
        print(f'Delete {row}')
        self.removeRow(row)
        del self.patternEditors[row]
        del self.matchers[row]

        self.emitPatternsChanged()

    def emitPatternsChanged(self, *args):
        #print('emitPatternsChanged')
        param = tuple(
            self.matchers[self.verticalHeader().logicalIndex(i)]
            for i in range(0, self.rowCount())
        )

        self.patternsChanged.emit(param)

    def createLevelEditor(self, row, matcher, choices):
        result = LevelEditor(choices)
        result.setLevel(matcher.result)
        result.levelChanged.connect(lambda level, matcher=matcher: self.updateLevel(matcher, level))
        return result

    def createPatternCellEditor(self, row, column, matcher):
        result = PatternEditor()
        result.setText(matcher.pattern)
        result.setFont(self.fixedFont)
        result.textEdited.connect(lambda pattern, matcher=matcher: self.updatePattern(matcher, pattern))
        result.focusPreviousWidget.connect(lambda row=row, column=column: self.movePatternFocus(row, column - 1))
        result.focusNextWidget.connect(lambda row=row: self.movePatternFocus(row, column + 1))
        result.accept.connect(lambda *args: self.accept.emit())
        return result

    def movePatternFocus(self, row, column):
        if column < 0:
            row -= 1
            if row < 0:
                return
            column = self.columnCount() - 1
        elif column >= self.columnCount():
            row += 1
            if row >= self.rowCount():
                return

            column = 0

        self.setCurrentCell(row, column, QItemSelectionModel.ClearAndSelect)

    def updatePattern(self, matcher, pattern):
        matcher.pattern = pattern
        self.emitPatternsChanged()

    def updateLevel(self, matcher, level):
        matcher.result = level
        self.emitPatternsChanged()

class CustomPatternDialog(QDialog):
    def __init__(self, preferences, customPatternPreferences, parent):
        super().__init__(parent)

        self.preferences = preferences
        self.customPatternPreferences = customPatternPreferences

        self.matchers = list(
            it.clone()
            for it in self.customPatternPreferences.matchers
        )
        self.test_input = list(customPatternPreferences.test_input)

        self.testResultsModel = None

        self.setModal(True)
        self.setWindowTitle("Log Pattern Editor")

        self.fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)        

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)
        self.layout.addWidget(self.splitter)

        self.patternTable = CustomPatternTable(self.matchers)
        self.patternTable.createWidgets()
        self.patternTable.patternsChanged.connect(self.patternsChanged)
        self.patternTable.accept.connect(self.accept)

        self.splitter.addWidget(self.patternTable)

        self.testInputEditor = QPlainTextEdit()
        self.testInputEditor.setFont(self.fixedFont)
        self.splitter.addWidget(self.testInputEditor)

        self.testInputEditor.setPlainText('\n'.join(self.test_input))

        self.testResults = QTableView()
        self.testResults.setSelectionMode(QAbstractItemView.SingleSelection)
        self.testResults.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.testResults.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        # Note: If this is missing, addWidget() will crash
        self.testResultsModel = CustomPatternDebugTableModel(self.preferences, self.testResults.style(), [])
        self.testResults.setModel(self.testResultsModel)
        self.testResults.setItemDelegateForColumn(1, HighlightDelegate(self.testResults))
        self.splitter.addWidget(self.testResults)

        header = self.testResults.horizontalHeader() 
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        buttons = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(buttons)
        self.buttonBox.button(QDialogButtonBox.Ok).setToolTip('<Ctrl+Return>\nAccept Changes')
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox)

        # TODO Remember size
        # TODO Remember position of splitter
        self.resize(800, 800)
        self.runDebugger()

        # Install this after everything else
        self.testInputEditor.textChanged.connect(self.testInputChanged)

    def testInputChanged(self):
        self.test_input = self.testInputEditor.toPlainText().split('\n')
        self.runDebugger()

    def patternsChanged(self, matchers):
        self.matchers = list(matchers)
        self.runDebugger()

    def updatePreferences(self):
        print('Updating custom patterns in the preferences')
        self.customPatternPreferences.matchers = self.matchers
        self.customPatternPreferences.test_input = self.test_input

    def runDebugger(self):
        #print('runDebugger')
        matchers = list(it.createMatcher() for it in self.matchers)
        strategy = LogLevelStrategy(matchers)
        debugger = LogLevelStrategyDebugger(strategy)

        text = self.testInputEditor.toPlainText()
        self.test_input = text.split('\n')
        result = debugger.debug(self.test_input)

        model = CustomPatternDebugTableModel(self.preferences, self.testResults.style(), result)
        self.testResults.setModel(model)
        self.testResultsModel = model

class MavenRunnerFrame(QFrame):
    startMaven = pyqtSignal(Project, CustomPatternPreferences, list)

    def __init__(self, projects, preferences, parent = None):
        super().__init__(parent)

        self.projects = projects
        self.preferences = preferences
        
        self.lastPath = Path.cwd()
        self.currentProject = None
        self.projectPreferences = None

        layout = QVBoxLayout(self)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        label = QLabel('Project:')
        label.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        hbox.addWidget(label)

        self.projectSelector = QComboBox()
        self.projectSelector.currentIndexChanged[int].connect(self.changeProject)
        hbox.addWidget(self.projectSelector)

        if len(self.projects) == 0:
            self.projectSelector.enabled = False
        else:
            self.projectSelector.addItems([it.name for it in self.projects])
            self.projectSelector.enabled = True

        self.addProjectButton = QPushButton('Add...')
        self.addProjectButton.setShortcut('Alt+A')
        self.addProjectButton.setToolTip('<Alt+A>\nPlease select a folder which contains a pom.xml')
        self.addProjectButton.clicked.connect(self.addProjectClicked)
        hbox.addWidget(self.addProjectButton)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        commonMavenOptions = QComboBox()
        commonMavenOptions.currentIndexChanged[str].connect(self.setGoals)
        commonMavenOptions.addItem('clean install')
        commonMavenOptions.addItem('clean test')
        commonMavenOptions.addItem('clean deploy')
        commonMavenOptions.addItem('clean')
        commonMavenOptions.addItem('dependency:tree')
        commonMavenOptions.addItem('-version')
        commonMavenOptions.addItem('')
        commonMavenOptions.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        hbox.addWidget(commonMavenOptions)

        self.mavenCmd = QLineEdit()
        hbox.addWidget(self.mavenCmd)

        hbox = QHBoxLayout()
        layout.addLayout(hbox)

        run = QPushButton('Run')
        run.setShortcut('Alt+R')
        run.setToolTip('<Alt+R>\nRun Maven with the selected options')
        run.clicked.connect(self.startMavenClicked)
        hbox.addWidget(run)

        self.resumeButton = QPushButton('Resume')
        self.resumeButton.setShortcut('Alt+S')
        self.resumeButton.setToolTip('<Alt+S>\nResume a partially failed build')
        self.resumeButton.setEnabled(False)
        self.resumeButton.clicked.connect(self.resumeMavenClicked)
        hbox.addWidget(self.resumeButton)

        self.skipTestsButton = QCheckBox('Skip Tests')
        self.skipTestsButton.setShortcut('Alt+T')
        self.skipTestsButton.setToolTip('<Alt+T>\nSkip tests')
        hbox.addWidget(self.skipTestsButton)

        patternsButton = QPushButton('Custom Patterns')
        patternsButton.setShortcut('Alt+P')
        patternsButton.setToolTip('<Alt+P>\nEdit patterns that determine what each line of log output means')
        patternsButton.clicked.connect(self.showCustomPatternDialog)
        hbox.addWidget(patternsButton)

        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.projectSelector.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        run.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.resumeButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.addProjectButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        patternsButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

    def showCustomPatternDialog(self):
        dlg = CustomPatternDialog(self.preferences, self.projectPreferences.customPatternPreferences, self)
        result = dlg.exec_()
        if result == QDialog.Accepted:
            dlg.updatePreferences()

    def saveProjectPreferences(self):
        if self.projectPreferences is not None:
            self.projectPreferences.save()

    def resumeDetected(self, resumeOption):
        self.resumeOption = resumeOption
        self.resumeButton.setEnabled(True)

    def setGoals(self, goals):
        self.goals = goals
        print(f'Selected goals "{self.goals}"')

    def setCurrentProjectIndex(self, index):
        self.projectSelector.setCurrentIndex(index)

    def addProjectClicked(self):
        qtPath = QFileDialog.getExistingDirectory(
            self,
            'Select Maven project folder',
            str(self.lastPath)
        )
        self.lastPath = Path(qtPath)
        
        pom = self.lastPath / 'pom.xml'
        if pom.exists():
            project = Project(self.lastPath)
            self.projects.append(project)
            self.projectSelector.addItem(project.name)
            
            self.projectSelector.setCurrentIndex(len(self.projects) - 1)
            
            self.projectSelector.enabled = True
        else:
            dialog = QErrorMessage(self)
            dialog.showMessage(f'Missing pom.xml in\n{self.lastPath}\nDid you select a Maven project?')

    def changeProject(self, index):
        if self.currentProject is not None and self.projectPreferences is not None:
            self.projectPreferences.save()

        self.currentProject = self.projects[index]
        print(f'Selected project "{self.currentProject.name}"')

        self.projectPreferences = ProjectPreferences(self.currentProject)
        self.projectPreferences.load()

    def startMavenClicked(self):
        #print('startMavenClicked')
        self.resumeButton.setEnabled(False)
        self.emitStartMaven(False)

    def resumeMavenClicked(self):
        self.emitStartMaven(True)

    def emitStartMaven(self, resume=False):
        args = []
        if resume:
            args.append('-rf')
            args.append(self.resumeOption)
        if len(self.goals) > 0:
            args.extend(self.goals.split(' '))
        extraOptions = self.mavenCmd.text()
        if len(extraOptions) > 0:
            args.extend(extraOptions.split(' '))
        if self.skipTestsButton.isChecked():
            args.append('-DskipTests')
        self.startMaven.emit(self.currentProject, self.projectPreferences.customPatternPreferences, args)

class LogView(QTextEdit):
    def __init__(self, preferences, parent = None):
        super().__init__(parent)

        self.preferences = preferences

        self.cursor = QTextCursor(self.document())
        self.reactorBuildOrderTable = None
        self.reactorSummaryTable = None

        self.errorBrush = QBrush(preferences.errorColor)
        self.warningBrush = QBrush(preferences.warningColor)

        self.defaultFormat = QTextCharFormat(self.currentCharFormat())

        self.moduleFormat = QTextCharFormat()
        self.moduleFormat.setFontWeight(QFont.Bold)
        self.moduleFormat.setFontPointSize(self.currentFont().pointSize() * 18 / 10)

        self.testHeaderFormat = QTextCharFormat()
        self.testHeaderFormat.setFontWeight(QFont.Bold)
        self.testHeaderFormat.setFontPointSize(self.currentFont().pointSize() * 14 / 10)

        self.testHeaderFailedFormat = QTextCharFormat(self.testHeaderFormat)
        self.testHeaderFailedFormat.setForeground(self.errorBrush)

        self.testHeaderWarningFormat = QTextCharFormat(self.testHeaderFormat)
        self.testHeaderWarningFormat.setForeground(self.warningBrush)

        self.testFormat = QTextCharFormat()
        self.testFormat.setFontWeight(QFont.Bold)
        self.testFormat.setFontPointSize(self.currentFont().pointSize() * 12 / 10)

        self.testFailedFormat = QTextCharFormat(self.testFormat)
        self.testFailedFormat.setForeground(self.errorBrush)

        self.testWarningFormat = QTextCharFormat(self.testFormat)
        self.testWarningFormat.setForeground(self.warningBrush)

        self.mavenPluginFormat = QTextCharFormat()
        self.mavenPluginFormat.setFontWeight(QFont.Bold)

        fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        self.dependencyFormat = QTextCharFormat()
        self.dependencyFormat.setFont(fixedFont)

        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(self.errorBrush)
        self.errorFormat.setFont(fixedFont)

        self.warningFormat = QTextCharFormat()
        self.warningFormat.setForeground(self.warningBrush)
        self.warningFormat.setFont(fixedFont)

        self.tableFormat = QTextTableFormat()
        #print(dir(self.tableFormat))
        # TODO Qt 5.14
        #self.tableFormat.setBorderCollapse(True)
        self.tableFormat.setCellPadding(2.0)
        self.tableFormat.setCellSpacing(0)
        self.tableFormat.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)

        self.successBackground = QBrush(self.preferences.successBackgroundColor)
        self.failureBackground = QBrush(self.preferences.failureBackgroundColor)
        self.skippedBackground = QBrush(self.preferences.skippedBackgroundColor)

        self.append('Ready.\n')

    def scrollToPosition(self, pos):
        scrollCursor = QTextCursor(self.document())
        contextLines = 5

        scrollCursor.setPosition(pos)
        scrollCursor.movePosition(QTextCursor.Up, QTextCursor.MoveAnchor, contextLines)
        self.setTextCursor(scrollCursor)
        self.ensureCursorVisible()
        
        scrollCursor.setPosition(pos)
        scrollCursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, contextLines)
        self.setTextCursor(scrollCursor)
        self.ensureCursorVisible()

        scrollCursor.setPosition(pos)
        scrollCursor.movePosition(QTextCursor.StartOfLine, QTextCursor.MoveAnchor)
        scrollCursor.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        self.setTextCursor(scrollCursor)

    def clear(self):
        self.setHtml('')
        self.cursor.setPosition(0)
        self.reactorBuildOrderTable = None
        self.reactorSummaryTable = None

    def append(self, text):
        self.cursor.movePosition(QTextCursor.End)
        self.cursor.insertText(text)

        self.setTextCursor(self.cursor)
        self.ensureCursorVisible()

    def appendLine(self, text, format=None):
        if format is None:
            format = self.defaultFormat

        self.cursor.movePosition(QTextCursor.End)
        self.cursor.insertText(text, format)
        self.cursor.insertText('\n')

        self.setTextCursor(self.cursor)
        self.ensureCursorVisible()

    def mavenStarted(self, project, args):
        self.clear()
        cmdLine = ' '.join(args)
        self.appendLine(f'Started Maven in {project.path}: {cmdLine}')

    def mavenModule(self, coordinate):
        self.appendLine(coordinate, self.moduleFormat)

    def mavenPlugin(self, coordinate):
        self.appendLine(f'--- {coordinate} ---', self.mavenPluginFormat)

    def testOutput(self, line):
        # TODO Make DEBUG output gray
        # TODO Make TRACE outout blue
        self.appendLine(line)

    def warning(self, message):
        self.appendLine(message, self.warningFormat)

    def error(self, message):
        self.appendLine(message, self.errorFormat)

    def testsStarted(self):
        self.appendLine("TESTS", self.testHeaderFormat)

    def startedTest(self, name):
        self.appendLine(name, self.testFormat)
    
    def finishedTest(self, name, numberOfTests, failures, errors, skipped, duration):
        text = f'Tests run: {numberOfTests} Failures: {failures} Errors: {errors} Skipped: {skipped} Time elapsed: {duration}'
        if failures > 0 or errors > 0:
            format = self.testFailedFormat
        elif skipped > 0:
            format = self.testWarningFormat
        else:
            format = self.testFormat

        self.appendLine(text, format)
        # TODO collapse test output

    def testsFinished(self, numberOfTests, failures, errors, skipped):
        text = f'Tests run: {numberOfTests} Failures: {failures} Errors: {errors} Skipped: {skipped}'
        if failures > 0 or errors > 0:
            format = self.testHeaderFailedFormat
        elif skipped > 0:
            format = self.testHeaderWarningFormat
        else:
            format = self.testHeaderFormat
        self.appendLine(text, format)

    def reactorBuildOrder(self, module, packaging):
        if self.reactorBuildOrderTable is None:
            self.reactorBuildOrderTable = self.cursor.insertTable(1, 2, self.tableFormat)
        else:
            self.reactorBuildOrderTable.appendRows(1)

        lastRow = self.reactorBuildOrderTable.rows() - 1
        cell = self.reactorBuildOrderTable.cellAt(lastRow, 0)
        cell.firstCursorPosition().insertText(module)

        cell = self.reactorBuildOrderTable.cellAt(lastRow, 1)
        cell.firstCursorPosition().insertText(packaging)

    def reactorSummary(self, module, state, duration):
        if self.reactorSummaryTable is None:
            self.reactorSummaryTable = self.cursor.insertTable(1, 3, self.tableFormat)
        else:
            self.reactorSummaryTable.appendRows(1)

        lastRow = self.reactorSummaryTable.rows() - 1
        cell = self.reactorSummaryTable.cellAt(lastRow, 0)
        cell.firstCursorPosition().insertText(module)
        
        cell = self.reactorSummaryTable.cellAt(lastRow, 1)
        cursor = cell.firstCursorPosition()
        blockFormat = cursor.blockFormat()
        if state == 'SUCCESS':
            blockFormat.setBackground(self.successBackground)
        elif state == 'FAILURE':
            blockFormat.setBackground(self.failureBackground)
        elif state == 'SKIPPED':
            blockFormat.setBackground(self.skippedBackground)
        else:
            print(f"WARN Unexpected state: {state}")

        cursor.mergeBlockFormat(blockFormat)
        cursor.insertText(state)

        cell = self.reactorSummaryTable.cellAt(lastRow, 2)
        cursor = cell.firstCursorPosition()
        blockFormat = cursor.blockFormat()
        blockFormat.setAlignment(Qt.AlignRight)
        cursor.mergeBlockFormat(blockFormat)
        cursor.insertText(duration)

    def mavenFinished(self, rc):
        if rc == 0:
            self.appendLine(f"Maven terminated with {rc}")
        else:
            self.error(f"Maven terminated with {rc}")

    def horizontalLine(self):
        self.cursor.movePosition(QTextCursor.End)
        self.cursor.insertHtml('<hr>\n')

        self.setTextCursor(self.cursor)
        self.ensureCursorVisible()

    def dependencyTree(self, dependency):
        self.appendLine(dependency, self.dependencyFormat)

class LogFrame(QFrame):
    NodeTypeRole = Qt.UserRole + 1
    TextPositionRole = Qt.UserRole + 2
    
    NT_Module, NT_Plugin, NT_Anchor = range(3)
    
    def __init__(self, preferences, parent = None):
        super().__init__(parent)

        self.preferences = preferences

        self.errors = 0
        self.warnings = 0
        self.started = None
        self.state = 'Idle'
        self.currentModule = None
        self.currentPlugin = None
        self.lastLeaf = None
        self.addedReactorSummary = False

        layout = QVBoxLayout(self)
        
        self.statisticsLabel = QLabel('Waiting.')
        self.statisticsLabel.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        layout.addWidget(self.statisticsLabel)

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        layout.addWidget(self.splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.clicked.connect(self.treeNodeClicked)
        self.splitter.addWidget(self.tree)
        
        self.logView = LogView(self.preferences)
        self.splitter.addWidget(self.logView)

        self.splitter.setStretchFactor(0, 30)
        self.splitter.setStretchFactor(1, 70)
        
        self.warningBrush = QBrush(preferences.warningColor)
        self.errorBrush = QBrush(preferences.errorColor)

    def treeNodeClicked(self, index):
        item = self.tree.itemFromIndex(index)
        pos = item.data(0, self.TextPositionRole)
        self.logView.scrollToPosition(pos)

    def mavenStarted(self, *args):
        self.tree.clear()
        
        self.started = time.time()
        self.errors = 0
        self.warnings = 0
        self.state = 'Running'

        self.updateStatistics()

        self.logView.mavenStarted(*args)
    
    def mavenFinished(self, rc):
        self.state = 'Done'
        self.updateStatistics()

        self.logView.mavenFinished(rc)
        
    def updateStatistics(self):
        if self.started is None:
            startTimestamp = '-'
            duration = '-'
        else:
            startTimestamp = time.strftime('%H:%M:%S %d.%m.%Y', time.localtime(self.started))
            duration = datetime.timedelta(seconds=time.time() - self.started)
        
        self.statisticsLabel.setText(f'State: {self.state} Started: {startTimestamp} Running: {duration!s} Errors: {self.errors} Warnings: {self.warnings}')

    def mavenModule(self, coordinate):
        item = QTreeWidgetItem()
        item.setText(0, coordinate)
        self.saveTextPosition(item)
        
        self.tree.addTopLevelItem(item)
        self.scrollToItem(item)
        item.setExpanded(True)
        
        self.currentModule = item
        self.currentPlugin = None
        self.lastLeaf = None
    
        self.logView.mavenModule(coordinate)

    def reactorSummary(self, *args):
        if not self.addedReactorSummary:
            item = QTreeWidgetItem()
            item.setText(0, 'Reactor Summary')
            self.saveTextPosition(item)
            
            self.tree.addTopLevelItem(item)
            self.scrollToItem(item)
            item.setExpanded(True)
            
            self.currentModule = item
            self.currentPlugin = None
            self.lastLeaf = None
            self.addedReactorSummary = True

        self.logView.reactorSummary(*args)
    
    def mavenPlugin(self, coordinate):
        item = QTreeWidgetItem()
        item.setText(0, coordinate)
        self.saveTextPosition(item)
        
        self.currentModule.addChild(item)
        self.scrollToItem(item)
        item.setExpanded(True)
        self.currentPlugin = item
        self.lastLeaf = None

        self.logView.mavenPlugin(coordinate)
    
    def startedTest(self, name):
        item = QTreeWidgetItem()
        item.setText(0, name)
        self.saveTextPosition(item)
        
        self.currentPlugin.addChild(item)
        self.scrollToItem(item)
        self.lastLeaf = None

        self.logView.startedTest(name)
    
    def saveTextPosition(self, item):
        pos = self.logView.cursor.position()
        item.setData(0, self.TextPositionRole, pos)
    
    def warning(self, message):
        self.warnings += 1
        self.updateStatistics()
        self.addLeaf(message, type='warning', foreground=self.warningBrush)

        self.logView.warning(message)

    def error(self, message):
        self.errors += 1
        self.updateStatistics()
        self.addLeaf(message, type='error', foreground=self.errorBrush)

        self.logView.error(message)

    def output(self, *args):
        self.lastLeaf = None

        self.logView.appendLine(*args)
        
    def testOutput(self, *args):
        self.lastLeaf = None

        self.logView.testOutput(*args)

    def addLeaf(self, message, type='', foreground=None, background=None):
        if self.currentPlugin is None:
            if self.currentModule is None:
                parent = None
            else:
                parent = self.currentModule
        else:
            parent = self.currentPlugin

        if self.lastLeaf is not None:
            lastType = self.lastLeaf.data(0, self.NodeTypeRole)
            if lastType == type:
                return
    
        item = QTreeWidgetItem()
        item.setText(0, message)
        item.setData(0, self.NodeTypeRole, type)
        self.saveTextPosition(item)
        
        if foreground is not None:
            item.setForeground(0, foreground)
        if background is not None:
            item.setBackground(0, background)
        
        if parent is None:
            self.tree.addTopLevelItem(item)
        else:
            parent.addChild(item)

        self.lastLeaf = item
        self.scrollToItem(item)
    
    def scrollToItem(self, item):
        index = self.tree.indexFromItem(item, 0)
        self.tree.scrollTo(index, QAbstractItemView.PositionAtBottom)

class UnitTestParser(QObject):
    endOfTests = pyqtSignal(int, int, int, int) # numberOfTests, failures, errors, skipped
    
    def __init__(self, runner, customPatternPreferences, logger):
        super().__init__()

        self.runner = runner
        self.customPatternPreferences = customPatternPreferences
        self.logger = logger
        
        self.state = self.skipTestHeaders
        self.linesWithDashes = 0
        self.lastFewLines = []

        factory = LogLevelStrategyFactory(self.customPatternPreferences)
        self.logLevelStrategy = factory.build()

        self.signalPerLogLevel = {
            LogLevelStrategy.ERROR: self.runner.error,
            LogLevelStrategy.WARNING: self.runner.warning,
            # TODO
            #LogLevelStrategy.INFO: self.runner.info,
            #LogLevelStrategy.DEBUG: self.runner.debug,
            #LogLevelStrategy.TRACE: self.runner.trace,
            LogLevelStrategy.INFO: self.runner.testOutput,
            LogLevelStrategy.DEBUG: self.runner.testOutput,
            LogLevelStrategy.TRACE: self.runner.testOutput,
            LogLevelStrategy.UNKNOWN: self.runner.testOutput,
        }
        
    def parse(self, line):
        try:
            self.state(line)
        except Exception as ex:
            raise Exception(f'Error processing {line!r}') from ex

    def skipTestHeaders(self, line):
        line = line.strip()
        if len(line) == 0:
            return
        
        if len(line.strip('-')) == 0:
            if self.linesWithDashes == 0:
                self.runner.testsStarted.emit()

            self.linesWithDashes += 1
            if self.linesWithDashes == 2:
                self.state = self.parseUnitTestOutput
                return

        if line.startswith('[INFO]'):
            self.runner.output.emit(line)
            return

        # Ignore anything else

    TEST_START_PREFIX = 'Running '
    TEST_FINISHED_PREFIX = 'Tests run: '
    TEST_FINISHED_PATTERN = re.compile(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+), Time elapsed: (.*)')
    TESTS_FINISHED_PATTERN = re.compile(r'Tests run: (\d+), Failures: (\d+), Errors: (\d+), Skipped: (\d+)')

    def parseUnitTestOutput(self, line):
        if line.startswith(self.TEST_START_PREFIX):
            name = line[len(self.TEST_START_PREFIX):].strip()
            self.currentTest = name
            self.runner.startedTest.emit(name)
            return
        
        if line.startswith(self.TEST_FINISHED_PREFIX):
            match = self.TEST_FINISHED_PATTERN.fullmatch(line)
            if match is not None:
                numberOfTests = int(match.group(1))
                failures = int(match.group(2))
                errors = int(match.group(3))
                skipped = int(match.group(4))
                duration = match.group(5)
                self.runner.finishedTest.emit(self.currentTest, numberOfTests, failures, errors, skipped, duration)
                return
        
        if line == '':
            self.lastFewLines = ['']
            self.state = self.mightBeEndOfTests1
            return
        
        level = self.logLevelStrategy.apply(line)
        signal = self.signalPerLogLevel[level]
        signal.emit(line)
    
    def wasSomethingElse(self):
        n = len(self.lastFewLines)
        self.logger.log('MTESTPARSER.wasSomethingElse', f'Emitting {n} lines')
        for line in self.lastFewLines:
            self.runner.testOutput.emit(line)
        
        self.lastFewLines = []
        self.state = self.parseUnitTestOutput
    
    def mightBeEndOfTests1(self, line):
        self.logger.log('MTESTPARSER.mightBeEndOfTests1', repr(line))
        self.lastFewLines.append(line)
        if line == 'Results :':
            self.state = self.mightBeEndOfTests3
        elif line == '':
            return
        else:
            self.wasSomethingElse()
    
    def mightBeEndOfTests3(self, line):
        self.logger.log('MTESTPARSER.mightBeEndOfTests3', repr(line))
        self.lastFewLines.append(line)
        if line.startswith('Tests run: '):
            self.testSummaryLine = line
            self.state = self.mightBeEndOfTests5
        elif line.startswith('Failed tests: '):
            self.state = self.mightBeEndOfTests4
        elif line == '':
            pass
        else:
            self.wasSomethingElse()
    
    def mightBeEndOfTests4(self, line):
        self.logger.log('MTESTPARSER.mightBeEndOfTests4', repr(line))
        if line.startswith('Tests run: '):
            self.testSummaryLine = line
            self.state = self.mightBeEndOfTests5
            return
        
        self.runner.error.emit(line)
    
    def mightBeEndOfTests5(self, line):
        self.logger.log('MTESTPARSER.mightBeEndOfTests5', repr(line))
        if line.startswith('[INFO]'):
            self.lastFewLines = []
            self.emitTestSummary()
            self.state = self.done

    def emitTestSummary(self):
        self.logger.log('MTESTPARSER.emitTestSummary', 'Emitting end-of-tests signal')
        match = self.TESTS_FINISHED_PATTERN.fullmatch(self.testSummaryLine)
        if match is None:
            raise Exception(f"Can't parse final test result: {self.testSummaryLine!r}")
        
        numberOfTests = int(match.group(1))
        failures = int(match.group(2))
        errors = int(match.group(3))
        skipped = int(match.group(4))
        
        self.endOfTests.emit(numberOfTests, failures, errors, skipped)

    def done(self, line):
        raise Exception(f'Called after end of tests: {line!r}')

class MavenOutputParser:
    def __init__(self, runner, customPatternPreferences, logger):
        self.runner = runner
        self.customPatternPreferences = customPatternPreferences
        self.logger = logger

        self.state = self.output
        self.isReactorBuild = False
        self.currentPlugin = ('', '', '')

    def parse(self, line):
        try:
            self.state(line)
        except Exception as ex:
            raise Exception(f'Error processing {line!r}') from ex

    MODULE_START_PREFIX = '[INFO] Building '
    SUMMARY_START_PREFIX = '[INFO] Reactor Summary'
    MAVEN_PLUGIN_PREFIX = '[INFO] --- '
    MAVEN_PLUGIN_SUFFIX = ' ---'
    MAVEN_RESUME_PATTERN = re.compile(r'\[ERROR\]\s+mvn <[^>]+> -rf (\S+)')

    def output(self, line):
        if line == '[INFO] Reactor Build Order:':
            self.state = self.reactorBuildOrderSkipEmptyLine
            self.isReactorBuild = True
            return
        if line.startswith(self.MODULE_START_PREFIX):
            if self.currentPlugin[0] == 'maven-jar-plugin':
                self.runner.output.emit(line)
                return
            if self.currentPlugin[0] == 'maven-source-plugin':
                self.runner.output.emit(line)
                return

            self.detectedModuleStart(line[len(self.MODULE_START_PREFIX):])
            return
        if line.startswith(self.SUMMARY_START_PREFIX):
            self.delectedSummaryStart(line[len(self.SUMMARY_START_PREFIX):])
            return
        if line.startswith(self.MAVEN_PLUGIN_PREFIX) and line.endswith(self.MAVEN_PLUGIN_SUFFIX):
            rest = line[len(self.MAVEN_PLUGIN_PREFIX):-len(self.MAVEN_PLUGIN_SUFFIX)]
            self.detectedMavenPlugin(rest)
            return

        if line.startswith('[WARNING]'):
            self.runner.warning.emit(line[9:].strip())
            return
        if line.startswith('[ERROR]'):
            if ' -rf ' in line:
                match = self.MAVEN_RESUME_PATTERN.fullmatch(line)
                if match is not None:
                    resumeOption = match.group(1)
                    self.runner.resumeDetected.emit(resumeOption)
            
            self.runner.error.emit(line[7:].strip())
            return
        if line.startswith('[INFO] ') and line[7:].strip('-') == '':
            self.runner.hr.emit()
            return

        self.runner.output.emit(line)

    def reactorBuildOrderSkipEmptyLine(self, line):
        if line == '[INFO]':
            return

        self.state = self.reactorBuildOrder
        self.state(line)

    def reactorBuildOrder(self, line):
        if line == '[INFO]':
            self.state = self.output
            return

        pos1 = line.index(']')
        pos2 = line.find('[', pos1)
        if pos2 == -1:
            module = line[pos1+1:].strip()
            packaging = ''
        else:
            module = line[pos1+1:pos2].strip()
            packaging = line[pos2+1:-1]

        self.runner.reactorBuildOrder.emit(module, packaging)

    def detectedModuleStart(self, line):
        if self.isReactorBuild:
            pos1 = line.find('[')
            if pos1 == -1:
                namePlusVersion = line.strip()
            else:
                pos2 = line.index(']', pos1)
                namePlusVersion = line[:pos1].strip()
                progress = [int(x) for x in line[pos1+1:pos2].split('/')]

                self.runner.progress.emit(*progress)

            self.runner.mavenModule.emit(namePlusVersion)
        else:
            self.runner.mavenModule.emit(line)

    def detectedMavenPlugin(self, line):
        self.runner.mavenPlugin.emit(line.strip())
        
        self.currentPlugin = line.strip().split(' ')[0].split(':')
        
        if self.currentPlugin[0] == 'maven-surefire-plugin':
            self.detectedStartOfUnitTests()
        elif self.currentPlugin[0] == 'maven-dependency-plugin' and self.currentPlugin[2] == 'tree':
            self.state = self.parseDependencyTree
    
    def parseDependencyTree(self, line):
        if line.startswith('[INFO] ---------------') or line == '[INFO]':
            self.state = self.output
            self.output(line)
        elif line.startswith('[INFO] '):
            line = line[6:].strip()
            self.runner.dependencyTree.emit(line)
        else:
            self.runner.warning.emit(f'Unexpected output in dependency:tree: {line!r}')

    def detectedStartOfUnitTests(self):
        self.logger.log('MPARSER', 'Detected unit test start')
        self.testParser = UnitTestParser(self.runner, self.customPatternPreferences, self.logger)
        self.testParser.endOfTests.connect(self.endOfTests)
        self.state = self.parseUnitTests

    def parseUnitTests(self, line):
        self.testParser.parse(line)

    def endOfTests(self, numberOfTests, failures, errors, skipped):
        self.runner.testsFinished.emit(numberOfTests, failures, errors, skipped)
        self.state = self.output

    def delectedSummaryStart(self, line):
        self.state = self.reactorSummarySkipEmptyLine

    def reactorSummarySkipEmptyLine(self, line):
        if line == '[INFO]':
            return

        self.state = self.reactorSummary
        self.state(line)

    def reactorSummary(self, line):
        if line.startswith('[INFO] ---'):
            self.state = self.output
            return

        pos1 = line.index(']')
        pos2 = line.find('[', pos1)

        if pos2 == -1:
            moduleAndState = line[pos1+1:].strip()
            duration = ''
        else:
            moduleAndState = line[pos1+1:pos2].strip()
            duration = line[pos2+1:-1]

        pos3 = moduleAndState.rindex(' ')
        moduleWithDots = moduleAndState[:pos3]
        module = moduleWithDots.rstrip(' .')
        state = moduleAndState[pos3:].strip()

        self.runner.reactorSummary.emit(module, state, duration)

class MavenOutputProcessor(QThread):
    def __init__(self, runner, process, project, customPatternPreferences, logger):
        super().__init__()

        self.runner = runner
        self.process = process
        self.project = project
        self.customPatternPreferences = customPatternPreferences
        self.logger = logger

        self.parser = MavenOutputParser(self.runner, self.customPatternPreferences, self.logger)

    def run(self):
        try:
            self.runner.mavenStarted.emit(self.project, self.process.args)

            print('Reading from process')
            while True:
                line = self.process.stdout.readline()
                if line == '':
                    break

                line = line.rstrip()
                self.logger.log('MOUT', line)
                self.parser.parse(line)
        except:
            error = traceback.format_exc()
            self.runner.error.emit(error)
        finally: 
            rc = self.process.poll()
            self.runner.mavenFinished.emit(rc)

            if self.logger is not None:
                self.logger.close()

class MavenRunner(QObject):
    mavenStarted = pyqtSignal(Project, list) # project, args
    reactorBuildOrder = pyqtSignal(str, str) # module, packaging
    mavenModule = pyqtSignal(str) # coordinate
    mavenPlugin = pyqtSignal(str) # coordinate
    testsStarted = pyqtSignal()
    startedTest = pyqtSignal(str) # test name
    finishedTest = pyqtSignal(str, int, int, int, int, str) # currentTest, numberOfTests, failures, errors, skipped, duration
    testOutput = pyqtSignal(str) # line
    testsFinished = pyqtSignal(int, int, int, int) # numberOfTests, failures, errors, skipped
    reactorSummary = pyqtSignal(str, str, str) # module, status, duration
    output = pyqtSignal(str) # One line of text
    warning = pyqtSignal(str) # One line of text
    error = pyqtSignal(str) # Multi-line error message
    mavenFinished = pyqtSignal(int) # exit code
    progress = pyqtSignal(int, int) # current, max
    resumeDetected = pyqtSignal(str) # resumeOption
    hr = pyqtSignal() # Horizontal line
    dependencyTree = pyqtSignal(str) # dependency

    def __init__(self, project, customPatternPreferences, cmdLine, logger=None):
        super().__init__()

        self.project = project
        self.customPatternPreferences = customPatternPreferences
        self.cmdLine = cmdLine
        self.logger = logger

        self.osInfo = OsSpecificInfo()

    def start(self):
        logger = self.logger
        if logger is None:
            logger = self.createLogger()

        try:
            process = self.createMavenProcess()

            self.processor = MavenOutputProcessor(self, process, self.project, self.customPatternPreferences, logger)
            self.processor.start()
        except:
            error = traceback.format_exc()
            self.error.emit(error)

    def createLogger(self):
        timestamp = time.strftime('%Y-%m-%d_%H%M%S', time.localtime(time.time()))
        filename = f'pmg-{timestamp}.log'
        folder = Path(tempfile.gettempdir()) / 'PyMavenRunner'
        logger = FileLogger(folder / filename)
        return logger

    def createMavenProcess(self):
        args = [self.osInfo.mavenCommand]
        args.extend(self.cmdLine)
        args.append('-Dfile.encoding=UTF-8')
        args.append('-B')
        print(args)

        try:
            return subprocess.Popen(
                args,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                close_fds=True,
                cwd=self.project.path,
                encoding='UTF-8'
            )
        except Exception as ex:
            osPath = '\n'.join(self.osInfo.commandSearchPath())
            raise Exception(f'Unable to start process: {args!r}\nIs Maven on the path?\n{osPath}') from ex

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.projects = []
        self.preferences = QtPreferences()

        self.settings = QSettings('de.pdark', 'PyMavenRunner')
        self.loadSettings()        

        self.createUI()

    def loadSettings(self):
        self.settings.beginGroup('MainWindow')
        self._size = self.settings.value("size", QSize(800, 600))
        self._pos = self.settings.value("pos", QPoint(100, 100))
        self.settings.endGroup()
        
        self.loadProjects()

    def saveSettings(self):
        self.settings.beginGroup('MainWindow')
        self.settings.setValue("size", self.size())
        self.settings.setValue("pos", self.pos())
        self.settings.endGroup()
        
        self.saveProjects()

    def saveProjects(self):
        self.settings.beginWriteArray('projects')
        
        index = 0
        for it in self.projects:
            self.settings.setArrayIndex(index)
            index += 1
            
            self.settings.setValue('path', str(it.path))
        self.settings.endArray()
        print(f'Saved {index} projects ...')
        
        index = self.projects.index(self.header.currentProject)
        self.settings.setValue('currentProject', index)

    def loadProjects(self):
        n = self.settings.beginReadArray('projects')
        print(f'Loading {n} projects ...')
        for i in range(n):
            self.settings.setArrayIndex(i)
            
            path = Path(self.settings.value('path'))
            project = Project(path)
            
            self.projects.append(project)
        
        self.settings.endArray()
        
        self.currentProjectIndex = int(self.settings.value('currentProject', '0'))

    def closeEvent(self, event):
        self.header.saveProjectPreferences()
        self.saveSettings()

    def createUI(self):
        self.setWindowTitle(f"Python Maven Runner v{pmr.VERSION}")

        frame = QFrame(self)
        self.setCentralWidget(frame)

        self.header = MavenRunnerFrame(self.projects, self.preferences)
        self.header.startMaven.connect(self.startMaven)
        self.header.setCurrentProjectIndex(self.currentProjectIndex)

        self.logFrame = LogFrame(self.preferences)
        self.logView = self.logFrame.logView

        layout = QVBoxLayout(frame)
        layout.addWidget(self.header)
        layout.addWidget(self.logFrame)

        self.resize(self._size)
        self.move(self._pos)

    def startMaven(self, project, customPatternPreferences, args):
        print('Create MavenRunner')
        runner = MavenRunner(project, customPatternPreferences, args)

        runner.mavenStarted.connect(self.logFrame.mavenStarted)
        runner.error.connect(self.logFrame.error)
        runner.warning.connect(self.logFrame.warning)
        runner.output.connect(self.logFrame.output)
        runner.testOutput.connect(self.logFrame.testOutput)
        runner.mavenModule.connect(self.logFrame.mavenModule)
        runner.mavenPlugin.connect(self.logFrame.mavenPlugin)
        runner.reactorSummary.connect(self.logFrame.reactorSummary)
        runner.mavenFinished.connect(self.logFrame.mavenFinished)
        runner.startedTest.connect(self.logFrame.startedTest)

        runner.reactorBuildOrder.connect(self.logView.reactorBuildOrder)
        runner.hr.connect(self.logView.horizontalLine)
        runner.dependencyTree.connect(self.logView.dependencyTree)
        runner.testsStarted.connect(self.logView.testsStarted)
        runner.finishedTest.connect(self.logView.finishedTest)
        runner.testsFinished.connect(self.logView.testsFinished)

        runner.resumeDetected.connect(self.header.resumeDetected)

        print('Start background thread')
        runner.start()
