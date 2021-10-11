import sys, os
sys.path.insert(1, os.path.pardir+'/core')
from photonParser import parse
from interpreter import Interpreter
import unittest
from subprocess import Popen, PIPE

class TranspilersTest(unittest.TestCase):
    langs = ['c', 'py', 'js']

    def runFile(self, file, lang='c'):
        out = ''
        result = Popen(f'photon testFiles/{file} --lang {lang}', shell=True, stdout=PIPE)
        for line in result.stdout:
            out += str(line, encoding='utf8').strip()
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
            break
        result.stdout.close()
        result.wait()
        return out

    def checkFile(self, filename, result=None):
        for lang in self.langs:
            out = self.runFile(filename, lang=lang)
            if isinstance(result, int):
                self.assertEqual(int(out), result)
            elif isinstance(result, str):
                self.assertEqual(str(out), result)
            elif isinstance(result, float):
                self.assertAlmostEqual(float(out), result)
            else:
                raise NotImplemented

    def test_printInt(self):
        out = self.checkFile('printFunc/printInt.w', 26)

    def test_printFloat(self):
        self.checkFile('printFunc/printFloat.w', 4.7)

    def test_printFloatDot(self):
        self.checkFile('printFunc/printFloatDot.w', 2.0)

    def test_printStr(self):
        self.checkFile('printFunc/printStr.w', 'Hello World')

    def test_printVar(self):
        self.runFile('printFunc/printVar.w', 2)

if __name__ == "__main__":
    unittest.main()
