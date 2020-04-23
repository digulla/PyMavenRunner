#!python3
# -*- coding: utf-8 -*-

import re
import json

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

class LogLevelDebugResult:
    def __init__(self, line, matcher=None, result=None, start=None, end=None):
        self.line, self.matcher, self.result, self.start, self.end = line, matcher, result, start, end

        self.level = LogLevelStrategy.LEVEL_NAMES[self.result]

    def __repr__(self):
        if self.matcher is None:
            return f'({self.line!r}, -)'

        return f'({self.line!r}, {self.matcher}, result={self.level}, range=[{self.start}:{self.end}])'

class LogLevelStrategy:
    UNKNOWN = None
    TRACE, DEBUG, INFO, WARNING, ERROR = range(5)
    LEVELS = [TRACE, DEBUG, INFO, WARNING, ERROR]
    LEVEL_NAMES = {
        UNKNOWN: 'UNKNOWN',
        TRACE: 'TRACE',
        DEBUG: 'DEBUG',
        INFO: 'INFO',
        WARNING: 'WARNING',
        ERROR: 'ERROR',
    }

    def __init__(self, matchers):
        self.matchers = matchers

    def apply(self, line):
        return next(r for r in (m.matches(line) for m in self.matchers) if r is not None)

    def debug(self, line):
        for m in self.matchers:
            r = m.debug(line)
            if r is not None:
                return LogLevelDebugResult(line, m, r[0], r[1], r[2])

        return LogLevelDebugResult(line)

class LogLevelStrategyDebugger:
    def __init__(self, strategy):
        self.strategy = strategy

    def debug(self, test_inputs):
        return (
            self.strategy.debug(line)
            for line in test_inputs
        )

class BaseMatcherConfig:
    def __init__(self, pattern, result):
        self.pattern, self.result = pattern, result

    def createMatcher(self):
        raise Exception('Please implement')

class SubstringMatcherConfig(BaseMatcherConfig):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def createMatcher(self):
        return SubstringMatcher(self.pattern, self.result)

    def clone(self):
        return SubstringMatcherConfig(self.pattern, self.result)

class RegexMatcherConfig(BaseMatcherConfig):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def createMatcher(self):
        return RegexMatcher(self.pattern, self.result)

    def clone(self):
        return RegexMatcherConfig(self.pattern, self.result)

class CustomPatternPreferences:
    def __init__(self):
        self.matchers = []
        self.test_input = []

    def unpickle(self, data):
        try:
            matchers = data['matchers']
        except KeyError as ex:
            raise Exception(f'Missing field "matchers": {data!r}') from ex
        if not isinstance(matchers, list):
            raise Exception(f'Expected list for "matchers": {data!r}')
        
        unpickledMatchers = list(
            self.unpickleMatcher(it)
            for it in matchers
        )

        try:
            test_input = data['test_input']
        except KeyError as ex:
            raise Exception(f'Missing field "test_input": {data!r}') from ex
        if not isinstance(test_input, list):
            raise Exception(f'Expected list for "test_input": {data!r}')
        for it in test_input:
            if not isinstance(it, str):
                raise Exception(f'Expected only strings in "test_input": {it!r}')

        self.matchers = unpickledMatchers
        self.test_input = test_input

    def pickle(self):
        if len(self.matchers) == 0 and len(self.test_input) == 0:
            return None

        pickled_matchers = list(
            self.pickleMatcher(it)
            for it in self.matchers
        )

        return {
            'matchers': pickled_matchers,
            'test_input': self.test_input
        }

    def pickleMatcher(self, matcher):
        if isinstance(matcher, SubstringMatcherConfig):
            return ['substring', matcher.pattern, matcher.result]
        elif isinstance(matcher, RegexMatcherConfig):
            return ['regex', matcher.pattern, matcher.result]
        else:
            raise Exception(f'Unsupported matcher {matcher!r}')

    def unpickleMatcher(self, data):
        if data[0] == 'substring':
            return SubstringMatcherConfig(*data[1:])
        elif data[0] == 'regex':
            return RegexMatcherConfig(*data[1:])
        else:
            raise Exception(f'Unsupported matcher {data!r}')

class ProjectPreferences:
    def __init__(self, project):
        self.project = project

        self.reset()

    def reset(self):
        self.customPatternPreferences = CustomPatternPreferences()

    def load(self):
        self.reset()

        path = self.getPath()
        if path.exists():
            print(f'Loading preferences from {path}')
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)

            self.unpickle(data)

    def unpickle(self, data):
        value = data.get('customPatternPreferences')
        if value is not None:
            self.customPatternPreferences.unpickle(value)

    def pickle(self):
        data = {}

        value = self.customPatternPreferences.pickle()
        if value is not None:
            data['customPatternPreferences'] = value 

        return data

    def getPath(self):
        return self.project.path / 'PyMavenRunner.conf'

    def save(self):
        data = self.pickle()

        path = self.getPath()
        if len(data) == 0:
            if path.exists():
                print(f'Deleting obsolete preferences {path}')
                path.unlink()
            else:
                print(f'Skipping saving empty preferences')
            return

        print(f'Saving preferences to {path}')
        with open(path, mode='w', encoding='utf-8') as fh:
            json.dump(data, fh, indent=4, sort_keys=True)
