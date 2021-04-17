from interpreter import Interpreter


class Toolchain():
    def __init__(self, platform, test=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.platform = platform
        self.test = test
        self.interpreter = Interpreter('main.w', standardLibs=standardLibs)

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
