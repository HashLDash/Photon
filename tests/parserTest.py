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
        
    def test_printFunc1(self):
        struct = self.runFile('/printFunc/printString.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'type':'str', 'value':'"Hello World"'})

    def test_printFunc2(self):
        struct = self.runFile('printFunc/printInt.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'type':'int', 'value':'26'})

    def test_printFunc3(self):
        struct = self.runFile('printFunc/printFloat.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'type':'float', 'value':'4.7'})

    def test_printFunc4(self):
        struct = self.runFile('printFunc/printFloatDot.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0], {'type':'float', 'value':'2.'})

    def test_printFunc5(self):
        struct = self.runFile('printFunc/printVar.w')
        self.assertEqual(struct['token'], 'printFunc')
        self.assertEqual(struct['expr']['args'][0]['name'], 'var')

if __name__ == "__main__":
    unittest.main()
