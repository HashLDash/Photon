# Basic Types
from copy import deepcopy
from pprint import pprint

class Type():
    nativeTypes = {
        'int':'long',
        'str':'char*',
        'float':'double',
        'bool':'int',
        'unknown':'void',
        '':'void',
        'obj':'obj',
    }
    def __init__(self, type, elementType=None, keyType=None, valType=None, returnType=None, funcName=None, argsTypes=None, name=None, namespace='', **kwargs):
        if isinstance(type, Type):
            self.namespace = type.namespace
            self.type = type.type
            self.elementType = type.elementType
            self.keyType = type.keyType
            self.valType = type.valType
            self.returnType = type.returnType
            self.funcName = type.funcName
            self.argsTypes = type.argsTypes
            self.name = type.name
        else:
            if type is not None and type.split(' ')[-1] == 'func':
                if ' ' in type:
                    returnType, type = type.split(' ')
                else:
                    type = 'func'
                    returnType = ''
            self.namespace = namespace
            self.type = type if type is not None else 'unknown'
            self.elementType = Type(elementType) if self.isKnown(self.type) else 'unknown'
            self.keyType = Type(keyType) if self.isKnown(self.type) else 'unknown'
            self.valType = Type(valType) if self.isKnown(self.type) else 'unknown'
            self.returnType = Type(returnType) if self.isKnown(self.type) else 'unknown'
            self.funcName = funcName if self.isKnown(self.type) else None
            self.argsTypes = argsTypes if self.isKnown(self.type) and isinstance(argsTypes, list) else []
            self.name = name

    @property
    def known(self):
        if self.type == 'array' and self.isKnown(self.elementType):
            return True
        elif self.type == 'map' and self.isKnown(self.valType) and self.isKnown(self.keyType):
            return True
        elif self.type == 'func' and self.isKnown(self.returnType):
            return True
        elif self.type not in ['array', 'map'] and self.isKnown(self.type):
            return True
        else:
            return False
    
    @property
    def isModule(self):
        if self.type == 'module' and self.name is not None:
            return True
        else:
            return False

    @property
    def isClass(self):
        if self.known and self.type in self.nativeTypes:
            return False
        elif self.known and not self.type in self.nativeTypes and self.type not in ['array', 'map', 'module'] and not 'func' in self.type.split(' '):
            return True
        else:
            return False

    def isKnown(self, type):
        if isinstance(type, Type):
            return type.known
        if type not in ['unknown', '']:
            return True
        return False
    
    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self.type == 'array':
            return f'list_{self.elementType.type}*'
        elif self.type == 'map':
            return f'dict_{self.keyType.type}_{self.valType.type}*'
        elif self.type == 'func':
            return f'{self.returnType} (*{self.funcName})({", ".join(self.argsTypes)})'
        elif self.type in self.nativeTypes:
            return self.nativeTypes[self.type] 
        elif self.isClass:
            return f'struct {self.type}*'
        else:
            return f'{self.type}'

    def __hash__(self):
        return hash((self.type, self.elementType, self.keyType, self.valType))

    def __eq__(self, obj):
        return hash(obj) == self.__hash__()

class Comment():
    def __repr__(self):
        return ''

    @property
    def index(self):
        return None

class Null():
    imports = []
    def __init__(self):
        self.namespace = ''
        self.type = Type('void')
    
    def prepare(self):
        pass

    def __repr__(self):
        return 'NULL'

    @property
    def index(self):
        return None

class Module():
    def __init__(self, expr, name, namespace):
        self.expr = expr
        self.name = name
        self.namespace = namespace
        self.type = Type('module', name=name)
        self.imports = [f'#include "{self.name}.h"']
        if self.name not in ['time']:
            self.links = [f'-l{self.name}']
        else:
            self.links = []

    def __repr__(self):
        return f'//module {self.name}'

    @property
    def index(self):
        return self.expr.index

class Group():
    imports = []
    def __init__(self, expr):
        self.expr = expr
        self.namespace = expr.namespace
        self.type = expr.type

    def prepare(self):
        pass

    def __repr__(self):
        return f'({self.expr})'

class Scope():
    beginSymbol = '{'
    endSymbol = '}'
    def __init__(self, obj, indent=4):
        if isinstance(obj, Scope):
            self.sequence = obj.sequence
        else:
            if not isinstance(obj, Sequence):
                self.sequence = Sequence(obj)
            else: 
                self.sequence = obj
        self.indent = ' '*indent

    def __repr__(self):
        return f'{self.beginSymbol}\n' + '\n'.join(
            [self.indent + r 
                for r in repr(self.sequence).split('\n')]
        ) + f'\n{self.endSymbol}'

    def extend(self, scope):
        self.sequence = self.sequence + scope.sequence

    def __iter__(self):
        return iter(self.sequence)

class NativeCode():
    imports = []
    def __init__(self, line):
        self.line = line

    def prepare(self):
        pass

    def __repr__(self):
        return self.line

class Obj():
    def __init__(self, value='', type='', namespace='', mode='expr'):
        self.value = value
        self.type = Type(type)
        self.namespace = namespace
        self.mode = mode
        self.imports = []

    def prepare(self):
        pass

    def expression(self):
        return 'Obj-expr'

    def declaration(self):
        return 'Obj-expr'

    def format(self):
        return 'Obj-expr'

    def method(self):
        return 'Obj-method'

    def __repr__(self):
        self.prepare()
        if self.mode == 'expr':
            return self.expression()
        elif self.mode == 'declaration':
            return self.declaration()
        elif self.mode == 'format':
            return self.format()
        elif self.mode == 'method':
            return self.method()
        elif self.mode == 'types':
            return self.types()
        elif self.mode == 'empty':
            return ''
        else:
            raise ValueError(f'Mode {self.mode} not implemented.')

    @property
    def index(self):
        return None

class Bool(Obj):
    def __repr__(self):
        return '1' if self.value == 'true' else '0'

class Num(Obj):
    def __repr__(self):
        return str(self.value)

class String(Obj):
    imports = ['#include "asprintf.h"']
    def __init__(self, expressions='', **kwargs):
        kwargs['type'] = 'str'
        super().__init__(**kwargs)
        self.value = '"' + self.value[1:-1].replace('"', '\\"') + '"'
        self.expressions = expressions if expressions else []
        for expr in self.expressions:
            expr.mode = 'format'
            valType = expr.type.type
            if 'func' in valType:
                valType = valType.replace(' func','').strip()
            if valType == 'str':
                self.value = self.value.replace('{}', '%s', 1)
            elif valType == 'int':
                self.value = self.value.replace('{}', '%ld', 1)
            elif valType == 'float':
                self.value = self.value.replace('{}', '%g', 1)
            elif valType == 'bool':
                self.value = self.value.replace('{}', '%s', 1)
            elif valType == 'array':
                self.value = self.value.replace('{}', '%s', 1)
            elif valType == 'map':
                self.value = self.value.replace('{}', '%s', 1)
            #elif valType in self.classes:
            #    self.value = self.value.replace('{}', '%s', 1)
            else:
                raise SyntaxError(f'Cannot format {valType} in formatStr')

    def __repr__(self):
        if self.expressions:
            return f'__photon_format_str({self.value}, {", ".join([repr(expr) for expr in self.expressions])})'
        return self.value

class Var(Obj):
    imports = []
    def __init__(self, *args, indexAccess=None, attribute=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.indexAccess = indexAccess
        self.attribute = attribute
        self.prepare()

    def prepare(self):
        if self.namespace:
            self.name = f'{self.namespace}__{self.value}'
        else:
            self.name = self.value

    def declaration(self):
        if self.type.type == 'func':
            self.type.funcName = self.value
            return f'{self.type}'
        return f'{self.type} {self.value}'

    def format(self):
        if self.type.type not in ['str','int','float']:
            call = repr(self.type).replace("*","")
            return f'{call}_str({self.name})'
        return self.name

    def method(self):
        return f'{self.name}'

    def expression(self):
        if self.indexAccess:
            if self.type.type == 'array':
                return f'list_{self.type.elementType.type}_get({self.name}, {self.indexAccess})'
            if self.type.type == 'map':
                return f'dict_{self.type.keyType.type}_{self.type.valType.type}_get({self.name}, {self.indexAccess})'
            else:
                return f'{self.name}[{self.indexAccess}]'
        return self.name

    def types(self):
        return f'{self.type}'

    def __hash__(self):
        self.prepare()
        return hash(self.name)

    @property
    def index(self):
        if self.namespace:
            return f'{self.namespace}__{self.value}'
        return f'{self.value}'

class Expr(Obj):
    operatorOrder = [
        'not','**','*','%','/','-','+','==','!=','>','<','>=','<=',
        'is','in','andnot','and','or','&', '<<', '>>'
    ]
    opConversions = {
        'and': '&&',
        'or': '||',
        'not': '!',
    }
    #TODO: not is not implemented
    def __init__(self, *elements, ops=None, **kwargs):
        super().__init__(**kwargs)
        self.elements = list(elements)
        self.ops = ops if ops else []
        if not self.value:
            self.process()
        else:
            # Already processed, so it's native code
            self.value = NativeCode(self.value)

    def prepare(self):
        self.value.mode = self.mode
        self.value.type = self.type
        self.value.namespace = self.namespace
        self.value.prepare()
        self.imports = self.value.imports

    def process(self):
        ops = self.ops.copy()
        elements = deepcopy(self.elements)
        if len(elements) == 1 and len(self.ops) == 1:
            if self.ops[0] == 'not':
                elements[0] = Expr(value=f'!{elements[0]}', type=Type('bool'))
                self.ops = []
        else:
            self.type = 'unknown'
            for op in self.operatorOrder:
                while op in ops:
                    index = ops.index(op)
                    arg1 = elements[index]
                    arg2 = elements[index+1]
                    elements[index] = self.operations(op, arg1, arg2)
                    del ops[index]
                    del elements[index+1]
        self.value = elements[0]
        self.namespace = elements[0].namespace
        self.type = elements[0].type
        self.indexAccess = getattr(elements[0], 'indexAccess', None)

    def operations(self, op, arg1, arg2):
        t = None
        intOrFloat = [Type('int'), Type('float')]
        if op in ['+', '-','*','**']:
            if arg1.type == arg2.type:
                t = arg1.type
            elif arg1.type in intOrFloat or arg2.type in intOrFloat:
                t = Type('float')
            else:
                t = Type('unknown')
        elif op == '/':
            t = Type('float')
        elif op == '%':
            t = Type('int')
        elif op in ['not','==','!=','>','<','>=','<=','in','and','or']:
            t = Type('bool')
        if op in self.opConversions:
            op = self.opConversions[op]
        return Expr(value=f'{arg1} {op} {arg2}', type=t)

    def __repr__(self):
        self.prepare()
        return repr(self.value)

    @property
    def index(self):
        if len(self.elements) == 1:
            return self.elements[0].index
        return super().index

class Delete():
    def __init__(self, expr):
        self.expr = expr

    def __repr__(self):
        self.expr.mode = 'method'
        if self.expr.type.type in ['array', 'map']:
            call = f'{self.expr.type}'.replace('*','')
            return f'{call}_del({self.expr}, {self.expr.value.indexAccess})'
        raise SyntaxError(f'Delete not supported for type {type(self.expr.value)}')

    @property
    def index(self):
        return None

class DotAccess():
    imports = []
    def __init__(self, chain=None, namespace='', mode='expr'):
        self.chain = chain
        self.namespace = namespace
        self.chain[0].namespace = namespace
        self.type = chain[-1].type
        self.indexAccess = getattr(chain[-1], 'indexAccess', None)
        self.mode = mode

    def prepare(self):
        pass

    def format(self):
        if self.type.type not in ['str','int','float']:
            call = repr(self.type).replace("*","")
            return f'{call}_str({self.value})'
        return self.value

    def expression(self):
        chain = [repr(self.chain[0])]
        currentType = self.chain[0].type
        for n, c in enumerate(self.chain[1:]):
            if currentType.isClass and isinstance(c, Call):
                instanceName = chain[n-1]
                chain[n-1] = currentType.type
                chain.append('_')
                c.args.args.insert(0, Var(instanceName, currentType))
                chain.append(repr(c))
            elif currentType.isModule:
                chain[n-1] = ''
                chain.append(repr(c))
            else:
                chain.append('->')
                chain.append(repr(c))
            currentType = c.type
        if self.mode == 'method':
            self.chain[-1].mode = 'method'
            chain[-1] = repr(self.chain[-1])
            self.chain[-1].mode = 'expr'
        return ''.join(chain)

    def __repr__(self):
        self.value = self.expression()
        if self.mode == 'format':
            self.value = self.format()
        return self.value

    @property
    def index(self):
        return None

class Return():
    def __init__(self, expr=None):
        self.expr = expr
        self.type = expr.type

    def __repr__(self):
        return f'return {self.expr}'

    @property
    def index(self):
        return None

class Array():
    def __init__(self, *elements, type=None, mode='expr'):
        self.elements = elements
        self.type = type
        self.prepare()
        self.namespace = ''
        self.mode = mode

    def prepare(self):
        self.len = len(self.elements)
        self.size = 8 if self.len < 8 else self.len
        if self.type.known:
            self.imports = [
                f'#include "list_{self.type.elementType.type}.h"',
                '#include "asprintf.h"']
        else:
            self.imports = []

    def expression(self):
        if self.elements:
            return f'list_{self.type.elementType.type}_constructor({self.len}, {self.size}, ' + ','.join([repr(e) for e in self.elements])+')'
        return f'list_{self.type.elementType.type}_constructor({self.len}, {self.size})'

    def __repr__(self):
        self.prepare()
        value = self.expression()
        if self.mode == 'format':
            return f'list_{self.type.elementType.type}_str({value})'
        return value

class KeyVal():
    def __init__(self, key='', val=''):
        self.key = key
        self.val = val

    def __repr__(self):
        return f'{self.key},{self.val}'

class Map():
    def __init__(self, *keyVals, type=None):
        self.keyVals = keyVals
        self.type = type
        self.namespace = ''
        self.prepare()
    
    def prepare(self):
        if self.type.known:
            self.imports = [
                f'#include "dict_{self.type.keyType.type}_{self.type.valType.type}.h"',
                '#include "asprintf.h"']
        else:
            self.imports = []

    def __repr__(self):
        self.prepare()
        size = 8 if (l:=len(self.keyVals)) < 8 else l
        if self.keyVals:
            return f'dict_{self.type.keyType.type}_{self.type.valType.type}_constructor({len(self.keyVals)},{size},' + ', '.join([repr(kv) for kv in self.keyVals])+')'
        return f'dict_{self.type.keyType.type}_{self.type.valType.type}_constructor({len(self.keyVals)},{size})'

class Input():
    def __init__(self, expr=None, namespace=''):
        self.expr = expr
        self.imports = ['#include "photonInput.h"']
        self.type = Type('str')
        self.namespace = namespace

    def prepare(self):
        pass

    def __repr__(self):
        return f'photonInput({self.expr})'

    @property
    def index(self):
        return None

class Break():
    def __repr__(self):
        return f'break'

    @property
    def index(self):
        return None

# Representation Types

class Sequence():
    def __init__(self, objs=None, terminator=';', apply=None):
        self.terminator = terminator
        self.sequence = [] if objs is None else objs
        self.apply = apply

    def add(self, obj):
        self.sequence.append(obj)

    def __add__(self, sequence):
        if isinstance(sequence, Sequence):
            print(sequence)
            print(type(self.sequence), type(sequence))
            print(type(self.sequence), type(sequence.sequence))
            return Sequence(self.sequence + sequence.sequence)
        raise ValueError(f'Object of type {type(sequence)} cannot be added to Sequence.')

    def __repr__(self):
        representation = ''
        for obj in self.sequence:
            if isinstance(obj, Expr):
                obj.mode = 'declaration'
            if self.apply:
                obj = self.apply(obj)
            representation += f'{obj}{self.terminator}\n'
        return representation

    def __len__(self):
        return len(self.sequence)

    def __getitem__(self, index):
        return self.sequence[index]

    def __iter__(self):
        return iter(self.sequence)

    @property
    def index(self):
        return None

class Cast():
    conversion = {
        'int':{
            'str': 'strtol({self.expr}, NULL, 10)',
            'float': '(long)({self.expr})',
        },
        'float':{
            'str': 'strtod({self.expr}, NULL)',
            'int': '(double)({self.expr})',
        },
        'str':{
            'int': '__photon_format_str("%ld", {self.expr})',
            'float': '__photon_format_str("%lf", {self.expr})',
        },
    }

    def __init__(self, expr, castTo):
        if isinstance(expr, Cast):
            self.expr = expr.expr
        else:
            self.expr = expr
        self.castTo = castTo
        self.type = self.castTo

    def __repr__(self):
        castFrom = self.expr.type.type
        castTo = self.castTo.type
        if castTo == 'map':
            castTo = self.castTo.valType.type
        elif castTo == 'array':
            castTo = self.castTo.elementType.type
        if castFrom == 'map' and self.expr.indexAccess is not None:
            castFrom = self.expr.type.valType
        elif castFrom == 'array' and self.expr.indexAccess is not None:
            castFrom = self.expr.type.elementType
        try:
            if self.castTo.isClass:
                return f'({self.castTo}) {self.expr}'
            elif castTo != castFrom:
                return self.conversion[castTo][castFrom].format(self=self)
            return repr(self.expr)
        except KeyError as e:
            raise SyntaxError(f'Cast not implemented for type {castTo} from {castFrom} {e}')

class Assign(Obj):
    def __init__(self, target='', inMemory=False, cast=None, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.inMemory = inMemory
        self.type = self.target.type
        self.cast = cast

    def declaration(self):
        return f'{self.target.type} {self.target}'

    def expression(self):
        if self.cast is not None:
            self.value = Cast(self.value, self.cast)
            print('Cast assign', self.value)
        if self.inMemory or isinstance(self.target, DotAccess):
            if self.target.indexAccess:
                if self.target.type.type == 'array':
                    return f'list_{self.target.type.elementType}_set({self.target.name}, {self.target.indexAccess}, {self.value})'
                if self.target.type.type == 'map':
                    return f'dict_{self.type.keyType.type}_{self.type.valType.type}_set({self.target.name}, {self.target.indexAccess}, {self.value})'
                else:
                    return f'{self.target.name}[{self.target.indexAccess}] = {self.value}'
            return f'{self.target} = {self.value}'
        else:
            return f'{self.target.type} {self.target} = {self.value}'

    def types(self):
        return f'{self.type}'

    @property
    def index(self):
        return self.target.index

class Args():
    def __init__(self, args, mode='expr'):
        if isinstance(args, Args):
            self.args = args.args
            self.mode = args.mode
        else:
            self.args = args
            self.mode = mode

    def prepare(self):
        for arg in self.args:
            arg.mode = self.mode
    
    def __bool__(self):
        return True if repr(self) else False

    def __getitem__(self, index):
        return self.args[index]

    def __repr__(self):
        self.prepare()
        return ', '.join([repr(arg) for arg in self.args])

class Kwargs():
    def __init__(self, kwargs, mode='expr'):
        if isinstance(kwargs, Kwargs):
            self.kwargs = kwargs.kwargs
            self.mode = kwargs.mode
        else:
            self.kwargs = kwargs
            self.mode = mode

    def prepare(self):
        mode = self.mode
        if mode == 'value':
            # value mode is exclusive for kwarg
            mode = 'expr'
        for kwarg in self.kwargs:
            kwarg.mode = mode

    def __bool__(self):
        return True if repr(self) else False

    def __repr__(self):
        self.prepare()
        if self.mode == 'value':
            return ', '.join([repr(kwarg.value) for kwarg in self.kwargs])
        return ', '.join([repr(kwarg) for kwarg in self.kwargs])

class Call(Obj):
    def __init__(self, name='', args='', kwargs='', signature='', namespace='', **defaults):
        super().__init__(**defaults)
        self.name = name
        self.type = self.name.type
        self.args = Args(args)
        self.kwargs = Kwargs(kwargs)
        self.signature = signature
        self.namespace = namespace

    def prepare(self):
        self.name.namespace = self.namespace

    def __repr__(self):
        if self.signature:
            kwargs = []
            args = [self.args[0]] if len(self.args.args) > 0 else []
            # allocate args then sort kwargs
            for s in self.signature[len(self.args.args):]:
                for kwarg in self.kwargs.kwargs:
                    if isinstance(s, Assign):
                        kwarg.target.namespace = ''
                        if s.target.index == kwarg.target.index:
                            kwargs.append(kwarg)
                            break
                else:
                    kwargs.append(s)
            kwargs = Kwargs(kwargs, mode='value')
            for arg, sig in zip(self.args[1:], self.signature):
                if arg.type != sig.type:
                    target = Var(repr(arg.value), arg.type)
                    args.append(Cast(target, sig.type))
                else:
                    args.append(arg)
            args = Args(args, mode='expr')
        else:
            kwargs = self.kwargs
            args = self.args
        separator = ', ' if self.args and self.kwargs else ''
        if self.type.isClass:
            return f'{self.name}_new({args}{separator}{kwargs})'
        else:
            return f'{self.name}({args}{separator}{kwargs})'

class Function(Obj):
    def __init__(self, name='', args='', kwargs='', code='', signature=None, **defaults):
        super().__init__(**defaults)
        self.name = name
        self.type = name.type
        self.args = Args(args, mode='declaration')
        self.kwargs = Kwargs(kwargs, mode='declaration')
        self.code = Scope(code)
        self.signature = signature if signature is not None else []

    def prepare(self):
        self.separator = ', ' if self.args and self.kwargs else ''

    def declaration(self):
        oldMode = self.args.mode
        self.args.mode = 'types'
        result = f'{self.name.type} (*{self.name})({self.args}{self.separator}{self.kwargs})'
        self.args.mode = oldMode
        return result

    def expression(self):
        return f'{self.name.type} {self.name}({self.args}{self.separator}{self.kwargs}) {self.code}'

    @property
    def index(self):
        return self.name.index

class Class():
    def __init__(self, name='', args='', code='', parameters=None, methods=None, new=None):
        self.name = name
        self.args = Args(args)
        self.code = Scope(code)
        self.type = Type(repr(self.name))
        self.parameters = parameters
        self.methods = methods
        self.new = new

    def declarationMode(self):
        for _, t in self.parameters.items():
            t.mode = 'declaration'
    
    def writeMode(self):
        for _, t in self.methods.items():
            t.mode = 'expr'

    def __repr__(self):
        self.declarationMode()
        parameters = Scope(list(self.parameters.values()))
        value = f'typedef struct {self.name} {parameters} {self.name};\n'
        self.writeMode()
        for method in self.methods.values():
            value += f'{method}\n'
        return value

    @property
    def index(self):
        return self.name.index

class Elif():
    def __init__(self, expr, block):
        self.expr = expr
        self.block = Scope(block)

    def __repr__(self):
        return f'else if ({self.expr}) {self.block}'

class Else():
    def __init__(self, block):
        self.block = Scope(block)

    def __repr__(self):
        return f'else {self.block}'

class If():
    def __init__(self, expr, ifBlock, elifs=None, elseBlock=None):
        self.expr = expr
        self.ifBlock = Scope(ifBlock)
        self.elifs = elifs
        self.elseBlock = Else(elseBlock) if elseBlock is not None else ''

    def __repr__(self):
        return f'if ({self.expr}) {self.ifBlock} {"".join(repr(e) for e in self.elifs)} {self.elseBlock}'

    @property
    def index(self):
        return None

class While():
    def __init__(self, expr, block=None):
        self.expr = expr
        self.block = Scope(block)

    def __repr__(self):
        return f'while ({self.expr}) {self.block}'

    @property
    def index(self):
        return None

class For():
    def __init__(self, args=None, iterable=None, code=None):
        self.args = Args(args)
        self.iterable = iterable
        self.code = Scope(code)

    def __repr__(self):
        if isinstance(self.iterable, Range):
            if len(self.args.args) == 1:
                return f'for ({self.args[0].type} {self.args[0]}={self.iterable.initial}; {self.args[0]} < {self.iterable.final}; {self.args[0]} += {self.iterable.step}) {self.code}'
            if len(self.args.args) == 2:
                return f'{{{self.args[0].type} {self.args[0]}=0; for ({self.args[1].type} {self.args[1]}={self.iterable.initial}; {self.args[1]} < {self.iterable.final}; {self.args[0]}++, {self.args[1]} += {self.iterable.step}) {self.code}}}'
        elif isinstance(self.iterable, Expr):
            if self.iterable.type.type == 'array':
                if len(self.args.args) == 1:
                    iterableVar = f'__iterable_{self.args[0]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[0].type} {self.args[0]} = {iterableVar}->values[0]; for (long __forIndex=0; __forIndex < {iterableVar}->len; __forIndex++, {self.args[0]} = {iterableVar}->values[__forIndex]) {self.code}}}'
                if len(self.args.args) == 2:
                    iterableVar = f'__iterable_{self.args[1]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[1].type} {self.args[1]} = {iterableVar}->values[0]; for ({self.args[0].type} {self.args[0]}=0; {self.args[0]} < {iterableVar}->len; {self.args[0]}++, {self.args[1]} = {iterableVar}->values[{self.args[1]}]) {self.code}}}'
            if self.iterable.type.type == 'map':
                if len(self.args.args) == 1:
                    iterableVar = f'__iterable_{self.args[0]}'
                    iterableIndex = f'__iterable_index_{self.args[0]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[0].type} {self.args[0]} = {iterableVar}->entries[0].key; for (long {iterableIndex}=0; {iterableIndex} < {iterableVar}->len; {iterableIndex}++, {self.args[0]} = {iterableVar}->entries[{iterableIndex}].key) {self.code}}}'
                if len(self.args.args) == 2:
                    iterableVar = f'__iterable_{self.args[1]}'
                    iterableIndex = f'__iterable_index_{self.args[1]}'
                    return f'{{{self.iterable.type} {iterableVar} = {self.iterable};\n{self.args[0].type} {self.args[0]} = {iterableVar}->entries[0].key;\n{self.args[1].type} {self.args[1]} = {iterableVar}->entries[0].val;\nfor (long {iterableIndex}=0; {iterableIndex} < {iterableVar}->len; {iterableIndex}++, {self.args[0]} = {iterableVar}->entries[{iterableIndex}].key, {self.args[1]} = {iterableVar}->entries[{iterableIndex}].val) {self.code}}}'
        else:
            raise ValueError(f'Iterable of type {type(self.iterable)} no supported in for.')

    @property
    def index(self):
        return None

class Range():
    def __init__(self, initial=None, final=None, step=None):
        self.initial = initial
        self.final = final
        self.step = step
        if self.initial.type.type == 'int' and self.step.type.type == 'int':
            self.type = Type('int')
        else:
            self.type = Type('float')

class AugAssign():
    def __init__(self, target=None, expr=None, operator=None):
        self.target = target
        self.expr = expr
        self.operator = operator

    def __repr__(self):
        if self.operator in ['+','-','*','/','%','&']:
            return f'{self.target} {self.operator}= {self.expr}'
        raise NotImplemented('operator not implemented')

    @property
    def index(self):
        return None

if __name__ == '__main__':
    pass
    #print(
    #    Scope(Sequence(
    #        Assign(
    #            target=Var('test', 'float'),
    #            value=Num(1, 'int')),
    #        Assign(
    #            target=Var('lol'),
    #            value=Array(Num(1, 'int'), Num(2, 'int')))
    #    ), indent=6)
    #)
    #print(
    #    Function(
    #        name=Var('myFunc', 'int'),
    #        args=[Var('arg1', 'int')],
    #        kwargs=[Assign(
    #            target=Var('test', 'float'),
    #            value=Num(1, 'int'))],
    #        code=Sequence(
    #            Assign(
    #                target=Var('test', 'float'),
    #                value=Num(1, 'int')),
    #            Assign(
    #                target=Var('lol'),
    #                value=Array(Num(1, 'int'), Num(2, 'int')))
    #        )
    #    )
    #)
    #print(Expr(Num(1, 'int'), Num(2, 'int'), ops=['and']))
    #print(Expr(Num(1, 'float'), Num(2, 'int'), Num(3, 'int'), ops=['-','+']))
    #print(Map(KeyVal(Num(1, 'float'), Num(2, 'int'))))
    #print(
    #    Class(
    #        name=Var('myClass', 'int'),
    #        args=[Var('arg1', 'int')],
    #        code=Sequence(
    #            Assign(
    #                target=Var('test', 'float'),
    #                value=Num(1, 'int')),
    #            Assign(
    #                target=Var('lol'),
    #                value=Array(Num(1, 'int'), Num(2, 'int'))),
    #            Function(
    #                name=Var('myFunc', 'int'),
    #                args=[Var('arg1', 'int')],
    #                kwargs=[Assign(
    #                    target=Var('test', 'float'),
    #                    value=Num(1, 'int'))],
    #                code=Sequence(
    #                    Assign(
    #                        target=Var('test', 'float'),
    #                        value=Num(1, 'int')),
    #                    Assign(
    #                        target=Var('lol'),
    #                        value=Array(Num(1, 'int'), Num(2, 'int')))
    #                )
    #            )
    #        )
    #    )
    #)
