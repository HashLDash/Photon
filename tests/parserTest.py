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
        struct = self.runFile('printFunc1.w')
        self.assertEqual(struct, {
            'token': 'printFunction',
            'expr': {'token': 'expr', 'args': [{'type': 'str', 'value': '"Hello World"'}],
            'ops': []},
            'opcode': 'printFunction'})

    def test_printFunc2(self):
        struct = self.runFile('printFunc2.w')
        self.assertEqual(struct, {
            'token': 'printFunction',
            'expr': {'token': 'expr', 'args': [{'type': 'int', 'value': '26'}],
            'ops': []},
            'opcode': 'printFunction'})

    def test_printFunc3(self):
        struct = self.runFile('printFunc3.w')
        self.assertEqual(struct, {
            'token': 'printFunction',
            'expr': {'token': 'expr', 'args': [{'type': 'float', 'value': '4.7'}],
            'ops': []},
            'opcode': 'printFunction'})

if __name__ == "__main__":
    unittest.main()
