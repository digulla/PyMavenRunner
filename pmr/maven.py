#!python3
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET

class Pom:
    NAMESPACE = '{http://maven.apache.org/POM/4.0.0}'
    def __init__(self, path):
        path = path.resolve()
        if path.is_dir():
            path = path / 'pom.xml'
        if not (path.is_file() and path.name == 'pom.xml'):
            raise FileNotFoundError(f'Expected path to pom.xml: {path}')

        self.path = path

        self.parse()

    def parse(self):
        tree = ET.parse(self.path)
        root = tree.getroot()

        expected = f'{self.NAMESPACE}project'
        if root.tag != expected:
            raise Exception(f"{self.path}: Expected {expected!r} but was {root.tag!r}")

        self.tree = tree
        self.root = root

    def parentElem(self):
        name = f'{self.NAMESPACE}parent'
        return self.root.find(name)

    def artifactIdElem(self):
        name = f'{self.NAMESPACE}artifactId'
        return self.root.find(name)

    @property
    def artifactId(self):
        name = f'{self.NAMESPACE}artifactId'
        elem = self.artifactIdElem()
        return self.parentElem().find(name).text if elem is None else elem.text

    def groupIdElem(self):
        name = f'{self.NAMESPACE}groupId'
        return self.root.find(name)

    @property
    def groupId(self):
        name = f'{self.NAMESPACE}groupId'
        elem = self.groupIdElem()
        return self.parentElem().find(name).text if elem is None else elem.text

    def versionElem(self):
        name = f'{self.NAMESPACE}version'
        return self.root.find(name)

    @property
    def version(self):
        name = f'{self.NAMESPACE}version'
        elem = self.versionElem()
        return self.parentElem().find(name).text if elem is None else elem.text

    @property
    def coordinate(self):
        return f'{self.groupId}:{self.artifactId}:{self.version}'

    def packagingElem(self):
        name = f'{self.NAMESPACE}packaging'
        return self.root.find(name)

    @property
    def packaging(self):
        elem = self.packagingElem()
        return 'jar' if elem is None else elem.text

    def modulesElem(self):
        name = f'{self.NAMESPACE}modules'
        return self.root.find(name)

    @property
    def modules(self):
        elem = self.modulesElem()
        if elem is None:
            return []

        return list(
            it.text
            for it in elem.findall(f'{self.NAMESPACE}module')
        )

    def childPom(self, moduleName):
        return Pom(self.path.parent / moduleName)

    @property
    def childPoms(self):
        return list(
            self.childPom(name)
            for name in self.modules
        )

    def __eq__(self, other):
        return self.path.samefile(other.path)

    def __repr__(self):
        return f'Pom({self.path})'
