#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import QtPreferences, LogFrame
from pathlib import Path

def test_maven_started(qtbot, qtmodeltester):
	prefs = QtPreferences()
	widget = LogFrame(prefs)
	qtbot.addWidget(widget)

	# TODO Core dump
	#qtmodeltester.check(widget.tree.model())
	# TODO Core dump!!! How?
	#qtmodeltester.check(widget.tree.model(), force_py=True)

	project = Project(Path('Foo'))
	args = ['mvn', 'clean', 'install']
	widget.mavenStarted(project, args)

def test_reactorSummary(qtbot):
	prefs = QtPreferences()
	widget = LogFrame(prefs)
	qtbot.addWidget(widget)

	widget.reactorSummary('foo', 'SUCCESS', '1 s')

def test_hierarchy(qtbot, qtmodeltester):
	prefs = QtPreferences()
	widget = LogFrame(prefs)
	qtbot.addWidget(widget)

	widget.mavenModule('foo:1.0')
	widget.mavenPlugin('maven-surefire-plugin:2.12.4:test')
	widget.startedTest('whatever')
	widget.warning('WARN')
	widget.error('ERROR')
	widget.startedTest('next test')

	# TODO Core dump
	#qtmodeltester.check(widget.tree.model())