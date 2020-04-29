#!python3
# -*- coding: utf-8 -*-

from pmr.ui import LevelEditor

choices = [
    ('a', 1),
    ('b', 2),
]

def test_init(qtbot):
    editor = LevelEditor(choices)
    assert [
        editor.currentIndex(),
        editor.currentData(),
        editor.currentText()
    ] == [0, 1, 'a']

def test_init(qtbot):
    editor = LevelEditor(choices)
    
    with qtbot.waitSignal(editor.levelChanged) as blocker:
        editor.setLevel(2)

    assert blocker.args == [2]

    assert [
        editor.currentIndex(),
        editor.currentData(),
        editor.currentText()
    ] == [1, 2, 'b']
