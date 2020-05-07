#!python3
# -*- coding: utf-8 -*-

import re
import json
from pmr.maven import Pom

class Project:
    def __init__(self, path):
        self.path = path
        self.name = path.name
        self._rootPom = None

    @property
    def rootPom(self):
        if self._rootPom is None:
            self._rootPom = Pom(self.path)

        return self._rootPom

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

class EndsWithMatcher(BaseMatcher):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def matches(self, line):
        return self.result if line.endswith(self.pattern) else None

    def debug(self, line):
        if line.endswith(self.pattern):
            n = len(line)
            return (self.result, n - len(self.pattern), n)

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
        self.matchers = list(matchers)

    def apply(self, line):
        try:
            return next(
                r
                for r in (
                    m.matches(line)
                    for m in self.matchers
                )
                if r is not None
            )
        except StopIteration:
            return self.UNKNOWN

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

    def clone(self):
        raise Exception('Please implement')

    def __repr__(self):
        typeInfo = type(self).__name__
        return f'{typeInfo}(pattern={self.pattern!r}, result={self.result})'

class SubstringMatcherConfig(BaseMatcherConfig):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def createMatcher(self):
        return SubstringMatcher(self.pattern, self.result)

    def clone(self):
        return SubstringMatcherConfig(self.pattern, self.result)

class StartsWithMatcherConfig(BaseMatcherConfig):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def createMatcher(self):
        return StartsWithMatcher(self.pattern, self.result)

    def clone(self):
        return StartsWithMatcherConfig(self.pattern, self.result)

class EndsWithMatcherConfig(BaseMatcherConfig):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def createMatcher(self):
        return EndsWithMatcher(self.pattern, self.result)

    def clone(self):
        return EndsWithMatcherConfig(self.pattern, self.result)

class RegexMatcherConfig(BaseMatcherConfig):
    def __init__(self, pattern, result):
        super().__init__(pattern, result)

    def createMatcher(self):
        return RegexMatcher(self.pattern, self.result)

    def clone(self):
        return RegexMatcherConfig(self.pattern, self.result)

class LogLevelStrategyFactory:
    def __init__(self, customPatternPreferences):
        self.customPatternPreferences = customPatternPreferences

    def build(self):
        matchers = list(
            it.createMatcher()
            for it in self.customPatternPreferences.matchers
        )

        return LogLevelStrategy(matchers)

class CustomPatternMavenJavaProjectDefaults:
    def __init__(self):
        self.matchers = [
            StartsWithMatcherConfig('\tat ', LogLevelStrategy.ERROR),
            SubstringMatcherConfig(' ERROR ', LogLevelStrategy.ERROR),
            RegexMatcherConfig('\bWARN(\b|NING)', LogLevelStrategy.WARNING),
            SubstringMatcherConfig(' INFO ', LogLevelStrategy.INFO),
            SubstringMatcherConfig(' DEBUG ', LogLevelStrategy.DEBUG),
            RegexMatcherConfig('(?i)error', LogLevelStrategy.ERROR),
        ]
        self.test_input = [
            'timestamp DEBUG PMR message',
            'timestamp INFO PMR running tests',
            'timestamp WARN PMR test warnings',
            'timestamp ERROR PMR test errors',
            '|ERROR the regex should catch this one',
            'something else',
            '',
            'WARN No match at start of line',
            'timestamp ERROR PMR test exception',
            'java.lang.IllegalArgumentException: Catch me if you can',
            '    at de.pdark.python.pmr.it2.module1.Foo2.logException(Foo2.java:16)',
        ]

class CustomPatternEmptyDefaults:
    def __init__(self):
        self.matchers = []
        self.test_input = []

class Defaults:
    def __init__(self, customPatternDefaults=None):
        self.customPatternDefaults = CustomPatternMavenJavaProjectDefaults() if customPatternDefaults is None else customPatternDefaults

class MissingField(Exception):
    def __init__(self, data, field):
        super().__init__((f'Missing field "{field}": {data!r}'))

class CustomPatternPreferences:
    def __init__(self, defaults=None):
        if defaults is None:
            defaults = Defaults().customPatternDefaults

        self.matchers = list(defaults.matchers)
        self.test_input = list(defaults.test_input)

    def unpickle(self, data):
        try:
            matchers = data['matchers']
        except KeyError:
            raise MissingField(data, 'matchers')
        if not isinstance(matchers, list):
            msg = type(matchers)
            raise Exception(f'Expected list for "matchers" but was {msg}')
        
        unpickledMatchers = list(
            self.unpickleMatcher(it)
            for it in matchers
        )

        try:
            test_input = data['test_input']
        except KeyError:
            raise MissingField(data, 'test_input')
        if not isinstance(test_input, list):
            msg = type(test_input)
            raise Exception(f'Expected list for "test_input" but was {msg}')
        for it in test_input:
            if not isinstance(it, str):
                msg = type(it)
                raise Exception(f'Expected only strings in "test_input" but was {msg}: {it!r}')

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
        elif isinstance(matcher, StartsWithMatcherConfig):
            return ['startswith', matcher.pattern, matcher.result]
        elif isinstance(matcher, EndsWithMatcherConfig):
            return ['endswith', matcher.pattern, matcher.result]
        elif isinstance(matcher, RegexMatcherConfig):
            return ['regex', matcher.pattern, matcher.result]
        else:
            raise Exception(f'Unsupported matcher {matcher!r}')

    def unpickleMatcher(self, data):
        if not isinstance(data, (tuple, list)):
            msg = type(data)
            raise Exception(f'Expected tuple or list but was {msg}: {data!r}')
        
        if data[0] == 'substring':
            return SubstringMatcherConfig(*data[1:])
        elif data[0] == 'startswith':
            return StartsWithMatcherConfig(*data[1:])
        elif data[0] == 'endswith':
            return EndsWithMatcherConfig(*data[1:])
        elif data[0] == 'regex':
            return RegexMatcherConfig(*data[1:])
        else:
            raise Exception(f'Unsupported matcher {data!r}')

class MavenPreferences:
    START_ALL, START_FIRST_CHANGE, START_WITH, BUILD_ONLY, BUILD_UP_TO, BUILD_SELECTED, START_OPTION_COUNT = range(7)
    START_OPTION_NAMES = {
        START_ALL: 'START_ALL',
        START_FIRST_CHANGE: 'START_FIRST_CHANGE',
        START_WITH: 'START_WITH',
        BUILD_ONLY: 'BUILD_ONLY',
        BUILD_UP_TO: 'BUILD_UP_TO',
        BUILD_SELECTED: 'BUILD_SELECTED',
    }

    DEFAULT_GOALS = 'clean install'
    DEFAULT_START_OPTION = START_ALL

    def __init__(self):
        self.goals = self.DEFAULT_GOALS
        self.startOption = self.DEFAULT_START_OPTION
        self.moduleList = []

    def pickle(self):
        result = {}
        if self.goals != self.DEFAULT_GOALS:
            result['goals'] = self.goals

        if self.startOption != self.DEFAULT_START_OPTION:
            result['startOption'] = self.START_OPTION_NAMES[self.startOption]

        if len(self.moduleList) > 0:
            result['moduleList'] = self.moduleList

        return None if len(result) == 0 else result

    def unpickle(self, data):
        self.goals = data.get('goals', self.DEFAULT_GOALS)
        name = data.get('startOption', None)
        if name is None:
            self.startOption = self.DEFAULT_START_OPTION
        else:
            lookup = {
                value: key
                for key, value in self.START_OPTION_NAMES.items()
            }
            self.startOption = lookup[name]
        
        self.moduleList = data.get('moduleList', [])
        # TODO validate

class ProjectPreferences:
    def __init__(self, project, defaults=None):
        if defaults is None:
            defaults = Defaults()

        self.project = project
        self.defaults = defaults

        self.reset()

    def reset(self):
        self.customPatternPreferences = CustomPatternPreferences(self.defaults.customPatternDefaults)
        self.maven = MavenPreferences()

    def load(self):
        self.reset()

        path = self.getPath()
        if path.exists():
            print(f'Loading preferences from {path}')
            with open(path, encoding='utf-8') as fh:
                data = json.load(fh)

            self.unpickle(data)

    def unpickle(self, data):
        self.reset()

        value = data.get('customPatternPreferences')
        if value is not None:
            self.customPatternPreferences.unpickle(value)

        value = data.get('maven')
        if value is not None:
            self.maven.unpickle(value)

    def pickle(self):
        data = {}

        value = self.customPatternPreferences.pickle()
        if value is not None:
            data['customPatternPreferences'] = value

        value = self.maven.pickle()
        if value is not None:
            data['maven'] = value

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
        with open(path, mode='w', encoding='utf-8', newline='\n') as fh:
            json.dump(data, fh, indent=4, sort_keys=True)
