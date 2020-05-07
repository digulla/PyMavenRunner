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
    qtbot.addWidget(widget)
    
    widget.skipTestsButton.setChecked(True)
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['clean', 'install', '-DskipTests'],
    ]

def getStartOptionState(widget):
    option = widget.startOptionWidget.currentData()

    visible = []
    if widget.modulesSingleSelectionVisible:
        visible.append('singleSelection')
    if widget.modulesMultiSelectionVisible:
        visible.append('multiSelection')

    enabled = []
    if widget.modulesSingleSelection.isEnabled():
        enabled.append('singleSelection')
    if widget.modulesMultiSelection.isEnabled():
        enabled.append('multiSelection')

    selected = []
    if widget.modulesSingleSelectionVisible:
        selected.append(widget.modulesSingleSelection.currentData())
    if widget.modulesMultiSelectionVisible:
        raise Exception('TODO')

    return {
        'startOption': MavenPreferences.START_OPTION_NAMES[option],
        'visible': visible,
        'enabled': enabled,
        'selected': selected,
    }

def test_resume_detected(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)
    #widget.show()

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.resumeDetected(':IT2-module1')
    
    actual = getStartOptionState(widget)
    assert actual == {
        'startOption': 'START_WITH',
        'visible': ['singleSelection'],
        'enabled': ['singleSelection'],
        'selected': ['de.pdark.python.pmr.it2:IT2-module1'],
    }
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['--resume-from', 'de.pdark.python.pmr.it2:IT2-module1', 'clean', 'install'],
    ]

def test_build_all_after_resume(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)
    #widget.show()

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.resumeDetected(':IT2-module1')

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.setStartOption(MavenPreferences.START_ALL)
    
    actual = getStartOptionState(widget)
    assert actual == {
        'startOption': 'START_ALL',
        'visible': ['singleSelection'],
        'enabled': [],
        'selected': ['de.pdark.python.pmr.it2:IT2-parent'],
    }
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['clean', 'install'],
    ]

def test_start_with(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)
    #widget.show()

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.setStartOption(MavenPreferences.START_WITH)
        widget.modulesSingleSelection.setCurrentIndex(1)
    
    actual = getStartOptionState(widget)
    assert actual == {
        'startOption': 'START_WITH',
        'visible': ['singleSelection'],
        'enabled': ['singleSelection'],
        'selected': ['de.pdark.python.pmr.it2:IT2-module1'],
    }
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['--resume-from', 'de.pdark.python.pmr.it2:IT2-module1', 'clean', 'install'],
    ]

def test_build_only(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)
    #widget.show()

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.setStartOption(MavenPreferences.BUILD_ONLY)
        widget.modulesSingleSelection.setCurrentIndex(1)
    
    actual = getStartOptionState(widget)
    assert actual == {
        'startOption': 'BUILD_ONLY',
        'visible': ['singleSelection'],
        'enabled': ['singleSelection'],
        'selected': ['de.pdark.python.pmr.it2:IT2-module1'],
    }
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['--projects', 'de.pdark.python.pmr.it2:IT2-module1', 'clean', 'install'],
    ]

def test_build_up_to(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)
    #widget.show()

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.setStartOption(MavenPreferences.BUILD_UP_TO)
        widget.modulesSingleSelection.setCurrentIndex(1)
    
    actual = getStartOptionState(widget)
    assert actual == {
        'startOption': 'BUILD_UP_TO',
        'visible': ['singleSelection'],
        'enabled': ['singleSelection'],
        'selected': ['de.pdark.python.pmr.it2:IT2-module1'],
    }
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['--also-make', '--projects', 'de.pdark.python.pmr.it2:IT2-module1', 'clean', 'install'],
    ]

def test_switch_from_build_only_to_up_to(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)
    #widget.show()

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int],
        widget.modulesSingleSelection.currentIndexChanged[int]
    ]):
        widget.setStartOption(MavenPreferences.BUILD_ONLY)
        widget.modulesSingleSelection.setCurrentIndex(1)

    with qtbot.waitSignals([
        widget.startOptionWidget.currentIndexChanged[int]
    ]):
        widget.setStartOption(MavenPreferences.BUILD_UP_TO)
    
    actual = getStartOptionState(widget)
    assert actual == {
        'startOption': 'BUILD_UP_TO',
        'visible': ['singleSelection'],
        'enabled': ['singleSelection'],
        'selected': ['de.pdark.python.pmr.it2:IT2-module1'],
    }
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['--also-make', '--projects', 'de.pdark.python.pmr.it2:IT2-module1', 'clean', 'install'],
    ]

def test_extra_options(qtbot):
    widget = createWithMultiModuleProject()
    qtbot.addWidget(widget)

    widget.mavenCmd.setText('--show-version --threads 2.0C')
    
    with qtbot.waitSignal(widget.startMaven) as blocker:
        widget.emitStartMaven()

    assert blocker.args == [
        widget.currentProject,
        widget.projectPreferences.customPatternPreferences,
        ['clean', 'install', '--show-version', '--threads', '2.0C'],
    ]
