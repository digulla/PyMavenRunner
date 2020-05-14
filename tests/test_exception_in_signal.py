#!python3
# -*- coding: utf-8 -*-
'''
Attempt to track down a "Windows fatal exception: access violation"
crash deep in pytest-qt.

For some reason, the code here works but when I change the comments in
ui.py, it always crashes :-(


Current thread 0x000044c4 (most recent call first):
  File "$PYTHON_HOME/Python37/lib/site-packages/pytestqt/plugin.py", line 197 in _process_events
  File "$PYTHON_HOME/Python37/lib/site-packages/pytestqt/plugin.py", line 166 in pytest_runtest_call
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/callers.py", line 203 in _multicall
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 87 in <lambda>
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 93 in _hookexec
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/hooks.py", line 286 in __call__
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/runner.py", line 217 in <lambda>
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/runner.py", line 244 in from_call
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/runner.py", line 217 in call_runtest_hook
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/runner.py", line 186 in call_and_report
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/runner.py", line 100 in runtestprotocol
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/runner.py", line 85 in pytest_runtest_protocol
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/callers.py", line 187 in _multicall
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 87 in <lambda>
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 93 in _hookexec
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/hooks.py", line 286 in __call__
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/main.py", line 272 in pytest_runtestloop
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/callers.py", line 187 in _multicall
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 87 in <lambda>
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 93 in _hookexec
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/hooks.py", line 286 in __call__
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/main.py", line 247 in _main
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/main.py", line 191 in wrap_session
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/main.py", line 240 in pytest_cmdline_main
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/callers.py", line 187 in _multicall
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 87 in <lambda>
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/manager.py", line 93 in _hookexec
  File "$PYTHON_HOME/python37/lib/site-packages/pluggy/hooks.py", line 286 in __call__
  File "$PYTHON_HOME/python37/lib/site-packages/_pytest/config/__init__.py", line 125 in main
  File "$PYTHON_HOME/Python37/Scripts/pytest.exe/__main__.py", line 9 in <module>
  File "$PYTHON_HOME/python37/lib/runpy.py", line 85 in _run_code
  File "$PYTHON_HOME/python37/lib/runpy.py", line 193 in _run_module_as_main

'''

from PyQt5.QtWidgets import QToolTip
from PyQt5.QtCore import pyqtSignal
from pmr.ui import CustomPatternDialog, CustomPatternTable, QtPreferences
from pmr.model import *
from pathlib import Path

class BadCustomPatternTable(CustomPatternTable):
    def __init__(self, matchers, parent=None):
        super().__init__(matchers, parent)

    def handleException(self, index, matcherConfig, ex):
        msg = str(ex)
        QToolTip.showText(self.rect().topLeft(), msg, self)

class BadCustomPatternDialog(CustomPatternDialog):
    emitException = pyqtSignal(int, BaseMatcherConfig, Exception) # index, matcherConfig, exception message

    def __init__(self, preferences, customPatternPreferences, parent):
        super().__init__(preferences, customPatternPreferences, parent)

        self.emitException.connect(self.patternTable.handleException)

    def createCustomPatternTable(self, matchers):
        return BadCustomPatternTable(matchers)

    def runDebugger(self):
        #print('runDebugger')
        matchers = []
        for index, it in enumerate(self.matchers):
            try:
                m = it.createMatcher()
                matchers.append(m)
            except Exception as ex:
                self.emitException.emit(index, it, ex)

def createEmptyDialog():
    project = Project(Path('Foo'))
    defaults = Defaults(CustomPatternEmptyDefaults())
    preferences = ProjectPreferences(project, defaults)
    
    qtPrefs = QtPreferences()
    return BadCustomPatternDialog(qtPrefs, preferences.customPatternPreferences, None)

def test_illegal_regex(qtbot):
    dialog = createEmptyDialog()
    qtbot.addWidget(dialog)
    
    with qtbot.waitSignal(dialog.patternTable.patternsChanged) as blocker:
        dialog.patternTable.addRegex()
    
    assert len(dialog.patternTable.patternEditors) == 1

    with qtbot.waitSignal(dialog.emitException) as blocker:
        dialog.matchers[-1].pattern = '('
        dialog.patternsChanged(dialog.matchers)
