#!python3
# -*- coding: utf-8 -*-

from pmr.model import (
    LogLevelStrategy,
    LogLevelStrategyDebugger,
    RegexMatcher,
    StartsWithMatcher,
    SubstringMatcher,
)

def testStartsWithMatcher_matches():
    tool = StartsWithMatcher('a', LogLevelStrategy.WARNING)
    assert tool.matches('a') == LogLevelStrategy.WARNING

def testStartsWithMatcher_debug():
    tool = StartsWithMatcher('a', LogLevelStrategy.WARNING)
    assert tool.debug('a') == (LogLevelStrategy.WARNING, 0, 1)

def testStartsWithMatcher_no_match():
    tool = StartsWithMatcher('a', LogLevelStrategy.WARNING)
    assert tool.matches('b') is None

def testStartsWithMatcher_debug_no_match():
    tool = StartsWithMatcher('a', LogLevelStrategy.WARNING)
    assert tool.debug('b') is None

def testStartsWithMatcher_serialize():
    tool = StartsWithMatcher('a', LogLevelStrategy.WARNING)
    serialized = tool.serialize()
    tool2 = StartsWithMatcher(*serialized)
    assert tool2.matches('a') == LogLevelStrategy.WARNING

def testSubstringMatcher_matches():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    assert tool.matches('a') == LogLevelStrategy.WARNING

def testSubstringMatcher_matches_2():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    assert tool.matches('abc') == LogLevelStrategy.WARNING

def testSubstringMatcher_matches_3():
    tool = SubstringMatcher('b', LogLevelStrategy.WARNING)
    assert tool.matches('abc') == LogLevelStrategy.WARNING

def testSubstringMatcher_matches_4():
    tool = SubstringMatcher('c', LogLevelStrategy.WARNING)
    assert tool.matches('abc') == LogLevelStrategy.WARNING

def testSubstringMatcher_debug():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    assert tool.debug('a') == (LogLevelStrategy.WARNING, 0, 1)

def testSubstringMatcher_debug_1():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    assert tool.debug('abc') == (LogLevelStrategy.WARNING, 0, 1)

def testSubstringMatcher_debug_2():
    tool = SubstringMatcher('b', LogLevelStrategy.WARNING)
    assert tool.debug('abc') == (LogLevelStrategy.WARNING, 1, 2)

def testSubstringMatcher_debug_3():
    tool = SubstringMatcher('c', LogLevelStrategy.WARNING)
    assert tool.debug('abc') == (LogLevelStrategy.WARNING, 2, 3)

def testSubstringMatcher_no_match():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    assert tool.matches('b') is None

def testSubstringMatcher_debug_no_match():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    assert tool.debug('b') is None

def testSubstringMatcher_serialize():
    tool = SubstringMatcher('a', LogLevelStrategy.WARNING)
    serialized = tool.serialize()
    tool2 = SubstringMatcher(*serialized)
    assert tool2.matches('a') == LogLevelStrategy.WARNING

def testRegexMatcher_matches():
    tool = RegexMatcher('a+', LogLevelStrategy.WARNING)
    assert tool.matches('abc') == LogLevelStrategy.WARNING

def testRegexMatcher_matches_1():
    tool = RegexMatcher('a+', LogLevelStrategy.WARNING)
    assert tool.matches('aabc') == LogLevelStrategy.WARNING

def testRegexMatcher_matches_2():
    tool = RegexMatcher('b+', LogLevelStrategy.WARNING)
    assert tool.matches('abc') == LogLevelStrategy.WARNING

def testRegexMatcher_matches():
    tool = RegexMatcher('b+', LogLevelStrategy.WARNING)
    assert tool.debug('abbc') == (LogLevelStrategy.WARNING, 1, 3)

def testRegexMatcher_serialize():
    tool = RegexMatcher('(?i)a+', LogLevelStrategy.WARNING)
    serialized = tool.serialize()
    tool2 = RegexMatcher(*serialized)
    assert tool2.matches('A') == LogLevelStrategy.WARNING

def testDebugger():
    matchers = (
        SubstringMatcher('ErrorTest', LogLevelStrategy.INFO),
        SubstringMatcher(' ERROR ', LogLevelStrategy.ERROR),
        SubstringMatcher(' WARN ', LogLevelStrategy.WARNING),
        SubstringMatcher(' INFO ', LogLevelStrategy.INFO),
        SubstringMatcher(' DEBUG ', LogLevelStrategy.DEBUG),
        RegexMatcher('(?i)error', LogLevelStrategy.ERROR),
    )
    test_input = (
        'timestamp DEBUG PMR message',
        'timestamp DEBUG ErrorTest to test error handling',
        'timestamp INFO PMR running tests',
        'timestamp WARN PMR test warnings',
        'timestamp ERROR PMR test errors',
        '|ERROR the regex should catch this one',
        'something else',
        '',
        'WARN no match at start of line',
    )

    tool = LogLevelStrategyDebugger(
        LogLevelStrategy(matchers)
    )
    actual = list(None if it is None else repr(it) for it in tool.debug(test_input))
    assert actual == [
        "('timestamp DEBUG PMR message', SubstringMatcher(' DEBUG ', 1), result=DEBUG, range=[9:16])",
        "('timestamp DEBUG ErrorTest to test error handling', SubstringMatcher('ErrorTest', 2), result=INFO, range=[16:25])",
        "('timestamp INFO PMR running tests', SubstringMatcher(' INFO ', 2), result=INFO, range=[9:15])",
        "('timestamp WARN PMR test warnings', SubstringMatcher(' WARN ', 3), result=WARNING, range=[9:15])",
        "('timestamp ERROR PMR test errors', SubstringMatcher(' ERROR ', 4), result=ERROR, range=[9:16])",
        "('|ERROR the regex should catch this one', RegexMatcher('(?i)error', 4, 34), result=ERROR, range=[1:6])",
        "('something else', -)",
        "('', -)",
        "('WARN no match at start of line', -)",
    ]
