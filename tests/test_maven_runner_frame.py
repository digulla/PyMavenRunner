#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pmr.ui import QtPreferences, MavenRunnerFrame
from pathlib import Path

rootFolder = Path(__file__).parent.parent.resolve()

def test_no_projects(qtbot):
	projects = []
	prefs = QtPreferences()
	widget = MavenRunnerFrame(projects, prefs)

	assert not widget.projectSelector.enabled

def createWithMultiModuleProject():
    projects = []
    prefs = QtPreferences()
    widget = MavenRunnerFrame(projects, prefs)

    path = rootFolder / 'it' / 'multi-module-project'
    widget.addProject(path)
    
    return widget

def test_add_project(qtbot):
    widget = createWithMultiModuleProject()
    
    assert widget.projectSelector.enabled
    assert widget.currentProject is not None
    assert widget.projectPreferences is not None
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.startMavenClicked()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['clean', 'install'],
    ]

def test_skip_tests(qtbot):
    widget = createWithMultiModuleProject()
    
    widget.skipTestsButton.setChecked(True)
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['clean', 'install', '-DskipTests'],
    ]

def test_resume_detected(qtbot):
    widget = createWithMultiModuleProject()

    widget.resumeDetected('foo')
    
    assert widget.resumeButton.isEnabled()
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.resumeMavenClicked()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['-rf', 'foo', 'clean', 'install'],
    ]

def test_resume_detected(qtbot):
    widget = createWithMultiModuleProject()

    widget.resumeDetected('foo')
    assert widget.resumeButton.isEnabled()
    
    widget.mavenFinished(0)
    assert not widget.resumeButton.isEnabled()

def test_extra_options(qtbot):
    widget = createWithMultiModuleProject()

    widget.mavenCmd.setText('--show-version --threads 2.0C')
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven(False)

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['clean', 'install', '--show-version', '--threads', '2.0C'],
    ]
