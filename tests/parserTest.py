import sys, os
sys.path.insert(1, os.path.pardir+'/core')
from parser import parse
from interpreter import Interpreter
import unittest

class ParserTest(unittest.TestCase):
    def runFile(self, file):
        i = Interpreter(os.path.pardir+'/tests/testFiles/'+file)

        nextLine = False
        while True:
            if not nextLine or i.line == '':
                i.line = i.input('>>> ')
            i.processing = True
            if i.line == 'exit' or not i.line:
                break
            tokenized = parse(i.line, filename=i.filename, no=i.lineNumber)
            struct, nextLine = i.handleTokenized(tokenized)
        return struct
        
    def test_printStr(self):
        struct = self.runFile('/printFunc/printStr.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'token':'str', 'type':'str', 'value':'"Hello World"'})

    def test_printInt(self):
        struct = self.runFile('printFunc/printInt.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'token':'num', 'type':'int', 'value':'26'})

    def test_printFloat(self):
        struct = self.runFile('printFunc/printFloat.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'token':'floatNumber','type':'float', 'value':'4.7'})

    def test_printFloatDot(self):
        struct = self.runFile('printFunc/printFloatDot.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'token':'floatNumber','type':'float', 'value':'2.'})

    def test_printVar(self):
        struct = self.runFile('printFunc/printVar.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0]['name'], 'var')

    def test_varInitInt(self):
        struct = self.runFile('varInit/initInt.w')
        self.assertEqual(struct['token'], 'expr')
        self.assertEqual(struct['args'][0]['name'], 'a')
        self.assertEqual(struct['args'][0]['type'], 'int')

    def test_varInitFloat(self):
        struct = self.runFile('varInit/initFloat.w')
        self.assertEqual(struct['token'], 'expr')
        self.assertEqual(struct['args'][0]['name'], 'a')
        self.assertEqual(struct['args'][0]['type'], 'float')

    def test_varInitStr(self):
        struct = self.runFile('varInit/initStr.w')
        self.assertEqual(struct['token'], 'expr')
        self.assertEqual(struct['args'][0]['name'], 'a')
        self.assertEqual(struct['args'][0]['type'], 'str')

    def test_varInitClass(self):
        struct = self.runFile('varInit/initClass.w')
        self.assertEqual(struct['token'], 'expr')
        self.assertEqual(struct['args'][0]['name'], 'a')
        self.assertEqual(struct['args'][0]['type'], 'SomeClass')

    def test_varInitStrArray(self):
        struct = self.runFile('varInit/initStrArray.w')
        self.assertEqual(struct['token'], 'expr')
        self.assertEqual(struct['args'][0]['name'], 'array')
        self.assertEqual(struct['args'][0]['elementType'], 'str')
        self.assertEqual(struct['args'][0]['len'], '10')

    def test_varInitClassArray(self):
        struct = self.runFile('varInit/initClassArray.w')
        self.assertEqual(struct['token'], 'expr')
        self.assertEqual(struct['args'][0]['name'], 'array')
        self.assertEqual(struct['args'][0]['type'], 'array')
        self.assertEqual(struct['args'][0]['elementType'], 'SomeClass')
        self.assertEqual(struct['args'][0]['len'], '10')


if __name__ == "__main__":
    unittest.main()
