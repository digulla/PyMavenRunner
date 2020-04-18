#!python3
# -*- coding: utf-8 -*-

class Version:
    def __init__(self, numbers):
        self.numbers = numbers
    
    def __lt__(self, other):
        n1 = len(self.numbers)
        n2 = len(other.numbers)
        n = max(n1, n2)
        
        for i in range(0, n):
            v1 = self.numbers[i] if i < n1 else -1
            v2 = other.numbers[i] if i < n2 else -1
            
            if v1 > v2:
                return False
        
        return True
            
    def __eq__(self, other):
        return self.numbers == other.numbers

    def __repr__(self):
        return '.'.join(str(x) for x in self.numbers)
