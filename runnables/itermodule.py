from types import ModuleType
import sys

class WTF(ModuleType):

    def __iter__(self):
        while True:
            yield 4

sys.modules[__name__] = WTF('wtf', 'seriously wtf')
