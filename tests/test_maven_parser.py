#!python3
# -*- coding: utf-8 -*-

from pmr.ui import MavenRunner, Project

from pathlib import Path

rootFolder = Path(__file__).parent.parent.resolve()
expectedOutputFolder = rootFolder / 'tests' / 'expected_output'

class MockProcessOutput:
    def __init__(self, mockProcess, stdout):
        self.mockProcess = mockProcess
        
        self.lines = stdout.split('\n')
    
    def readline(self):
        if len(self.lines) == 0:
            self.mockProcess.eof()
            return ''
        
        return self.lines.pop(0) + '\n'

class MockProcess:
    def __init__(self, args, stdout, returncode=0):
        self.args, self._stdout, self._returncode = args, stdout, returncode
        
        self.rc = None
        self.stdout = MockProcessOutput(self, self._stdout)

    def eof(self):
        self.rc = self._returncode

    def poll(self):
        return self.rc        

class MockMavenRunner(MavenRunner):
    def __init__(self, project, cmdLine, mockProcess):
        super().__init__(project, cmdLine)
        
        self.mockProcess = mockProcess
    
    def createMavenProcess(self):
        return self.mockProcess

def readCannedMavenOutput(testCase, fileName):
    path = expectedOutputFolder / testCase / fileName
    if not path.exists():
        raise Exception(f'Missing {path}')
    
    with open(path, mode='r', encoding='utf-8') as fh:
        return fh.read()

class QtSignalCollector:
    def __init__(self):
        self.log = []
    
    def install(self, runner):
        for name in dir(runner):
            value = getattr(runner, name)
            
            #print(name, type(name), value)
            if (self.isPyQtSignal(value)):
                print(f'Installing handler for {value}')
                handler = lambda *args, name=name: self.signalHandler(name, args)
                value.connect(handler)

    def isPyQtSignal(self, obj):
        return str(obj).startswith('<bound PYQT_SIGNAL ') and hasattr(obj, 'connect')

    def signalHandler(self, name, args):
        #print(f'Received {name} {args}')
        entry = [name]
        entry.extend(args)
        self.log.append(entry)
    
    def __repr__(self):
        return '\n'.join(repr(x) for x in self.log)

class DumpMavenRunnerLog:
    def __init__(self, log):
        self.log = log
    
    def dump(self):
        result = []
        for it in self.log:
            methodName = f'dump_' + it[0]
            
            m = getattr(self, methodName)
            result.append(m(*it[1:]))
        
        return '\n'.join(result)
    
    def dump_mavenStarted(self, project, args):
        return f'#MAVEN_START {project.name} {args}'
    
    def dump_reactorBuildOrder(self, module, packaging):
        return f'#BUILD_ORDER [{module}] {packaging}'
    
    def dump_progress(self, current, max):
        return f'#PROGRESS {current}/{max}'
        
    def dump_output(self, line):
        return line
    
    def dump_mavenModule(self, name):
        return f'#MAVEN_MODULE [{name}]'
    
    def dump_mavenPlugin(self, text):
        return f'#MAVEN_PLUGIN [{text}]'
    
    def dump_mavenFinished(self, rc):
        return f'#MAVEN_RC {rc}'
    
    def dump_warning(self, message):
        return f'#WARNING {message}'
    
    def dump_error(self, message):
        return f'#ERROR {message}'
    
    def dump_testsStarted(self):
        return f'#START_OF_TESTS'
    
    def dump_startedTest(self, name):
        return f'#TEST [{name}]'
    
    def dump_testOutput(self, line):
        return f'#TOUT {line}'
    
    def dump_finishedTest(self, name, *stats):
        return f'#TEST_RESULT [{name}] {stats}'
        
    def dump_testsFinished(self, *stats):
        return f'#END_OF_TESTS {stats}'
    
    def dump_resumeDetected(self, resumeOption):
        return f'#RESUME {resumeOption!r}'
        
    def dump_reactorSummary(self, module, status, duration):
        return f'#REACTOR_SUMMARY [{module}] {status} {duration}'

def assertSignalLog(testName, log):
    assert len(log) > 0

    expectedPath = expectedOutputFolder / 'test_maven_parser' / f'{testName}.txt'
    if expectedPath.exists():
        with open(expectedPath, encoding='utf-8') as fh:
            expected = fh.read()
    else:
        expected = None

    tool = DumpMavenRunnerLog(log)
    actual = tool.dump()
    
    actualFolder = rootFolder / 'tmp' / 'signal-logs' / 'test_maven_parser'
    actualFolder.mkdir(parents=True, exist_ok=True)
    with open(actualFolder / f'{testName}.txt', mode='w', encoding='utf-8') as fh:
        fh.write(actual)
    
    if expected is None:
        expectedPath.parent.mkdir(parents=True, exist_ok=True)

        with open(expectedPath, mode='w', encoding='utf-8') as fh:
            fh.write(actual)

        expected = '-- File was created!'

    assert actual == expected
    
def run_process(qtbot, project, args, stdout):
    process = MockProcess(args, stdout)
    
    runner = MockMavenRunner(project, process.args, process)
    
    collector = QtSignalCollector()
    collector.install(runner)
    
    runner.start()
    
    if hasattr(runner, 'processor'):
        with qtbot.waitSignal(runner.mavenFinished):
            assert runner.processor.wait(10 * 1000)
    else:
        raise Exception(f'Something is wrong:\n{collector}')
    
    return collector.log

singleProject = Project(rootFolder / 'it' / 'single-project')

def test_single_project_clean(qtbot, request):
    stdout = readCannedMavenOutput('single-project', 'mvn-clean.log')
    
    log = run_process(qtbot, singleProject, ['clean'], stdout)
    assertSignalLog(request.node.name, log)

def test_single_project_clean_existing_repo(qtbot, request):
    stdout = readCannedMavenOutput('single-project', 'mvn-clean-existing-repo.log')
    
    log = run_process(qtbot, singleProject, ['clean'], stdout)
    assertSignalLog(request.node.name, log)

def test_single_project_clean_install(qtbot, request):
    stdout = readCannedMavenOutput('single-project', 'mvn-clean-install.log')
    
    log = run_process(qtbot, singleProject, ['clean', 'install'], stdout)
    assertSignalLog(request.node.name, log)

def test_single_project_clean_install_existing_repo(qtbot, request):
    stdout = readCannedMavenOutput('single-project', 'mvn-clean-install-existing-repo.log')
    
    log = run_process(qtbot, singleProject, ['clean', 'install'], stdout)
    assertSignalLog(request.node.name, log)

def test_single_project_typo(qtbot, request):
    stdout = readCannedMavenOutput('single-project', 'mvn-clen.log')
    
    log = run_process(qtbot, singleProject, ['clen'], stdout)
    assertSignalLog(request.node.name, log)

def test_multi_module_project(qtbot, request):
    stdout = readCannedMavenOutput('multi-module-project', 'mvn-clean-install-existing-repo.log')
    
    log = run_process(qtbot, singleProject, ['clen'], stdout)
    assertSignalLog(request.node.name, log)
