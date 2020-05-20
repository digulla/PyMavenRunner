#!python3
# -*- coding: utf-8 -*-

from PyQt5.QtCore import QRect
from pmr.ui import make_visible

SCREEN = QRect(0, 0, 1000, 800)
SECOND_MONITOR = QRect(100, 100, 800, 600)

def test_fully_visible():
    window = QRect(10, 10, 100, 100)
    actual = make_visible(SCREEN, window)
    assert actual == window

def test_fully_visible_2():
    window = QRect(110, 110, 100, 100)
    actual = make_visible(SECOND_MONITOR, window)
    assert actual == window

def test_outside_right():
    window = QRect(950, 10, 100, 100)
    actual = make_visible(SCREEN, window)

    assert actual == QRect(900, 10, 100, 100)

def test_outside_right_2():
    assert SECOND_MONITOR.width() == 800
    assert SECOND_MONITOR.left() == 100

    window = QRect(950, 110, 150, 100)
    actual = make_visible(SECOND_MONITOR, window)

    assert actual == QRect(750, 110, 150, 100)

def test_outside_bottom():
    window = QRect(10, 750, 100, 100)
    actual = make_visible(SCREEN, window)

    assert actual == QRect(10, 700, 100, 100)

def test_outside_bottom_right():
    window = QRect(1200, 1100, 100, 100)
    actual = make_visible(SCREEN, window)

    assert actual == QRect(900, 700, 100, 100)

def test_outside_left():
    window = QRect(-10, 10, 100, 100)
    actual = make_visible(SCREEN, window)

    assert actual == QRect(0, 10, 100, 100)

def test_outside_top():
    window = QRect(10, -10, 100, 100)
    actual = make_visible(SCREEN, window)

    assert actual == QRect(10, 0, 100, 100)

def test_outside():
    window = QRect(-10, -10, 1200, 1200)
    actual = make_visible(SCREEN, window)

    assert actual == SCREEN

def test_second_monitor():
    window = QRect(-10, -10, 1200, 1200)
    actual = make_visible(SECOND_MONITOR, window)

    assert actual == SECOND_MONITOR

