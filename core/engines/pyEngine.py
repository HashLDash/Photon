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
        source = list(self.transpiler.imports) + self.transpiler.outOfMain + self.transpiler.source
        code = ''
        indent = 0
        for line in source:
            if line:
                if line.startswith('#end'):
                    indent -= 4
                code += ' '*indent+line+'\n'
                if self.transpiler.isBlock(line):
                    indent += 4
        try:
            if token['token'] in {'expr'}:
                if code[-2] == ';':
                    code = code[:-2]
                bytecode = compile(f'print({code})','<string>','exec')
                exec(bytecode, self.globals, self.globals)
            else:
                bytecode = compile(code,'<string>','exec')
                exec(code, self.globals, self.globals)
        except Exception as e:
            print(f'RuntimeError: {e}')
        self.transpiler.source = []
        self.transpiler.outOfMain = []
        self.transpiler.imports = set()
