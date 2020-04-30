#!python3
# -*- coding: utf-8 -*-

import sys
import os

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
