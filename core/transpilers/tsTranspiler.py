from transpilers.jsTranspiler import Transpiler as JSTranspiler
import os

def debug(*args):
    #print(*args)
    pass

class Transpiler(JSTranspiler):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.filename = self.filename.replace('.w','.ts')
        self.lang = 'ts'

    def formatPrint(self, value, terminator='\\n'):
        if value['value']:
            return f'Deno.writeAll(Deno.stdout, new TextEncoder().encode(JSON.stringify({value["value"]})+"{terminator}"))'
        return f'Deno.writeAll(Deno.stdout, new TextEncoder().encode("{terminator}"))'

    def write(self):
        boilerPlateStart = [
        ]
        boilerPlateEnd = [
        ]
        indent = 0
        count = 0
        if not 'Sources' in os.listdir():
            os.mkdir('Sources')
        if not 'ts' in os.listdir('Sources'):
           os.mkdir('Sources/ts')
        if not self.module:
            self.filename = 'main.js'
        else:
            self.filename = f'{moduleName}.js'
            boilerPlateStart = []
            boilerPlateEnd = []
            del self.imports[0]
            del self.imports[0]
            del self.imports[0]
        # Force utf8 on windows
        with open(f'Sources/ts/{self.filename}', 'w', encoding='utf8') as f:
            for imp in self.imports:
                module = imp.split(' ')[-1].replace('.w', '').replace('"',  '')
                debug(f'Importing {module}')
                if f'{module}.ts' in os.listdir('Sources/ts'):
                    with open(f'Sources/ts/{module}.js', 'r') as m:
                        for line in m:
                            f.write(line)
                else:
                    f.write(imp + '\n')
            for line in [''] + self.outOfMain + [''] + boilerPlateStart + self.source + boilerPlateEnd:
                if line:
                    if line.startswith('}'):
                        indent -= 4
                    f.write(' ' * indent + line.replace('/*def*/', '') + '\n')
                    if self.isBlock(line):
                        indent += 4
        debug('Generated ' + self.filename)

    def run(self):
        from subprocess import call, check_call
        self.write()
        debug(f'Running {self.filename}')
        try:
            check_call(['deno', 'run', f'Sources/ts/{self.filename}'])
        except Exception as e:
            print(f'Compilation error {e}. Check errors above.')
