#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import QtPreferences, MavenRunnerFrame

def test_no_projects(qtbot):
	projects = []
	prefs = QtPreferences()
	widget = MavenRunnerFrame(projects, prefs)

	assert not widget.projectSelector.enabled
