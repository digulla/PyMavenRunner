#!python3
# -*- coding: utf-8 -*-

from pmr.model import *

def test_no_pickle_defaults():
    prefs = MavenPreferences()
    assert prefs.pickle() == None

def test_unpickle_empty_dict():
    prefs = MavenPreferences()
    prefs.unpickle({})
    assert prefs.pickle() == None

def test_pickle():
    prefs = MavenPreferences()
    prefs.goals = 'xxx'
    prefs.startOption = MavenPreferences.BUILD_ONLY
    prefs.moduleList = ['a', 'b']
    assert prefs.pickle() == {
        'goals': 'xxx',
        'startOption': 'BUILD_ONLY',
        'moduleList': ['a', 'b'], 
    }

def test_unpickle():
    data = {
        'goals': 'xxx',
        'startOption': 'BUILD_ONLY',
        'moduleList': ['a', 'b'], 
    }

    prefs = MavenPreferences()
    prefs.unpickle(data)
    assert prefs.pickle() == data
