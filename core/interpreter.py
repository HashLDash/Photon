# Photon Interpreter
#
# This script funcion is:
#   - Get lines of code from a file or interpreter
#   - Call the parser to generate tokens and the struct   
#   - Call the engine to Process the struct
#   - Run the processed struct

from photonParser import parse, assembly
import sys

class Interpreter():
    def __init__(self, filename='', lang='c', target=sys.platform, module=False, standardLibs=''):
        if lang == 'c':
            from transpilers.cTranspiler import Transpiler
        elif lang == 'dart':
            from transpilers.dartTranspiler import Transpiler
        elif lang == 'js':
            from transpilers.jsTranspiler import Transpiler
        elif lang == 'haxe':
            from transpilers.haxeTranspiler import Transpiler
        elif lang == 'd':
            from transpilers.dTranspiler import Transpiler
        self.filename = filename
        if filename:
            self.engine = Transpiler(filename=filename,target=target, module=module, standardLibs=standardLibs)
            self.input = self.file
            with open(filename,'r') as f:
                self.source = [line for line in f]
        else:
            try:
                import readline
            except ModuleNotFoundError:
                # Windows doesn't have readline
                try:
                    import pyreadline
                except ModuleNotFoundError:
                    # Run without history and arrow key functionality
                    pass
            from engines.pyEngine import Engine
            self.engine = Engine(filename=filename,target=target, module=module, standardLibs=standardLibs)
            self.input = self.console
        self.end = False
        self.processing = True
        self.transpileOnly = False
        self.lineNumber = 0

    def console(self, glyph='>>> '):
        return input(glyph)

    def file(self, *args):
        try:
            line = self.source.pop(0)
            self.lineNumber += 1
            while line.strip() == '':
                line = self.source.pop(0)
                self.lineNumber += 1
            rest = ''
            count = 1 # checking where is the end of the function call. When it ends, count is 0
            while line[-2:] in {'(\n',',\n','{\n','[\n'} or rest.lstrip() in  {')\n',']\n','}\n'} and count > 0:
                line = line.replace('\n','')
                rest = self.source.pop(0).lstrip()
                self.lineNumber += 1
                while rest.strip() == '':
                    rest = self.source.pop(0)
                    self.lineNumber += 1
                if rest.lstrip() in {')\n',']\n','}\n'}:
                    if ')' in rest:
                        count -= 1
                    if line[-1] == ',':
                        line = line[:-1]
                    rest = rest.lstrip()
                line += rest
            return line
        except IndexError:
            if self.processing:
                return ''
            else:
                if not self.transpileOnly:
                    self.engine.run()
                    sys.exit()
                else:
                    self.engine.write()
                    self.classes = self.engine.classes
                    return 'exit'
    
    def getBlock(self, indent):
        ''' Return a list of code corresponding to the indentation level
        '''
        self.line = self.input('... ')
        blockTokenized = parse(self.line, filename=self.filename, no=self.lineNumber)
        blockIndent = blockTokenized[0]['indent']
        block = []
        if blockIndent > indent:
            struct, nextLine = self.handleTokenized(blockTokenized)
            block.append(struct)
            if not nextLine:
                self.line = self.input('... ')
            blockTokenized = parse(self.line, filename=self.filename, no=self.lineNumber)
            while blockTokenized[0]['indent'] == blockIndent:
                struct, nextLine = self.handleTokenized(blockTokenized)
                block.append(struct)
                if not nextLine:
                    self.line = self.input('... ')
                blockTokenized = parse(self.line, filename=self.filename, no=self.lineNumber)
            return block, blockTokenized
        else:
            return block, blockTokenized
            raise SyntaxError(f'Expecting an indented block here.\nLine: {self.line}')

    def handleBlock(self, tokenized):
        ''' Return a struct with a block and possibly modifiers '''
        indent = tokenized[0]['indent']
        block, nextTokenized = self.getBlock(indent)
        tokenized = assembly(tokenized, block=block)
        if len(nextTokenized) > 1:
            while nextTokenized[1]['token'] in {'elifStatement','elseStatement'} and nextTokenized[0]['indent'] == indent:
                block, afterTokenized = self.getBlock(indent)
                nextTokenized = assembly(nextTokenized, block=block)
                tokenized = assembly(tokenized, modifier=nextTokenized)
                nextTokenized = afterTokenized
                if len(nextTokenized) == 1:
                    break
        struct = assembly(tokenized)
        return struct

    def handleTokenized(self, tokenized):
        ''' Return a struct to be processed by the VM '''
        ''' And if there is a line to be processed in the buffer (self.line) '''
        if tokenized[-1]['token'] == 'beginBlock':
            struct = self.handleBlock(tokenized)
            return struct, True
        else:
            struct = assembly(tokenized)
            return struct, False

    def run(self):
        nextLine = False
        while True:
            if not nextLine or self.line == '':
                self.line = self.input('>>> ')
            self.processing = True
            if self.line == 'exit':
                break
            tokenized = parse(self.line, filename=self.filename, no=self.lineNumber)
            struct, nextLine = self.handleTokenized(tokenized)
            self.engine.process(struct)
            self.processing = False

if __name__ == "__main__":
    try:
        filename = sys.argv[1]
    except IndexError:
        filename = ''
    Interpreter(filename).run()

