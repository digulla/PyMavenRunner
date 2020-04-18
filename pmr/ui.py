#!python3
# -*- coding: utf-8 -*-

try:
    from PyQt5.QtWidgets import QMainWindow, QFrame, QApplication, QVBoxLayout, QPushButton, QLineEdit, QTreeWidget, QTextEdit, QHBoxLayout, QSplitter, QSizePolicy, QLabel, QComboBox, QShortcut, QTreeWidgetItem
    from PyQt5.QtGui import QTextCursor, QFont, QTextCharFormat, QBrush, QTextFormat, QFontDatabase, QTextTableFormat, QTextFrameFormat
    from PyQt5.QtCore import Qt, pyqtSignal, QObject, QThread
except:
    print("Please install python3-pyqt and python3-sip")
    raise

from pathlib import Path
import subprocess
import traceback

class Project:
    def __init__(self, path):
        self.path = path
        self.name = path.name

class MavenRunnerFrame(QFrame):
    startMaven = pyqtSignal(Project, list)

    def __init__(self, parent = None):
        super().__init__(parent)

        devFolder = Path.home() / 'dev'
        self.projects = [
            Project(devFolder / 'foo'),
            Project(devFolder / 'bar'),
        ]

        layout = QVBoxLayout(self)

        hbox = QHBoxLayout()
        label = QLabel('Project:')
        hbox.addWidget(label)

        projectSelector = QComboBox()
        projectSelector.addItems([it.name for it in self.projects])
        projectSelector.setCurrentIndex(1)
        self.currentProject = self.projects[1]
        projectSelector.activated[str].connect(self.changeProject)
        hbox.addWidget(projectSelector)

        addProject = QPushButton('Add...')
        hbox.addWidget(addProject)

        self.mavenCmd = QLineEdit()
        self.mavenCmd.setText('mvn clean install')
        self.mavenCmd.setText('mvn -version')
        self.mavenCmd.setText('mvn clean')

        run = QPushButton('Run')
        run.setShortcut('Alt+R')
        run.clicked.connect(self.startMavenClicked)

        #self.runShortcut = QShortcut('Alt+R', self.startMavenClicked)

        layout.addLayout(hbox)
        layout.addWidget(self.mavenCmd)
        layout.addWidget(run)

        self.setSizePolicy(QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed))
        run.setSizePolicy(QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed))

    def changeProject(self, name):
        selected = [it for it in self.projects if it.name == name]
        if len(selected) == 1:
            self.currentProject = selected[0]
            print(f'Selected "{self.currentProject.name}"')
        else:
            raise Exception(f'Unknown project {name}')

    def startMavenClicked(self):
        cmdLine = self.mavenCmd.text().split(' ')
        print('startMavenClicked')
        self.startMaven.emit(self.currentProject, cmdLine)

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

        fixedFont = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(QBrush(Qt.darkRed))
        self.errorFormat.setFont(fixedFont)

        self.tableFormat = QTextTableFormat()
        #print(dir(self.tableFormat))
        # TODO Qt 5.14
        #self.tableFormat.setBorderCollapse(True)
        self.tableFormat.setCellPadding(2.0)
        self.tableFormat.setCellSpacing(0)
        self.tableFormat.setBorderStyle(QTextFrameFormat.BorderStyle_Solid)

        self.append('Ready.')

    def clear(self):
        self.setHtml('')
        self.cursor.setPosition(0)

    def append(self, text):
        self.cursor.movePosition(QTextCursor.End)
        self.cursor.insertText(text)

    def appendLine(self, text, format=None):
        if format is None:
            format = self.defaultFormat

        self.cursor.movePosition(QTextCursor.End)
        self.cursor.insertText(text, format)
        self.cursor.insertText('\n')

    def mavenStarted(self, project, args):
        self.clear()
        cmdLine = ' '.join(args)
        self.appendLine(f'Started Maven in {project.path}: {cmdLine}')

    def mavenModule(self, coordinate):
        self.appendLine(coordinate, self.moduleFormat)

    def error(self, message):
        self.appendLine(message, self.errorFormat)

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
        cell.firstCursorPosition().insertText(state)
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
    def __init__(self, parent = None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Horizontal)
        layout.addWidget(splitter)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        splitter.addWidget(self.tree)
        self.logView = LogView()
        splitter.addWidget(self.logView)

        splitter.setStretchFactor(0, 30)
        splitter.setStretchFactor(1, 70)

    def mavenModule(self, coordinate):
        item = QTreeWidgetItem()
        item.setText(0, coordinate)
        self.tree.addTopLevelItem(item)

class MavenOutputParser:
    def __init__(self, runner):
        self.runner = runner

        self.state = self.output
        self.isReactorBuild = False

    def parse(self, line):
        print(line)
        try:
            self.state(line)
        except Exception as ex:
            raise Exception(f'Error processing {line!r}') from ex

    MODULE_START_PREFIX = '[INFO] Building '
    SUMMARY_START_PREFIX = '[INFO] Reactor Summary for '

    def output(self, line):
        if line == '[INFO] Reactor Build Order:':
            self.state = self.reactorBuildOrderSkipEmptyLine
            self.isReactorBuild = True
            return
        if line.startswith(self.MODULE_START_PREFIX):
            self.detectedModuleStart(line[len(self.MODULE_START_PREFIX):])
            return
        if line.startswith(self.SUMMARY_START_PREFIX):
            self.delectedSummaryStart(line[len(self.SUMMARY_START_PREFIX):])

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
        pos2 = line.index('[', pos1)

        module = line[pos1+1:pos2].strip()
        packaging = line[pos2+1:-1]

        self.runner.reactorBuildOrder.emit(module, packaging)

    def detectedModuleStart(self, line):
        if self.isReactorBuild:
            pos1 = line.index('[')
            pos2 = line.index(']', pos1)
            namePlusVersion = line[:pos1].strip()
            progress = [int(x) for x in line[pos1+1:pos2].split('/')]

            self.runner.mavenModule.emit(namePlusVersion)
            self.runner.progress.emit(*progress)
        else:
            self.runner.mavenModule.emit(line)

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
                if line == '' and self.process.poll() is not None:
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
    mavenModule = pyqtSignal(str) # coordînate
    startedTest = pyqtSignal(str) # test name
    finishedTest = pyqtSignal(str, str) # test name, status
    testsFinished = pyqtSignal(str) # Overall test result
    reactorSummary = pyqtSignal(str, str, str) # module, status, duration
    output = pyqtSignal(str) # One line of text
    error = pyqtSignal(str) # Multi-line error message
    mavenFinished = pyqtSignal(int) # exit code
    progress = pyqtSignal(int, int) # current, max

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
        args = list(self.cmdLine)
        args.append('-Dfile.encoding=UTF-8')
        args.append('-B')
        print(args)

        return subprocess.Popen(
            args,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            close_fds=True,
            cwd=self.project.path,
            encoding='UTF-8'
        )

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.createUI()

    def createUI(self):
        self.setWindowTitle("Python Maven Runner v0.1")

        frame = QFrame(self)
        self.setCentralWidget(frame)

        header = MavenRunnerFrame()
        header.startMaven.connect(self.startMaven)
        self.logFrame = LogFrame()
        self.logView = self.logFrame.logView

        layout = QVBoxLayout(frame)
        layout.addWidget(header)
        layout.addWidget(self.logFrame)

        self.resize (800, 600)

    def startMaven(self, project, args):
        print('Create MavenRunner')
        runner = MavenRunner(project, args)

        runner.mavenStarted.connect(self.logView.mavenStarted)
        runner.reactorBuildOrder.connect(self.logView.reactorBuildOrder)
        runner.error.connect(self.logView.error)
        runner.output.connect(self.logView.appendLine)
        runner.mavenModule.connect(self.logView.mavenModule)
        runner.mavenModule.connect(self.logFrame.mavenModule)
        runner.reactorSummary.connect(self.logView.reactorSummary)
        runner.mavenFinished.connect(self.logView.mavenFinished)

        print('Start background thread')
        runner.start()
