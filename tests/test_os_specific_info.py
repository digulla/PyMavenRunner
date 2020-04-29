#!python3
# -*- coding: utf-8 -*-

from pmr.ui import OsSpecificInfo
from pathlib import Path

def test_search_path():
    tool = OsSpecificInfo()
    path = tool.commandSearchPath()

    for it in path:
        maybe = Path(it) / tool.mavenCommand
        if maybe.exists():
            return

    raise Exception(f'{tool.mavenCommand} not found in {path}')
