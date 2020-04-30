#!python3
# -*- coding: utf-8 -*-

from pmr.logging import *
from pathlib import Path
import shutil

rootFolder = Path(__file__).parent.parent.resolve()

def test_DummyLogger():
    log = DummyLogger()
    log.log('message')
    log.close()

def test_MockLogger():
    log = MockLogger('ignored')
    log.log('message')
    log.close()
    
    assert log.events == [('message',)]

def test_FileLogger(request):
    path = Path(rootFolder / 'tmp' / 'test_logging' / request.node.name / 'foo.log')
    if path.parent.exists():
        shutil.rmtree(path.parent)
    
    assert not path.exists()
        
    log = FileLogger(path)
    assert path.exists()

    log.log('DEBUG', 'test')
    log.log('INFO', 'test')
    log.log('ERROR', 'test')
    log.close()
    
    with open(path, encoding='utf-8') as fh:
        actual = fh.read()
    
    assert actual == '''\
DEBUG test
INFO test
ERROR test
'''