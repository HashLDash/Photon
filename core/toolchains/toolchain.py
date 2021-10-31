from interpreter import Interpreter

class BaseToolchain():
    def __init__(self, platform, filename='main.w', test=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.platform = platform
        self.test = test
        self.interpreter = Interpreter(filename, standardLibs=standardLibs, transpileOnly=True)

    def logcat(self):
        pass

    def getBuildFiles(self):
        pass

    def transpile(self):
        pass

    def prepare(self):
        pass

    def make(self):
        pass

    def runProject(self):
        pass
