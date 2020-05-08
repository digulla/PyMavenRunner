#!python3
# -*- coding: utf-8 -*-

from pmr.version import Version

def test_same():
    v1 = Version(1)
    v2 = Version(1)
    assert v1 == v2

def test_same2():
    v1 = Version(1,1)
    v2 = Version(1,1)
    assert v1 == v2

def test_before():
    v1 = Version(1)
    v2 = Version(2)
    assert v1 < v2

def test_before2():
    v1 = Version(1,0)
    v2 = Version(2,0)
    assert v1 < v2

def test_before3():
    v1 = Version(1,9)
    v2 = Version(2,0)
    assert v1 < v2

def test_different_length():
    v1 = Version(1)
    v2 = Version(2,0)
    assert v1 < v2

def test_different_length2():
    v1 = Version(1,0)
    v2 = Version(2)
    assert v1 < v2

def test_after():
    v1 = Version(2)
    v2 = Version(1)
    assert v1 > v2

def test_after2():
    v1 = Version(2,0)
    v2 = Version(1,9)
    assert v1 > v2

def test_same_version():
    import pmr
    v = Version(*pmr.VERSION_INFO)
    assert repr(v) == pmr.VERSION
