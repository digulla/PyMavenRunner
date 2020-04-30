#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import PatternEditor
from PyQt5.QtGui import QKeyEvent
from PyQt5.QtCore import QEvent, Qt

def createKeyPressEvent(key, modifier=Qt.NoModifier):
    return QKeyEvent(QEvent.KeyPress, key, modifier, 0, 0, 0)

def test_focusPreviousWidget(qtbot):
    editor = PatternEditor()
    event = createKeyPressEvent(Qt.Key_Left)
    
    with qtbot.waitSignal(editor.focusPreviousWidget) as blocker:
        editor.keyPressEvent(event)
    
    assert blocker.args == []
    
def test_focusNextWidget(qtbot):
    editor = PatternEditor()
    event = createKeyPressEvent(Qt.Key_Right)
    
    with qtbot.waitSignal(editor.focusNextWidget) as blocker:
        editor.keyPressEvent(event)
    
    assert blocker.args == []

def test_enter_return_without_ctrl(qtbot):
    editor = PatternEditor()
    
    with qtbot.assertNotEmitted(editor.accept, wait=100) as blocker:
        event = createKeyPressEvent(Qt.Key_Enter)
        editor.keyPressEvent(event)
        event = createKeyPressEvent(Qt.Key_Return)
        editor.keyPressEvent(event)

def test_enter_with_ctrl(qtbot):
    editor = PatternEditor()

    with qtbot.waitSignal(editor.accept) as blocker:
        event = createKeyPressEvent(Qt.Key_Enter, Qt.ControlModifier)
        editor.keyPressEvent(event)
    
    assert blocker.args == []

def test_return_with_ctrl(qtbot):
    editor = PatternEditor()

    with qtbot.waitSignal(editor.accept) as blocker:
        event = createKeyPressEvent(Qt.Key_Return, Qt.ControlModifier)
        editor.keyPressEvent(event)
    
    assert blocker.args == []
