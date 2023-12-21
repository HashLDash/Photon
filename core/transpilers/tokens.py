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
    def __init__(self, type, elementType=None, keyType=None, valType=None, returnType=None, funcName=None, argsTypes=None, name=None, **kwargs):
        if isinstance(type, Type):
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
            return f'{self.type}*'
        else:
            return f'{self.type}'

    def __hash__(self):
        return hash((self.type, self.elementType, self.keyType, self.valType))

    def __eq__(self, obj):
        return hash(obj) == self.__hash__()

class Module():
    def __init__(self, expr, name):
        self.expr = expr
        self.name = name
        self.type = Type('module', name=name)
        self.imports = [f'#include "{self.name}.h"']

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

    def __repr__(self):
        self.prepare()
        if self.mode == 'expr':
            return self.expression()
        elif self.mode == 'declaration':
            return self.declaration()
        elif self.mode == 'format':
            return self.format()
        elif self.mode == 'types':
            return self.types()
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
    def __init__(self, *args, indexAccess=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.indexAccess = indexAccess
        self.prepare()
        #TODO Type may be dict, but with indexAccess type should be valType

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

    def expression(self):
        if self.indexAccess:
            if self.type.type == 'array':
                return f'list_{self.elementType.type}_get({self.name}, {indexAccess})'
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
        '**','*','%','/','-','+','==','!=','>','<','>=','<=',
        'is','in','andnot','and','or','&', '<<', '>>'
    ]
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
        elif op in ['==','!=','>','<','>=','<=','in','and','or']:
            t = Type('bool')
        return Expr(value=f'{arg1} {op} {arg2}', type=t)

    def __repr__(self):
        self.prepare()
        return repr(self.value)

    @property
    def index(self):
        if len(self.elements) == 1:
            return self.elements[0].index
        return super().index

class DotAccess():
    imports = []
    def __init__(self, chain=None, namespace=''):
        self.chain = chain
        self.chain[0].namespace = namespace
        self.type = chain[-1].type
        self.indexAccess = None

    def prepare(self):
        pass

    def __repr__(self):
        chain = [repr(self.chain[0])]
        currentType = self.chain[0].type
        for n, c in enumerate(self.chain[1:]):
            if currentType.isClass and isinstance(c, Call):
                chain[n-1] = currentType.type
                chain.append('_')
                chain.append(repr(c))
            elif currentType.isModule:
                chain[n-1] = ''
                chain.append(repr(c))
            else:
                chain.append('->')
                chain.append(repr(c))
            currentType = c.type
        return ''.join(chain)

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
    def __init__(self, *elements, type=None):
        self.elements = elements
        self.type = type
        self.prepare()

    def prepare(self):
        if self.type.known:
            self.imports = [
                f'#include "list_{self.type.elementType.type}.h"',
                '#include "asprintf.h"']
        else:
            self.imports = []

    def __repr__(self):
        self.prepare()
        size = 8 if (l:=len(self.elements)) < 8 else l
        if self.elements:
            return f'list_{self.type.elementType.type}_constructor({l}, {size}, ' + ','.join([repr(e) for e in self.elements])+')'
        return f'list_{self.type.elementType.type}_constructor({l}, {size})'

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
    def __init__(self, expr=None):
        self.expr = expr
        self.imports = ['#include "photonInput.h"']
        self.type = Type('str')

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
            return Sequence(self.sequence + sequence.sequence)
        raise ValueError(f'Object of type {type(sequence)} cannot be added to Sequence.')

    def __repr__(self):
        representation = ''
        for obj in self.sequence:
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
        }
    }

    def __init__(self, expr, castTo):
        if isinstance(expr, Cast):
            self.expr = expr.expr
        else:
            self.expr = expr
        self.castTo = castTo
        self.type = self.castTo

    def __repr__(self):
        print('Repr', self.expr)
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
            if castTo != castFrom:
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
    def __init__(self, args, mode=None):
        self.args = args
        self.mode = mode
    
    def __bool__(self):
        return True if repr(self) else False

    def __getitem__(self, index):
        return self.args[index]

    def __repr__(self):
        if self.mode is not None:
            # override mode
            for arg in self.args:
                arg.mode = self.mode
        return ', '.join([repr(arg) for arg in self.args])

class Kwargs():
    def __init__(self, kwargs, mode='expr'):
        self.kwargs = kwargs
        self.mode = mode

    def prepare(self):
        for kwarg in kwargs:
            kwarg.mode = self.mode
    
    def __bool__(self):
        return True if repr(self) else False

    def __repr__(self):
        return ', '.join([repr(kwarg) for kwarg in self.kwargs])

class Call(Obj):
    def __init__(self, name='', args='', kwargs='', **defaults):
        super().__init__(**defaults)
        self.name = name
        self.type = self.name.type
        self.args = Args(args)
        self.kwargs = Kwargs(kwargs)

    def __repr__(self):
        separator = ', ' if self.args and self.kwargs else ''
        if self.type.isClass:
            return f'{self.name}_new({self.args}{separator}{self.kwargs})'
        else:
            return f'{self.name}({self.args}{separator}{self.kwargs})'

class Function(Obj):
    def __init__(self, name='', args='', kwargs='', code='', **defaults):
        super().__init__(**defaults)
        self.name = name
        self.type = name.type
        self.args = Args(args, mode='declaration')
        self.kwargs = Kwargs(kwargs, mode='declaration')
        self.code = Scope(code)

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
    def __init__(self, name='', args='', code=''):
        self.name = name
        self.args = Args(args)
        self.code = Scope(code)
        self.type = Type(repr(self.name))
        self.parameters = {}
        self.methods = {}
        self.new = None
        for instruction in self.code:
            if isinstance(instruction, Assign):
                instruction.target.namespace = ''
                self.parameters[instruction.index] = instruction
            elif isinstance(instruction, Function):
                if instruction.name.value == 'new':
                    self.new = instruction
                instruction.name.value = f'{self.name.value}_{instruction.name.value}'
                self.methods[instruction.index] = instruction
        if self.new is None:
            self.new = Function(name=Var(f'{self.name.value}_new',namespace=self.name.namespace))
            self.methods[self.new.index] = self.new
        self.new.name.type = f'struct {self.name}*'
        #TODO Include new args here
        #instruction.args = Args(list(self.parameters.values()), mode='declaration')
        self.new.code = Scope([
            NativeCode(f'{self.type} self = malloc(sizeof({self.name}))'),
            *[NativeCode(f'self->{a.target} = {a.value}') for a in self.parameters.values()],
            *self.new.code,
            NativeCode(f'return self')
        ])

    def declarationMode(self):
        for t in self.code:
            t.mode = 'declaration'
    
    def writeMode(self):
        for t in self.code:
            t.mode = 'expr'

    def __repr__(self):
        self.declarationMode()
        value = f'typedef struct {self.name} {self.code} {self.name};\n'
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
