#!python3
# -*- coding: utf-8 -*-

import urllib.request
import re
from pathlib import Path
import hashlib
import tarfile
import subprocess
import os
import shutil
from pmr.version import Version

rootFolder = Path(__file__).parent.parent.resolve()
tmpFolder = rootFolder / 'tmp'

def download(url, target):
    if target.exists():
        print(f'Using cached file {target}')
        return
    
    print(f'Downloading {url} as {target}')
    size = 0
    print(f'Downloaded {size} bytes', end='\r', flush=True)
    with open(target, mode='wb') as targetFH:
        with urllib.request.urlopen(url) as fh:
            while True:
                content = fh.read(1024)
                n = len(content)
                if n == 0:
                    break
                targetFH.write(content)
                
                size += n
                print(f'Downloaded {size} bytes', end='\r', flush=True)
    
    print('')

def getMavenMirrorURL():
    cache = tmpFolder / 'maven-download.html'

    if cache.exists():
        print('Getting download mirror from cached file')
        with open(cache, mode='r', encoding='utf-8') as fh:
            content = fh.read()
    else:
        print('Getting download mirror from maven.apache.org')
        with urllib.request.urlopen('http://maven.apache.org/download.cgi') as fh:
            content = fh.read().decode('utf-8')
        with open(cache, mode='w', encoding='utf-8') as fh:
            fh.write(content)
    
    pattern = re.compile(r'<a href=["\'"](http[^"\'"]+)["\'"]')
    for match in pattern.finditer(content):
        url = match.group(1)
        if url.endswith('.tar.gz'):
            return url

    raise Exception('No download URL found')

def calculateCheckum(path):
    m = hashlib.sha512()
    
    with open(path, mode='rb') as fh:
        while True:
            content = fh.read(102400)
            if len(content) == 0:
                break
            m.update(content)

    return m.hexdigest()

def downloadMaven(version):
    url = getMavenMirrorURL()
    checksumUrl = f'https://archive.apache.org/dist/maven/maven-3/{version}/binaries/apache-maven-{version}-bin.tar.gz.sha512'
    
    tarArchive = tmpFolder / f'apache-maven-{version}-bin.tar'
    download(url, tarArchive)
    remoteChecksumPath = tmpFolder / f'apache-maven-{version}-bin.tar.sha512'
    download(checksumUrl, remoteChecksumPath)
    
    localChecksum = calculateCheckum(tarArchive)
    
    with open(remoteChecksumPath, mode='r', encoding='ascii') as fh:
        remoteCheckum = fh.read()

    if localChecksum != remoteCheckum:
        raise Exception(f'Checksum mismatch for {tarArchive}:\nExpected: {remoteCheckum}\nActual..: {localChecksum}')
    
    print('Checksum OK')
    
    return tarArchive

def unpackTar(tarArchive, targetFolder):
    targetFolder = targetFolder.resolve()
    tool = tarfile.open(tarArchive)
    for member in tool:
        #print(member.type, member.name)
        segments = member.name.split('/')
        targetPath = targetFolder.joinpath(*segments).resolve()
        if not targetFolder in targetPath.parents:
            raise Exception(f'Security alert: Member {member.name} of tar archive {tarArchive} has a path outside of {targetFolder}')
        
        if member.isdir():
            targetPath.mkdir(mode=member.mode, parents=True, exist_ok=True)
        elif member.isfile():
            print(f'Unpacking {member.size:15,d} {member.mode:#6o} {member.name}')
            tool.extract(member, targetFolder)
        else:
            raise Exception(f'Unsupported member {tarinfo.name} in tar archive {tarArchive}')

def checkJavaVersion(minimumVersion):
    command = 'java'
    if 'JAVA_HOME' in os.environ:
        path = Path(os.environ['JAVA_HOME']) / 'bin' / 'java'

    args = [command, '-version']
    print('Running', args)
    result = subprocess.run(args,
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        check=True,
        universal_newlines=True)
    #print(repr(result.stdout))
    
    firstLine = result.stdout.split('\n')[0]
    pattern = re.compile(r'"([^"]+)"')
    match = pattern.search(firstLine)
    if match is None:
        raise Exception(f"Unable to find version in {firstLine!r}")
    version = match.group(1)
    
    parts = version.split('.')
    if parts[2].startswith('0_'):
        parts[2] = parts[2][2:]
    
    parts = [int(x) for x in parts]
    version = Version(parts)
    
    if version < minimumVersion:
        raise Exception(f'Found Java version {version} but this project needs at least {minimumVersion}')
    
    print(f'OK Found Java version {version}')

def checkMaven(folder):
    result = subprocess.run(
        [mavenCommand, '-version'],
        stderr=subprocess.STDOUT,
        stdout=subprocess.PIPE,
        check=True,
        universal_newlines=True
    )
    print('OK Can start local Maven')

class ExpectedOutputGenerator:
    def __init__(self, mavenCommand, itFolder, logFolder, tmpFolder):
        self.mavenCommand, self.itFolder, self.logFolder, self.tmpFolder = mavenCommand, itFolder, logFolder, tmpFolder
    
    def run(self, testCase, mavenOptions, name=None, deleteMavenRepo=True):
        if name is None:
            name = 'mvn-' + '-'.join(mavenOptions)
            
            if not deleteMavenRepo:
                name += '-existing-repo'
        
        mavenRepo = self.tmpFolder / name / 'm2repo'
        if deleteMavenRepo and mavenRepo.exists():
            shutil.rmtree(mavenRepo)
        mavenRepo.mkdir(parents=True, exist_ok=False)
        
        args = [
            self.mavenCommand,
            '-B',
            f'-Dmaven.repo.local={mavenRepo}',
        ]
        args.extend(mavenOptions)

        print(f'Preparing output for {testCase} {name}')
        folder = self.logFolder / testCase
        folder.mkdir(parents=True, exist_ok=True)
        with open(folder / f'{name}.log', mode='w', newline=None, encoding='utf-8') as fh:
            subprocess.run(
                args,
                stderr=subprocess.STDOUT,
                stdout=fh,
                check=True,
                universal_newlines=True,
                cwd=self.itFolder / testCase
            )

if __name__ == '__main__':
    tmpFolder.mkdir(parents=True, exist_ok=True)
    
    mavenVersion = '3.6.3'
    mavenTarArchive = downloadMaven(mavenVersion)
    mavenFolder = tmpFolder / f'apache-maven-{mavenVersion}'
    if not mavenFolder.exists():
        unpackTar(mavenTarArchive, tmpFolder)

    minimumVersion = Version([1,7])
    checkJavaVersion(minimumVersion)
    
    mavenCommand = mavenFolder / 'bin' / 'mvn'
    checkMaven(mavenCommand)
    
    itFolder = rootFolder / 'it'
    logFolder = rootFolder / 'tests' / 'expected_output'
    gen = ExpectedOutputGenerator(mavenCommand, itFolder, logFolder, tmpFolder / 'expected_output')
    
    gen.run('single-project', ['clean'])
    gen.run('single-project', ['clean'], deleteMavenRepo=False)
    gen.run('single-project', ['clean', 'install'])
    gen.run('single-project', ['clean', 'install'], deleteMavenRepo=False)
