import sys, os
sys.path.insert(1, os.path.pardir+'/core')
from photonParser import parse
from interpreter import Interpreter
import unittest
from subprocess import Popen, PIPE

class TranspilersTest(unittest.TestCase):
    def runFile(self, file, lang='c'):
        result = Popen(f'photon testFiles/{file}', shell=True, stdout=PIPE)
        result.stdout
        out = str(result.stdout.readlines()[0].strip(), encoding='utf8')
        result.stdout.close()
        return out

    def test_printInt(self):
        out = self.runFile('printFunc/printInt.w')
        self.assertEqual(out, '26')

    def test_printFloat(self):
        out = self.runFile('printFunc/printFloat.w')
        self.assertAlmostEqual(float(out), 4.7)

    def test_printStr(self):
        out = self.runFile('printFunc/printStr.w')
        self.assertAlmostEqual(out, 'Hello World')

if __name__ == "__main__":
    unittest.main()
