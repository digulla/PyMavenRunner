#!python3
# -*- coding: utf-8 -*-

class Version:
    def __init__(self, *numbers):
        self.numbers = tuple(numbers)
    
    def __lt__(self, other):
        return self.numbers < other.numbers

    def __eq__(self, other):
        return self.numbers == other.numbers

    def __repr__(self):
        return '.'.join(map(str, self.numbers))
