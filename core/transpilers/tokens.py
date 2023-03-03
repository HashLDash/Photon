# Basic Types
from copy import deepcopy

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
    def __init__(self, type, elementType='', keyType='', valType=''):
        self.type = type if isinstance(type, str) else type.type
        self.elementType = elementType
        self.keyType = keyType
        self.valType = valType
        
        if self.type == 'array' and self.isKnown(self.elementType):
            self.known = True
        elif self.type == 'map' and self.isKnown(self.valType) and self.isKnown(self.keyType):
            self.known = True
        elif self.isKnown(self.type):
            self.known = True
        else:
            self.known = False
        if self.known and self.type in self.nativeTypes:
            self.isClass = False
        else:
            self.isClass = True

    def isKnown(self, type):
        if type not in ['unknown', '']:
            return True
        return False
    
    def __str__(self):
        return repr(self)

    def __repr__(self):
        if self.type == 'array':
            return f'list_{self.elementType}*'
        elif self.type == 'map':
            return f'dict_{self.keyType}_{self.valType}*'
        elif self.type in self.nativeTypes:
            return self.nativeTypes[self.type] 
        else:
            return f'{self.type}'

    def __hash__(self):
        return hash((self.type, self.elementType, self.keyType, self.valType))

    def __eq__(self, obj):
        return hash(obj) == self.__hash__()

class Obj():
    def __init__(self, value='', type='', namespace='namespace', mode='expr'):
        self.value = value
        self.type = Type(type)
        self.namespace = namespace
        self.mode = mode

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
        else:
            raise ValueError(f'Mode {self.mode} not implemented.')

    @property
    def index(self):
        return None

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
    def prepare(self):
        if self.namespace:
            self.name = f'{self.namespace}__{self.value}'
        else:
            self.name = self.value

    def declaration(self):
        return f'{self.type} {self.value}'

    def format(self):
        if self.type.type not in ['str','int','float']:
            call = repr(self.type).replace("*","")
            return f'{call}_str({self.name})'
        return self.name

    def expression(self):
        return self.name

    def __hash__(self):
        return hash(self.namespace+self.value)

    @property
    def index(self):
        return f'{self.namespace}__{self.value}'

class Expr(Obj):
    operatorOrder = [
        '**','*','%','/','-','+','==','!=','>','<','>=','<=',
        'is','in','andnot','and','or','&', '<<', '>>'
    ]
    #TODO: not is not implemented
    def __init__(self, *elements, ops=None, **kwargs):
        super().__init__(**kwargs)
        self.elements = elements
        self.ops = ops if ops else []
        if not self.value:
            self.process()

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
        self.value.mode = self.mode
        return repr(self.value)

    @property
    def index(self):
        if len(self.elements) == 1:
            return self.elements[0].index
        return super().index

class Array():
    def __init__(self, *elements, elementType=''):
        self.elements = elements
        self.elementType = elementType
        if not self.elementType:
            self.inferType()
            self.imports = [f'#include "list_{self.elementType}.h"']
        self.type = Type('array', elementType=self.elementType)

    def inferType(self):
        types = set()
        for element in self.elements:
            types.add(element.type.type)
        if len(types) == 1:
            self.elementType = element.type.type
        elif types == {Type('int'), Type('float')}:
            self.elementType = Type('float')
        else:
            self.elementType = Type('unknown')
        
    def __repr__(self):
        size = 8 if (l:=len(self.elements)) < 8 else self.len
        return f'list_{self.elementType}_constructor({l}, {size}, ' + ','.join([repr(e) for e in self.elements])+')'

class KeyVal():
    def __init__(self, key='', val=''):
        self.key = key
        self.val = val

    def __repr__(self):
        return f'{self.key}, {self.val}'

class Map():
    def __init__(self, *keyVals, keyType='', valType=''):
        self.keyVals = keyVals
        self.keyType = keyType
        self.valType = valType
        if not self.keyType or not self.valType:
            self.inferType()
        self.type = Type('map', keyType=self.keyType, valType=self.valType)

    def inferType(self):
        keyTypes = set()
        valTypes = set()
        for keyVal in self.keyVals:
            keyTypes.add(keyVal.key.type)
            valTypes.add(keyVal.val.type)
        if len(keyTypes) == 1:
            self.keyType = keyVal.key.type
        else:
            raise NotImplemented('Keys of different types not implemented yet')
        if len(valTypes) == 1:
            self.valType = keyVal.val.type
        else:
            raise NotImplemented('Vals of different types not implemented yet')
        
    def __repr__(self):
        return f'{self.type}(' + ','.join([repr(kv) for kv in self.keyVals])+')'

# Representation Types

class Sequence():
    def __init__(self, objs=None, terminator=';', apply=None):
        self.terminator = terminator
        self.sequence = [] if objs is None else objs
        self.apply = apply

    def add(self, obj):
        self.sequence.append(obj)

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

class Assign(Obj):
    def __init__(self, target='', inMemory=False, **kwargs):
        super().__init__(**kwargs)
        self.target = target
        self.inMemory = inMemory
        input(f'target type {self.target.type}')
        input(f'expr type {self.value.type}')
        if self.target.type.known:
            self.type = self.target.type
        elif self.value.type.known:
            self.type = self.value.type
            self.target.type = self.type

        if self.type != self.value.type:
            #TODO: cast value
            print(f'cast {self.value.type} to {self.type}')
            pass

    def declaration(self):
        return f'{self.target.type} {self.target}'

    def expression(self):
        if self.inMemory:
            return f'{self.target} = {self.value}'
        else:
            return f'{self.target.type} {self.target} = {self.value}'

    @property
    def index(self):
        return self.target.index

class Args():
    def __init__(self, args, mode='expr'):
        self.args = args
        self.mode = mode
    
    def __bool__(self):
        return True if repr(self) else False

    def __repr__(self):
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
            return f'{self.name}_new({self.args}{separator}{self.kwargs})'

class Function(Obj):
    def __init__(self, name='', args='', kwargs='', code='', **defaults):
        super().__init__(**defaults)
        self.name = name
        self.args = Args(args, mode='declaration')
        self.kwargs = Kwargs(kwargs, mode='declaration')
        self.code = Scope(code)

    def prepare(self):
        self.separator = ', ' if self.args and self.kwargs else ''

    def declaration(self):
        return f'{self.name.type} (*{self.name})({self.args}{self.separator}{self.kwargs})'

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
        for instruction in self.code:
            if isinstance(instruction, Assign):
                instruction.target.namespace = ''
                self.parameters[instruction.index] = instruction
            elif isinstance(instruction, Function):
                instruction.name.value = f'{self.name.value}_{instruction.name.value}'
                self.methods[instruction.index] = instruction

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
