from transpilers.pyTranspiler import Transpiler
from transpilers.pyTokens import Sequence, Print
import os

def debug(*args):
    #print(*args)
    pass

class Engine():
    def __init__(self, filename, **kwargs):
        self.transpiler = Transpiler(filename, **kwargs)
        self.globals = {}
        self.importedLibs = set()

    def process(self, token):
        if token:
            self.transpiler.process(token)
            for lib in self.transpiler.imports - self.importedLibs:
                bytecode = compile(lib,'<string>','exec')
                exec(bytecode, self.globals, self.globals)
                self.importedLibs.add(lib)
            try:
                if token['token'] in {'expr'}:
                    code = repr(Print(args=[self.transpiler.sequence[-1]]))
                    bytecode = compile(code,'<string>','exec')
                    exec(bytecode, self.globals, self.globals)
                else:
                    code = repr(self.transpiler.sequence[-1])
                    bytecode = compile(code,'<string>','exec')
                    exec(code, self.globals, self.globals)
            except Exception as e:
                print(f'RuntimeError: {e}')
            #self.transpiler.sequence = Sequence()
            #self.transpiler.imports = set()
