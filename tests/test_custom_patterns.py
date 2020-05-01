#!python3
# -*- coding: utf-8 -*-

from pmr.model import *
import pytest

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

def test_pickle_base_config():
    tool = CustomPatternPreferences()
    tool.matchers = [BaseMatcherConfig('a', 0)]
    
    with pytest.raises(Exception, match=re.escape(f'Unsupported matcher BaseMatcherConfig(pattern=\'a\', result=0)')):
        tool.pickle()

SAMPLE_CUSTOM_PATTERN_PICKLE = {
    'matchers': [
        ['substring', ' DEBUG ', 1],
        ['regex', '(?i)error', 4]
    ], 
    'test_input': [
        '',
        'timestamp DEBUG PMR message',
    ]
}

def test_unpickle_without_matchers():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    del data['matchers']
    
    with pytest.raises(MissingField, match=re.escape(f'Missing field "matchers": {data!r}')):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def test_unpickle_matchers_is_not_a_list():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    data['matchers'] = 'xxx'
    
    with pytest.raises(Exception, match=re.escape('Expected list for "matchers" but was <class \'str\'>')):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def test_unpickle_wrong_matcher_pickle():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    data['matchers'] = [['xxx']]
    
    with pytest.raises(Exception, match=re.escape("Unsupported matcher ['xxx']")):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def test_unpickle_wrong_matcher_pickle_2():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    data['matchers'] = ['xxx']
    
    with pytest.raises(Exception, match=re.escape("Expected tuple or list but was <class 'str'>: 'xxx'")):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def test_unpickle_without_test_input():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    del data['test_input']
    
    with pytest.raises(MissingField, match=re.escape(f'Missing field "test_input": {data!r}')):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def test_unpickle_test_input_is_not_a_list():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    data['test_input'] = 'xxx'
    
    with pytest.raises(Exception, match=re.escape('Expected list for "test_input" but was <class \'str\'>')):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def test_unpickle_wrong_element_in_test_input():
    data = dict(SAMPLE_CUSTOM_PATTERN_PICKLE)
    data['test_input'] = [1]
    
    with pytest.raises(Exception, match=re.escape('Expected only strings in "test_input" but was <class \'int\'>: 1')):
        tool = CustomPatternPreferences()
        tool.unpickle(data)

def createLogLevelStrategy(prefs = None):
    if prefs is None:
        prefs = createCustomPatternPreferences()
    factory = LogLevelStrategyFactory(prefs)
    return factory.build()

def test_log_level_strategy_debug():
    tool = createLogLevelStrategy()
    result = tool.apply('timestamp DEBUG PMR message')
    assert result == LogLevelStrategy.DEBUG

def test_log_level_strategy_unknown():
    tool = createLogLevelStrategy()
    result = tool.apply('foo')
    assert result == LogLevelStrategy.UNKNOWN

def test_log_level_strategy_unknown_2():
    tool = createLogLevelStrategy()
    result = tool.apply('')
    assert result == LogLevelStrategy.UNKNOWN

def test_clone_substring_matcher_config():
    tool = SubstringMatcherConfig('a', LogLevelStrategy.DEBUG)
    clone = tool.clone()
    assert tool.pattern == clone.pattern and tool.result == clone.result

def test_clone_substring_matcher_config_2():
    tool = SubstringMatcherConfig('foo', LogLevelStrategy.INFO)
    clone = tool.clone()
    assert tool.pattern == clone.pattern and tool.result == clone.result

def test_clone_starts_with_matcher_config():
    tool = StartsWithMatcherConfig('a', LogLevelStrategy.DEBUG)
    clone = tool.clone()
    assert tool.pattern == clone.pattern and tool.result == clone.result

def test_clone_starts_with_matcher_config_2():
    tool = StartsWithMatcherConfig('foo', LogLevelStrategy.INFO)
    clone = tool.clone()
    assert tool.pattern == clone.pattern and tool.result == clone.result

def test_clone_ends_with_matcher_config():
    tool = EndsWithMatcherConfig('a', LogLevelStrategy.DEBUG)
    clone = tool.clone()
    assert tool.pattern == clone.pattern and tool.result == clone.result

def test_ends_with_matcher_config_create_matcher():
    tool = EndsWithMatcherConfig('a', LogLevelStrategy.DEBUG)
    assert isinstance(tool.createMatcher(), BaseMatcher)

def test_ends_with_matcher_matches():
    tool = EndsWithMatcher('z', LogLevelStrategy.DEBUG)
    assert tool.matches('xyz') == LogLevelStrategy.DEBUG

def test_ends_with_matcher_no_match():
    tool = EndsWithMatcher('z', LogLevelStrategy.DEBUG)
    assert tool.matches('abc') is None

def test_pickle_ends_with():
    matcher = EndsWithMatcherConfig('foo', LogLevelStrategy.INFO)
    tool = CustomPatternPreferences()
    tool.matchers = [matcher]
    
    pickled = tool.pickle()
    tool.unpickle(pickled)
    
    assert repr(tool.matchers[0]) == repr(matcher)

def test_base_matcher_config_requires_to_implement_createMatcher():
    tool = BaseMatcherConfig('', 0)
    
    with pytest.raises(Exception, match=re.escape('Please implement')):
        tool.createMatcher()

def test_base_matcher_config_requires_to_implement_clone():
    tool = BaseMatcherConfig('', 0)
    
    with pytest.raises(Exception, match=re.escape('Please implement')):
        tool.clone()
