#!python3
# -*- coding: utf-8 -*-

from pmr.model import *

def createCustomPatternPreferences():
	result = CustomPatternPreferences()
	result.matchers = [
        SubstringMatcherConfig(' DEBUG ', LogLevelStrategy.DEBUG),
        RegexMatcherConfig('(?i)error', LogLevelStrategy.ERROR),		
	]
	result.test_input = [
		'',
		'timestamp DEBUG PMR message',
	]
	return result

def test_save_custom_pattern_prefs():
	tool = createCustomPatternPreferences()

	actual = tool.pickle()
	assert actual == {
		'matchers': [
			['substring', ' DEBUG ', 1],
			['regex', '(?i)error', 4]
		], 
		'test_input': [
			'',
			'timestamp DEBUG PMR message',
		]
	}

def test_load_custom_pattern_prefs():
	tool = createCustomPatternPreferences()

	actual = tool.pickle()

	tool2 = CustomPatternPreferences()
	tool2.unpickle(actual)

	actual2 = tool2.pickle()
	assert actual2 == actual
