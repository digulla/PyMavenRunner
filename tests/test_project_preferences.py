#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
from pathlib import Path

rootFolder = Path(__file__).parent.parent.resolve()
tempFolder = rootFolder / 'tmp'
projectsFolder = tempFolder / 'test_project_preferences'

def test_load_missing_preferences(request):
	projectFolder = projectsFolder / request.node.name
	projectFolder.mkdir(parents=True, exist_ok=True)
	project = Project(projectFolder)

	prefs = ProjectPreferences(project)
	prefs.load()

def test_skip_saving_empty_preferences(request):
	projectFolder = projectsFolder / request.node.name
	projectFolder.mkdir(parents=True, exist_ok=True)
	project = Project(projectFolder)

	prefs = ProjectPreferences(project)
	prefs.save()

	path = prefs.getPath()
	assert not path.exists()

def test_save_test_input(request):
	projectFolder = projectsFolder / request.node.name
	projectFolder.mkdir(parents=True, exist_ok=True)
	project = Project(projectFolder)

	prefs = ProjectPreferences(project)
	prefs.customPatternPreferences.test_input.append('foo')

	prefs.save()

	path = prefs.getPath()
	assert path.exists()

def test_delete_obsolete_preferences(request):
	projectFolder = projectsFolder / request.node.name
	projectFolder.mkdir(parents=True, exist_ok=True)
	project = Project(projectFolder)

	prefs = ProjectPreferences(project)
	path = prefs.getPath()
	with open(path, mode='w', encoding='utf-8') as fh:
		fh.write('{}')

	assert path.exists()
	prefs.save()
	assert not path.exists()

def test_load_custom_pattern_multi_module_project():
	projectFolder = rootFolder / 'it' / 'multi-module-project'
	project = Project(projectFolder)

	prefs = ProjectPreferences(project)
	prefs.load()

	assert len(prefs.customPatternPreferences.matchers) > 0
	assert len(prefs.customPatternPreferences.test_input) > 0
