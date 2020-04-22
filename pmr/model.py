#!python3
# -*- coding: utf-8 -*-

import re

class Project:
    def __init__(self, path):
        self.path = path
        self.name = path.name

class BaseMatcher:
    def __init__(self, pattern, result):
        self.pattern = pattern
        self.result = result

    def serialize(self):
        return (self.pattern, self.result)

    def __repr__(self):
        info = self.serialize()
        return f'{self.__class__.__name__}{info!r}'

class RegexMatcher(BaseMatcher):
    def __init__(self, pattern, result, flags=0):
        if isinstance(pattern, str):
            pattern = re.compile(pattern, flags)
        super().__init__(pattern, result)

    def matches(self, line):
        return None if self.pattern.search(line) is None else self.result

    def debug(self, line):
        matcher = self.pattern.search(line)
        if matcher is None:
            return None

        return (self.result, matcher.start(), matcher.end())

    def serialize(self):
        return (self.pattern.pattern, self.result, self.pattern.flags)

class SubstringMatcher(BaseMatcher):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def matches(self, line):
        return self.result if self.pattern in line else None

    def debug(self, line):
        pos = line.find(self.pattern)
        if pos == -1:
            return None

        return (self.result, pos, pos + len(self.pattern))

class StartsWithMatcher(BaseMatcher):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def matches(self, line):
        return self.result if line.startswith(self.pattern) else None

    def debug(self, line):
        if line.startswith(self.pattern):
            return (self.result, 0, len(self.pattern))

        return None

class LogLevelStrategy:
    UNKNOWN = None
    TRACE, DEBUG, INFO, WARNING, ERROR = range(5)

    def __init__(self, matchers):
        self.matchers = matchers

    def apply(self, line):
        return next(r for r in (m.matches(line) for m in self.matchers) if r is not None)

    def debug(self, line):
        for m in self.matchers:
            r = m.debug(line)
            if r is not None:
                return (line, m, r)

        return (line, None)

class LogLevelStrategyDebugger:
    def __init__(self, strategy):
        self.strategy = strategy

    def debug(self, test_inputs):
        return (
            self.strategy.debug(line)
            for line in test_inputs
        )
