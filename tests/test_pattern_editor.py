#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import PatternEditor
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import QEvent, Qt

def test_focusPreviousWidget(qtbot):
    editor = PatternEditor()
    
    with qtbot.waitSignal(editor.focusPreviousWidget) as blocker:
        qtbot.keyPress(editor, Qt.Key_Left)
    
    assert blocker.args == []
    
def test_focusNextWidget(qtbot):
    editor = PatternEditor()
    
    with qtbot.waitSignal(editor.focusNextWidget) as blocker:
        qtbot.keyPress(editor, Qt.Key_Right)
    
    assert blocker.args == []

def test_enter_return_without_ctrl(qtbot):
    editor = PatternEditor()
    
    with qtbot.assertNotEmitted(editor.accept, wait=100) as blocker:
        qtbot.keyPress(editor, Qt.Key_Enter)
        qtbot.keyPress(editor, Qt.Key_Return)

def test_enter_with_ctrl(qtbot):
    editor = PatternEditor()

    with qtbot.waitSignal(editor.accept) as blocker:
        qtbot.keyPress(editor, Qt.Key_Enter, Qt.ControlModifier)
    
    assert blocker.args == []

def test_return_with_ctrl(qtbot):
    editor = PatternEditor()

    with qtbot.waitSignal(editor.accept) as blocker:
        qtbot.keyPress(editor, Qt.Key_Return, Qt.ControlModifier)
    
    assert blocker.args == []
