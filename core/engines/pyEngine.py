from transpilers.pyTranspiler import Transpiler
import os

def debug(*args):
    #print(*args)
    pass

class Engine():
    def __init__(self, filename, **kwargs):
        self.transpiler = Transpiler(filename, **kwargs)
        self.globals = {}

    def process(self, token):
        self.transpiler.process(token)
        source = self.transpiler.source
        code = ''
        indent = 0
        for line in source:
            if line:
                if line.startswith('#end'):
                    indent -= 4
            code += ' '*indent+line+'\n'
            if self.transpiler.isBlock(line):
                indent += 4
        exec(code, self.globals)
        self.transpiler.source = []
