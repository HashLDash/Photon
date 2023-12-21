from interpreter import Interpreter
from copy import deepcopy
import os
from pprint import pprint
from .tokens import *

class CurrentScope():
    def __init__(self):
        self.currentScope = {}
        self.localScope = {}
        self.local = False

    def startLocalScope(self):
        self.local = True
        self.localScope = {}

    def endLocalScope(self):
        self.local = False
        self.localScope = {}

    def add(self, token):
        print(f'Called for token {token}')
        if not isinstance(token, Var) and token.index is not None:
            print(f'adding {token.index} with type {token.type.type}')
            if self.local:
                self.localScope[token.index] = token
            else:
                self.currentScope[token.index] = token

    def update(self, scope):
        self.currentScope.update(scope.currentScope)
        self.localScope.update(scope.localScope)

    def __repr__(self):
        s = 'SCOPE DUMP\n'
        for i, t in {**self.currentScope, **self.localScope}.items():
            s += f'"{i}" {t.type}\n'
        return s

    def get(self, index):
        return {**self.currentScope, **self.localScope}[index]

    def inMemory(self, obj):
        try:
            print('Checking memory')
            a = self.get(obj.index)
            print(f'Yep, in memory: {a}')
            return True
        except KeyError:
            return False
        
    def typeOf(self, obj):
        #TODO CLASS INSTANCE IS NOT BEING FOUND
        try:
            return self.get(obj.index).type
        except KeyError:
            return Type('unknown')

class BaseTranspiler():
    def __init__(self, filename, target='web', module=False, standardLibs='', debug=False):
        self.debug = debug
        self.standardLibs = standardLibs
        self.target = target
        self.lang = 'photon'
        self.libExtension = 'photonExt'
        self.filename = filename.split('/')[-1].replace('.w','.photon')
        self.moduleName = self.filename.replace('.photon','')
        self.module = module

        self.instructions = {
            'printFunc': self.processPrint,
            'inputFunc': self.processInput,
            'expr': self.processExpr,
            'assign': self.processAssign,
            'augAssign': self.processAugAssign,
            'if': self.processIf,
            'while': self.processWhile,
            'for': self.processFor,
            'forTarget': self.processForTarget,
            'func': self.processFunc,
            'class': self.processClass,
            'return': self.processReturn,
            'breakStatement': self.processBreak,
            'comment': self.processComment,
            'import': self.processImport,
            'num': self.processNum,
            'var': self.processVar,
            'floatNumber': self.processNum,
            'str': self.processString,
            'call': self.processCall,
            'array': self.processArray,
            'map': self.processMap,
            'keyVal': self.processKeyVal,
            'dotAccess': self.processDotAccess,
            'range': self.processRange,
            'return': self.processReturn,
            'bool': self.processBool,
            'group': self.processGroup,
        }

        self.sequence = Sequence()
        self.currentScope = CurrentScope()
        self.currentNamespace = self.moduleName

    def typeOf(self, obj):
        if obj.type.known:
            return obj.type
        if isinstance(obj, String):
            return Type('str')
        try:
            return self.currentScope.typeOf(obj)
        except Exception as e:
            print(f'Exception in typeOf {e}')
            return Type('unknown')

    def process(self, token):
        print('Processing:')
        pprint(token)
        if token is not None:
            processedToken = self.instructions[token['opcode']](token)
            if processedToken is not None:
                self.currentScope.add(processedToken)
                self.sequence.add(processedToken)

    def preprocess(self, token):
        processedToken = self.instructions[token['token']](token)
        return processedToken

    def processNum(self, token):
        return Num(value=token['value'], type=token['type'])

    def processBool(self, token):
        return Bool(value=token['value'])

    def processGroup(self, token):
        return Group(expr=self.preprocess(token['expr']))

    def processString(self, token):
        for i in String.imports:
            self.imports.add(i)
        expressions = self.processTokens(token['expressions'])
        return String(
            value=token['value'],
            expressions=expressions,
        )

    def processInput(self, token):
        return Input(
            expr=self.preprocess(token['expr']),
        )

    def processVar(self, token):
        indexAccess = self.preprocess(token['indexAccess']) if 'indexAccess' in token else None
        var = Var(
            value=token['name'],
            type=Type(**token),
            namespace=self.currentNamespace,
            indexAccess=indexAccess,
        )
        if not var.type.known:
            var.type = self.typeOf(var)
        return var

    def processArray(self, token):
        def inferType():
            types = set()
            for element in elements:
                types.add(element.type.type)
            if len(types) == 1:
                elementType = element.type.type
            elif types == {Type('int'), Type('float')}:
                elementType = 'float'
            else:
                elementType = 'unknown'
            return Type('array', elementType=elementType)

        elements = self.processTokens(token['elements'])
        arrayType = Type(**token)
        if not arrayType.known:
            arrayType = inferType()
        array = Array(
            *elements,
            type=arrayType,
        )
        for i in array.imports:
            self.imports.add(i)
        self.listTypes.add(array.type.elementType.type)
        return array

    def processMap(self, token):
        def inferType():
            keyTypes = set()
            valTypes = set()
            for keyVal in keyVals:
                keyTypes.add(keyVal.key.type)
                valTypes.add(keyVal.val.type)
            if len(keyTypes) == 0:
                return Type('map')
            if len(keyTypes) == 1:
                keyType = keyVal.key.type
            else:
                raise NotImplemented('Keys of different types not implemented yet')
            if len(valTypes) == 1:
                valType = keyVal.val.type
            else:
                raise NotImplemented('Vals of different types not implemented yet')
            return Type('map', keyType=keyType, valType=valType)

        keyVals = self.processTokens(token['elements'])
        mapType = Type(**token)
        if not mapType.known:
            mapType = inferType()
        obj = Map(
            *keyVals,
            type=mapType,
        )
        for i in obj.imports:
            self.imports.add(i)
        if obj.type.known:
            self.dictTypes.add((obj.type.keyType.type, obj.type.valType.type))
        input(f'{self.dictTypes} {obj.type} {mapType}')
        return obj

    def processKeyVal(self, token):
        return KeyVal(
            key=self.preprocess(token['key']),
            val=self.preprocess(token['val'])
        )

    def processExpr(self, token):
        return Expr(
            *[self.preprocess(t) for t in token['args']],
            ops = token['ops']
        )

    def processAssign(self, token):
        target = self.preprocess(token['target'])
        value = self.preprocess(token['expr'])
        inMemory = self.currentScope.inMemory(target)
        if inMemory:
            target.type = self.typeOf(target)

        if target.type.known and value.type.known:
            cast = target.type
        else:
            cast = None
        if not target.type.known:
            print(f'Infering type from expr {target} {target.type} {self.typeOf(target)}')
            target.type = value.type
        if not value.type.known:
            print(f'Infering type from target {target} {target.type} {self.typeOf(target)}')
            value.type = target.type
        assign = Assign(
            target=target,
            value=value,
            namespace=self.currentNamespace,
            inMemory=inMemory,
            cast=cast,
        )
        value.prepare()
        for i in value.imports:
            self.imports.add(i)
            if value.type.type == 'map':
                self.dictTypes.add((value.type.keyType.type, value.type.valType.type))
            if value.type.type == 'array':
                self.listTypes.add(value.type.elementType.type)
        return assign

    def processAugAssign(self, token):
        return AugAssign(
            target=self.preprocess(token['target']),
            expr=self.preprocess(token['expr']),
            operator=token['operator']
        )

    def processIf(self, token):
        #TODO: create context manager for localScope
        self.currentScope.startLocalScope()
        ifBlock = self.processTokens(token['block'], addToScope=True)
        self.currentScope.endLocalScope()
        elifs = []
        if 'elifs' in token:
            for e in token['elifs']:
                self.currentScope.startLocalScope()
                elifs.append(
                    Elif(
                        self.preprocess(e['expr']),
                        self.processTokens(e['elifBlock'], addToScope=True)
                    )
                )
                self.currentScope.endLocalScope()
        self.currentScope.startLocalScope()
        elseBlock = None if not 'else' in token else self.processTokens(token['else'], addToScope=True)
        self.currentScope.endLocalScope()
        return If(
            expr = self.preprocess(token['expr']),
            ifBlock = ifBlock,
            elifs = elifs,
            elseBlock = elseBlock,
        )

    def processWhile(self, token):
        return While(
            expr=self.preprocess(token['expr']),
            block=self.processTokens(token['block'])
        )

    def processFor(self, token):
        iterable = self.preprocess(token['iterable'])
        self.currentScope.startLocalScope()
        args = self.processTokens(token['vars'])
        if isinstance(iterable, Range):
            if len(args) == 1:
                args[0].type = iterable.type
            elif len(args) == 2:
                args[0].type = Type('int')
                args[1].type = iterable.type
            else:
                raise SyntaxError('For with range cannot have more than 2 variables')
        elif isinstance(iterable, Expr):
            if iterable.type.type == 'array':
                if len(args) == 1:
                    args[0].type = Type(iterable.type.elementType)
                elif len(args) == 2:
                    args[0].type = Type('int')
                    args[1].type = Type(iterable.type.elementType)
            elif iterable.type.type == 'map':
                if len(args) == 1:
                    args[0].type = Type(iterable.type.keyType)
                elif len(args) == 2:
                    args[0].type = Type(iterable.type.keyType)
                    args[1].type = Type(iterable.type.valType)
        else:
            raise ValueError(f'Iterable with type {type(iterable)} not supported in processFor')
        for t in args:
            self.currentScope.add(Assign(target=t, value=Num(0, t.type)))
        code=self.processTokens(token['block'])
        self.currentScope.endLocalScope()
        return For(
            code=code,
            args=args,
            iterable=iterable,
        )

    def processForTarget(self, token):
        target = token['target'].lower()
        if target in [self.lang, self.target]:
            block = self.processTokens(token['block'])
        else:
            block = []
        return Sequence(block)

    def processCall(self, token, className=None):
        callType = self.preprocess(token['name']).type
        if callType.isClass:
            scope = self.currentScope.get(callType.type).parameters
            #args = [f for f in scope]
        return Call(
            name=self.processVar(token['name']),
            args=self.processTokens(token['args']),
            kwargs=self.processTokens(token['kwargs']),
        )

    def processDotAccess(self, token):
        initialType = self.preprocess(token['dotAccess'][0]).type
        oldNamespace = self.currentNamespace
        self.currentNamespace = ''
        chain = self.processTokens(token['dotAccess'])
        chain[0].type = initialType
        currentType = initialType
        for c in chain[1:]:
            input(f'Chaining {c}')
            if currentType.isClass:
                scope = self.currentScope.get(currentType.type).__dict__
                if c.index in scope['parameters']:
                    print('parameter')
                    c.type = scope['parameters'][c.index].type
                elif isinstance(c, Call):
                    methodIndex = f'{currentType.type}_{c.name}'
                    if methodIndex in scope['methods']:
                        c.type = scope['methods'][methodIndex].type
                        print(f'ITS A METHODDDDDDDDDDDDDDDDDDDdd with type {c.type}')
            elif currentType.type == 'map': #TODO: Make this part of the token class
                if f'{c}' == 'len':
                    c.type = Type('int')
            elif currentType.type == 'array': #TODO: Make this part of the token class
                if f'{c}' == 'len':
                    c.type = Type('int')
            elif currentType.type == 'module':
                if isinstance(c, Call):
                    print(self.currentScope)
                    c.name.namespace = currentType.name
                    c.type = self.currentScope.get(c.name).type
                elif isinstance(c, Var):
                    c.namespace = currentType.name
                    print(self.currentScope)
                    input(c.index)
                    c.type = self.currentScope.get(c.index).type

            currentType = c.type
        for c in chain:
            print(c.type)
        input('Correct?')
        self.currentNamespace = oldNamespace
        return DotAccess(
            chain,
            namespace=oldNamespace,
        )

    def processClass(self, token):
        return Class(
            name=Var(token['name'], namespace=self.currentNamespace),
            args=self.processTokens(token['args']),
            code=self.processTokens(token['block'])
        )

    def processFunc(self, token):
        self.currentScope.startLocalScope()
        oldNamespace = self.currentNamespace
        self.currentNamespace = ''
        #TODO WARNING: Global variables cannot be called inside
        #because the namespace will be different
        #in the local scope
        #use global syntax or try to infer global variables
        args=self.processTokens(token['args'])
        kwargs=self.processTokens(token['kwargs'])
        for t in args + kwargs:
            self.currentScope.add(t)
        code=self.processTokens(token['block'], addToScope=True)
        self.currentNamespace = oldNamespace
        self.currentScope.endLocalScope()
        returnType = Type(token['type'])
        if not returnType.known:
            print('infering function returnType')
            types = []
            for t in code:
                if isinstance(t, Return):
                    types.append(t.type.type)
            if len(set(types)) == 1:
                returnType = Type(types[0])
            elif len(set(types)) == 2 and 'int' in types and 'float' in types:
                returnType = Type('float')
        print(f'Return type is {returnType}') 
        return Function(
            name=Var(
                token['name'],
                type=returnType,
                namespace=self.currentNamespace,
            ),
            args=args,
            kwargs=kwargs,
            code=code,
        )

    def processRange(self, token):
        return Range(
            initial=self.preprocess(token['from']),
            final=self.preprocess(token['to']),
            step=self.preprocess(token['step']) if 'step' in token else Num(1, 'int'),
        )

    def processReturn(self, token):
        return Return(
            expr=self.preprocess(token['expr'])
        )

    def processBreak(self, token):
        return Break()

    def processComment(self, token):
        pass

    def processImport(self, token):
        #TODO: relative path and package imports
        folder = None
        #self.oldNamespace = self.currentNamespace
        #self.currentNamespace = ''
        moduleExpr = self.preprocess(token['expr'])
        input(moduleExpr.namespace)
        input(token['expr'])
        #self.currentNamespace = self.oldNamespace
        moduleExpr.namespace = ''
        name = f'{moduleExpr}'
        moduleExpr.namespace = self.currentNamespace
        print(f'Importing {name}')
        if f"{name}.w" in os.listdir(folder) + os.listdir(self.standardLibs):
            if f"{name}.w" in os.listdir(self.standardLibs):
                filename = f'{self.standardLibs}/{name}.w'
                # Photon module import
                # Inject assets folder
                #raise SyntaxError('Standard lib import not implemented yet.')
            else:
                # Local module import
                moduleExpr.namespace = ''
                filename = f'{name}.w'
                moduleExpr.namespace = self.currentNamespace
            interpreter = Interpreter(
                    filename=filename,
                    lang=self.lang,
                    target=self.target,
                    module=True,
                    standardLibs=self.standardLibs,
                    transpileOnly=True,
                    debug=self.debug)
            interpreter.run()
            self.classes.update(interpreter.engine.classes)
            print('Added scope: {interpreter.engine.currentScope}')
            self.currentScope.update(interpreter.engine.currentScope)
            self.imports = self.imports.union(interpreter.engine.imports)
            self.links = self.links.union(interpreter.engine.links)
            self.outOfMain += interpreter.engine.outOfMain
            self.source += interpreter.engine.source
            self.header += interpreter.engine.header
            self.sequence = self.sequence + interpreter.engine.sequence
        elif f"{name}.{self.libExtension}" in os.listdir(self.standardLibs + f'/native/{self.lang}/'):
            # Native Photon lib module import
            raise SyntaxError('Native Photon lib module import not implemented yet.')
        elif f"{name}.{self.libExtension}" in os.listdir():
            # Native Photon local module import
            raise SyntaxError('Native Photon local module import not implemented yet.')
        else:
            # System library import
            pass
            #raise SyntaxError('System library import not implemented yet.')
        return Module(moduleExpr, name)

    def processTokens(self, tokens, addToScope=False):
        if addToScope:
            processedTokens = []
            for t in tokens:
                processedToken = self.preprocess(t)
                self.currentScope.add(processedToken)
                processedTokens.append(processedToken)
            return processedTokens
        return [self.preprocess(t) for t in tokens]

    def processPrint(self, token):
        formats = {
            'str': '%s',
            'int': '%ld',
            'float': '%g',
            'array': '%s',
            'map': '%s',
        }
        args = self.processTokens(token['args'])
        types = []
        for arg in args:
            argType = self.typeOf(arg)
            if argType.type == 'map':
                if getattr(arg, 'indexAccess', None) is not None:
                    argType = argType.valType
            elif argType.type == 'array':
                if getattr(arg, 'indexAccess', None) is not None:
                    argType = argType.elementType
            elif argType.type == 'func':
                argType = argType.returnType
                argType.funcName = arg.value
            types.append(argType)
        template = String(value='"'+" ".join([formats[t.type] for t in types])+'\\n"')
        args.insert(0, template)
        for arg in args:
            arg.mode = 'format'
        return Call(
            name = Var('printf', 'unknown', namespace=''),
            args = args,
        )

    def run(self):
        print('Running')
