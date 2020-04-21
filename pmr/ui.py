#!python3
# -*- coding: utf-8 -*-

try:
    from PyQt5.QtWidgets import (
        QAbstractItemView,
        QApplication,
        QCheckBox,
        QComboBox,
        QErrorMessage,
        QFileDialog,
        QFrame,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QPushButton,
        QShortcut,
        QSizePolicy,
        QSplitter,
        QTextEdit,
        QTreeWidget,
        QTreeWidgetItem,
        QVBoxLayout,
    )
    from PyQt5.QtGui import (
        QBrush,
        QColor,
        QFont,
        QFontDatabase,
        QTextCharFormat,
        QTextCursor,
        QTextFormat,
        QTextFrameFormat,
        QTextTableFormat,
    )
    from PyQt5.QtCore import (
        pyqtSignal,
        QObject,
        QPoint,
        QSettings,
        QSize,
        Qt,
        QThread,
    )
except:
    # Cygwin
    print("Please install python3-pyqt and python3-sip")
    raise

from pathlib import Path
import subprocess
import traceback
import time
import datetime
import re
import os
import sys
import pmr

class OsSpecificInfo:
    def __init__(self):
        self.commandSearchPathSep = ':'
        self.mavenCommand = 'mvn'

        if sys.platform == 'win32':
            self.initWin32()

    def initWin32(self):
        self.commandSearchPathSep = ';'
        self.mavenCommand = 'mvn.cmd'

    def commandSearchPath(self):
        raw = os.environ['PATH']
        return raw.split(self.commandSearchPathSep)

class Project:
    def __init__(self, path):
        self.path = path
        self.name = path.name

class MavenRunnerFrame(QFrame):
    startMaven = pyqtSignal(Project, list)

    def __init__(self, projects, parent = None):
        super().__init__(parent)
        
        self.lastPath = Path.cwd()
        self.projects = projects

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
        run.clicked.connect(self.startMavenClicked)
        hbox.addWidget(run)

        self.resumeButton = QPushButton('Resume')
        self.resumeButton.setShortcut('Alt+S')
        self.resumeButton.setEnabled(False)
        self.resumeButton.clicked.connect(self.resumeMavenClicked)
        hbox.addWidget(self.resumeButton)

        self.skipTestsButton = QCheckBox('Skip Tests')
        hbox.addWidget(self.skipTestsButton)

        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        self.projectSelector.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        run.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.resumeButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))
        self.addProjectButton.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

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
        self.currentProject = self.projects[index]
        print(f'Selected project "{self.currentProject.name}"')

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
        self.startMaven.emit(self.currentProject, args)

class LogView(QTextEdit):
    def __init__(self, parent = None):
        super().__init__(parent)

        self.cursor = QTextCursor(self.document())
        self.reactorBuildOrderTable = None
        self.reactorSummaryTable = None

        self.defaultFormat = QTextCharFormat(self.currentCharFormat())

        self.moduleFormat = QTextCharFormat()
        self.moduleFormat.setFontWeight(QFont.Bold)
        self.moduleFormat.setFontPointSize(self.currentFont().pointSize() * 18 / 10)

        self.testHeaderFormat = QTextCharFormat()
        self.testHeaderFormat.setFontWeight(QFont.Bold)
        self.testHeaderFormat.setFontPointSize(self.currentFont().pointSize() * 14 / 10)

        self.testFormat = QTextCharFormat()
        self.testFormat.setFontWeight(QFont.Bold)
        self.testFormat.setFontPointSize(self.currentFont().pointSize() * 12 / 10)

        self.mavenPluginFormat = QTextCharFormat()
        self.mavenPluginFormat.setFontWeight(QFont.Bold)

        fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(QBrush(Qt.darkRed))
        self.errorFormat.setFont(fixedFont)

        self.warningFormat = QTextCharFormat()
        self.warningFormat.setForeground(QBrush(Qt.darkYellow))
        self.warningFormat.setFont(fixedFont)

        self.tableFormat = QTextTableFormat()
        #print(dir(self.tableFormat))
        # TODO Qt 5.14
        #self.tableFormat.setBorderCollapse(True)
        self.tableFormat.setCellPadding(2.0)
        self.tableFormat.setCellSpacing(0)
        self.tableFormat.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)

        self.successBackground = QBrush(QColor('lime'))
        self.failureBackground = QBrush(Qt.red)

        self.append('Ready.')

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
        text = f'Finished {name} #of Tests: {numberOfTests} Failures: {failures} Errors: {errors} Skipped: {skipped} Time elapsed: {duration}'
        self.appendLine(text, self.testFormat)
        
        # TODO collapse test output

    def testsFinished(self, numberOfTests, failures, errors, skipped):
        text = f'Tests run: {numberOfTests} Failures: {failures} Errors: {errors} Skipped: {skipped}'
        self.appendLine(text, self.testHeaderFormat)

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
            background = self.successBackground
        elif state == 'FAILURE':
            background = self.failureBackground
        blockFormat.setBackground(background)
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

class LogFrame(QFrame):
    NodeTypeRole = Qt.UserRole + 1
    TextPositionRole = Qt.UserRole + 2
    
    NT_Module, NT_Plugin, NT_Anchor = range(3)
    
    def __init__(self, parent = None):
        super().__init__(parent)

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

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        layout.addWidget(splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.clicked.connect(self.treeNodeClicked)
        splitter.addWidget(self.tree)
        
        self.logView = LogView()
        splitter.addWidget(self.logView)

        splitter.setStretchFactor(0, 30)
        splitter.setStretchFactor(1, 70)
        
        self.warningBrush = QBrush(Qt.darkYellow)
        self.errorBrush = QBrush(Qt.darkRed)

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
    
    def mavenFinished(self, rc):
        self.state = 'Done'
        self.updateStatistics()
        
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
    
    def reactorSummary(self, *args):
        if self.addedReactorSummary:
            return
        
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
    
    def mavenPlugin(self, coordinate):
        item = QTreeWidgetItem()
        item.setText(0, coordinate)
        self.saveTextPosition(item)
        
        self.currentModule.addChild(item)
        self.scrollToItem(item)
        item.setExpanded(True)
        self.currentPlugin = item
        self.lastLeaf = None
    
    def startedTest(self, name):
        item = QTreeWidgetItem()
        item.setText(0, name)
        self.saveTextPosition(item)
        
        self.currentPlugin.addChild(item)
        self.scrollToItem(item)
        self.lastLeaf = None
    
    def saveTextPosition(self, item):
        pos = self.logView.cursor.position()
        item.setData(0, self.TextPositionRole, pos)
    
    def warning(self, message):
        self.warnings += 1
        self.updateStatistics()
        self.addLeaf(message, type='warning', foreground=self.warningBrush)

    def error(self, message):
        self.errors += 1
        self.updateStatistics()
        self.addLeaf(message, type='error', foreground=self.errorBrush)

    def output(self, *args):
        self.lastLeaf = None
        
    def testOutput(self, *args):
        self.lastLeaf = None

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
    
    def __init__(self, runner):
        super().__init__()

        self.runner = runner
        
        self.state = self.skipTestHeaders
        self.linesWithDashes = 0
        self.lastFewLines = []
        
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

    ERROR_PATTERN = re.compile('ERROR|^\tat ')
    WARNING_PATTERN = re.compile('WARN( |NING)')

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
        
        match = self.ERROR_PATTERN.search(line)
        if match is not None:
            self.runner.error.emit(line)
            return
        
        match = self.WARNING_PATTERN.search(line)
        if match is not None:
            self.runner.warning.emit(line)
            return
        
        self.runner.testOutput.emit(line)
    
    def wasSomethingElse(self):
        #print('wasSomethingElse')
        for line in self.lastFewLines:
            self.runner.testOutput.emit(line)
        
        self.lastFewLines = []
        self.state = self.parseUnitTestOutput
    
    def mightBeEndOfTests1(self, line):
        #print('mightBeEndOfTests1', line)
        self.lastFewLines.append(line)
        if line == 'Results :':
            self.state = self.mightBeEndOfTests2
        elif line == '':
            return
        else:
            self.wasSomethingElse()
    
    def mightBeEndOfTests2(self, line):
        #print('mightBeEndOfTests2', line)
        self.lastFewLines.append(line)
        if line == '':
            self.state = self.mightBeEndOfTests3
        else:
            self.wasSomethingElse()
    
    def mightBeEndOfTests3(self, line):
        #print('mightBeEndOfTests3', line)
        self.lastFewLines.append(line)
        if line.startswith('Tests run: '):
            self.testSummaryLine = line
            self.state = self.mightBeEndOfTests5
        elif line.startswith('Failed tests: '):
            self.state = self.mightBeEndOfTests4
        else:
            self.wasSomethingElse()
    
    def mightBeEndOfTests4(self, line):
        #print('mightBeEndOfTests4', line)
        if line.startswith('Tests run: '):
            self.testSummaryLine = line
            self.state = self.mightBeEndOfTests5
            return
        
        self.runner.error.emit(line)
    
    def mightBeEndOfTests5(self, line):
        #print(f'mightBeEndOfTests5 {line!r}')
        if line.startswith('[INFO]'):
            self.lastFewLines = []
            self.emitTestSummary()
            self.state = self.done

    def emitTestSummary(self):
        #print('emitTestSummary')
        match = self.TESTS_FINISHED_PATTERN.fullmatch(self.testSummaryLine)
        if match is None:
            raise Exception(f"Can't parse final test result: {result!r}")
        
        numberOfTests = int(match.group(1))
        failures = int(match.group(2))
        errors = int(match.group(3))
        skipped = int(match.group(4))
        
        #print('END_OF_TESTS')
        self.endOfTests.emit(numberOfTests, failures, errors, skipped)

    def done(self, line):
        raise Exception(f'Called after end of tests: {line!r}')

class MavenOutputParser:
    def __init__(self, runner):
        self.runner = runner

        self.state = self.output
        self.isReactorBuild = False
        self.currentPlugin = ('', '', '')

    def parse(self, line):
        print(line)
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
    
    def detectedStartOfUnitTests(self):
        self.testParser = UnitTestParser(self.runner)
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
        pos2 = line.index('[', pos1)

        moduleAndState = line[pos1+1:pos2].strip()
        duration = line[pos2+1:-1]

        pos3 = moduleAndState.rindex(' ')
        moduleWithDots = moduleAndState[:pos3]
        module = moduleWithDots.rstrip(' .')
        state = moduleAndState[pos3:].strip()

        self.runner.reactorSummary.emit(module, state, duration)

class MavenOutputProcessor(QThread):
    def __init__(self, runner, process, project):
        super().__init__()

        self.runner = runner
        self.process = process
        self.project = project

        self.parser = MavenOutputParser(runner)

    def run(self):
        try:
            self.runner.mavenStarted.emit(self.project, self.process.args)

            print('Reading from process')
            while True:
                line = self.process.stdout.readline()
                if line == '':
                    break

                self.parser.parse(line.rstrip())
        except:
            error = traceback.format_exc()
            self.runner.error.emit(error)
        finally: 
            rc = self.process.poll()
            self.runner.mavenFinished.emit(rc)

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

    def __init__(self, project, cmdLine):
        super().__init__()

        self.project = project
        self.cmdLine = cmdLine

    def start(self):
        try:
            process = self.createMavenProcess()

            self.processor = MavenOutputProcessor(self, process, self.project)
            self.processor.start()
        except:
            error = traceback.format_exc()
            self.error.emit(error)

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
        self.saveSettings()

    def createUI(self):
        self.setWindowTitle(f"Python Maven Runner v{pmr.VERSION}")

        frame = QFrame(self)
        self.setCentralWidget(frame)

        self.header = MavenRunnerFrame(self.projects)
        self.header.startMaven.connect(self.startMaven)
        self.header.setCurrentProjectIndex(self.currentProjectIndex)

        self.logFrame = LogFrame()
        self.logView = self.logFrame.logView

        layout = QVBoxLayout(frame)
        layout.addWidget(self.header)
        layout.addWidget(self.logFrame)

        self.resize(self._size)
        self.move(self._pos)

    def startMaven(self, project, args):
        print('Create MavenRunner')
        runner = MavenRunner(project, args)

        runner.mavenStarted.connect(self.logFrame.mavenStarted)
        runner.mavenStarted.connect(self.logView.mavenStarted)
        runner.reactorBuildOrder.connect(self.logView.reactorBuildOrder)
        runner.error.connect(self.logFrame.error)
        runner.error.connect(self.logView.error)
        runner.warning.connect(self.logFrame.warning)
        runner.warning.connect(self.logView.warning)
        runner.output.connect(self.logFrame.output)
        runner.output.connect(self.logView.appendLine)
        runner.testOutput.connect(self.logFrame.testOutput)
        runner.testOutput.connect(self.logView.testOutput)
        runner.mavenModule.connect(self.logFrame.mavenModule)
        runner.mavenModule.connect(self.logView.mavenModule)
        runner.mavenPlugin.connect(self.logFrame.mavenPlugin)
        runner.mavenPlugin.connect(self.logView.mavenPlugin)
        runner.reactorSummary.connect(self.logFrame.reactorSummary)
        runner.reactorSummary.connect(self.logView.reactorSummary)
        runner.mavenFinished.connect(self.logFrame.mavenFinished)
        runner.mavenFinished.connect(self.logView.mavenFinished)
        
        runner.testsStarted.connect(self.logView.testsStarted)
        runner.startedTest.connect(self.logFrame.startedTest)
        runner.startedTest.connect(self.logView.startedTest)
        runner.finishedTest.connect(self.logView.finishedTest)
        runner.testsFinished.connect(self.logView.testsFinished)

        runner.resumeDetected.connect(self.header.resumeDetected)

        print('Start background thread')
        runner.start()
