class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs=''):
        self.standardLibs = standardLibs
        self.target = target
        self.filename = filename.split('/')[-1].replace('.w','.d')
        self.module = module

    def process(self, token):
        print('Processing')

    def run(self):
        print('Running')
