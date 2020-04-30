#!python3
# -*- coding: utf-8 -*-

class DummyLogger:
    def log(self, *args):
        pass

    def close(self):
        pass

class MockLogger:
    def __init__(self, *args):
        self.events = []

    def log(self, *args):
        self.events.append(args)

    def close(self):
        pass

class FileLogger:
    def __init__(self, path):
        self.path = path

        print(f'Writing log to {self.path}')
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, mode='w', encoding='utf-8')
        print(self.fh)

    def log(self, type, message):
        self.fh.write(type)
        self.fh.write(' ')
        self.fh.write(message)
        self.fh.write('\n')

    def close(self):
        self.fh.close()
        self.fh = None
