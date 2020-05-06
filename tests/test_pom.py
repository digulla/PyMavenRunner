#!python3
# -*- coding: utf-8 -*-

from pmr.maven import *
from pathlib import Path

rootFolder = Path(__file__).parent.parent.resolve()
integrationTestFolder = rootFolder / 'it'
singleProject = integrationTestFolder / 'single-project'
multiModuleProject = integrationTestFolder / 'multi-module-project'

def test_parse_single_pom_dir():
    pom = Pom(singleProject)

def test_parse_single_pom_file():
    pom = Pom(singleProject / 'pom.xml')

def test_artifactId_single():
    pom = Pom(singleProject)
    assert pom.artifactId == 'IT1'

def test_groupId_single():
    pom = Pom(singleProject)
    assert pom.groupId == 'de.pdark.python.pmr'

def test_version_single():
    pom = Pom(singleProject)
    assert pom.version == '1.0'

def test_packaging_single():
    pom = Pom(singleProject)
    assert pom.packaging == 'jar'

def test_single_modules():
    pom = Pom(singleProject)
    assert pom.modules == []

def test_parse_multi_root_pom():
    pom = Pom(multiModuleProject)

def test_artifactId_multi_root():
    pom = Pom(multiModuleProject)
    assert pom.artifactId == 'IT2-parent'

def test_groupId_multi_root():
    pom = Pom(multiModuleProject)
    assert pom.groupId == 'de.pdark.python.pmr.it2'

def test_version_multi_root():
    pom = Pom(multiModuleProject)
    assert pom.version == '1.0'

def test_packaging_multi_root():
    pom = Pom(multiModuleProject)
    assert pom.packaging == 'pom'

def test_multi_root_modules():
    pom = Pom(multiModuleProject)
    assert pom.modules == ['module1', 'module2']

def test_multi_root_childPoms():
    pom = Pom(multiModuleProject)
    assert pom.childPoms == [
        Pom(multiModuleProject / 'module1'),
        Pom(multiModuleProject / 'module2'),
    ]

def test_parse_multi_m1_pom():
    pom = Pom(multiModuleProject / 'module1')

def test_artifactId_multi_m1_pom():
    pom = Pom(multiModuleProject / 'module1')
    assert pom.artifactId == 'IT2-module1'

def test_groupId_multi_m1():
    pom = Pom(multiModuleProject / 'module1')
    assert pom.groupId == 'de.pdark.python.pmr.it2'

def test_version_multi_m1():
    pom = Pom(multiModuleProject / 'module1')
    assert pom.version == '1.0'

def test_packaging_multi_m1():
    pom = Pom(multiModuleProject / 'module1')
    assert pom.packaging == 'jar'

def test_multi_m1_modules():
    pom = Pom(multiModuleProject / 'module1')
    assert pom.modules == []

