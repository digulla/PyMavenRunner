#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import QtPreferences, LogFrame
from pathlib import Path

def test_maven_started(qtbot):
	prefs = QtPreferences()
	widget = LogFrame(prefs)

	project = Project(Path('Foo'))
	args = ['mvn', 'clean', 'install']
	widget.mavenStarted(project, args)

def test_reactorSummary(qtbot):
	prefs = QtPreferences()
	widget = LogFrame(prefs)

	widget.reactorSummary('foo', 'SUCCESS', '1 s')

def test_hierarchy(qtbot):
	prefs = QtPreferences()
	widget = LogFrame(prefs)

	widget.mavenModule('foo:1.0')
	widget.mavenPlugin('maven-surefire-plugin:2.12.4:test')
	widget.startedTest('whatever')
	widget.warning('WARN')
	widget.error('ERROR')
	widget.startedTest('next test')
