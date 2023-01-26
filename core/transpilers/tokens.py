# Basic Types
from copy import deepcopy

class Type():
    nativeTypes = {
        'int':'long',
        'str':'char*',
        'float':'double',
        'bool':'int',
        'unknown':'auto',
        '':'auto',
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

    def isKnown(self, type):
        if type not in ['unknown', '']:
            return True
        return False
    
    def __repr__(self):
        if self.type == 'array':
            return f'list_{self.elementType}'
        elif self.type == 'map':
            return f'dict_{self.keyType}_{self.valType}'
        return self.nativeTypes[self.type] 

    def __hash__(self):
        return hash((self.type, self.elementType, self.keyType, self.valType))

    def __eq__(self, obj):
        return hash(obj) == self.__hash__()

class Obj():
    def __init__(self, value='', type='', namespace='namespace'):
        self.value = value
        self.type = Type(type)
        self.namespace = namespace

    def __repr__(self):
        return 'Obj'

class Num(Obj):
    def __repr__(self):
        return str(self.value)

class String(Obj):
    def __init__(self, **kwargs):
        print(kwargs)
        kwargs['type'] = 'str'
        print(kwargs)
        super().__init__(**kwargs)

    def __repr__(self):
        return self.value

class Var(Obj):
    def __repr__(self):
        if self.namespace:
            return f'{self.namespace}__{self.value}'
        return f'{self.value}'

    def __hash__(self):
        return hash(self.namespace+self.value)

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
        return repr(self.value)

class Array():
    def __init__(self, *elements, elementType=''):
        self.elements = elements
        self.elementType = elementType
        if not self.elementType:
            self.inferType()
        self.type = Type('array', elementType=self.elementType)

    def inferType(self):
        types = set()
        for element in self.elements:
            types.add(element.type)
        if len(types) == 1:
            self.elementType = element.type
        elif types == {Type('int'), Type('float')}:
            self.elementType = Type('float')
        else:
            self.elementType = Type('unknown')
        
    def __repr__(self):
        return f'{self.type}(' + ','.join([repr(e) for e in self.elements])+')'

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
    def __init__(self, *objs, terminator=';'):
        self.terminator = terminator
        self.sequence = list(objs)

    def add(self, obj):
        self.sequence.append(obj)

    def __repr__(self):
        representation = ''
        for obj in self.sequence:
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
        if self.target.type.known:
            self.type = self.target.type
        elif self.value.type.known:
            self.type = self.value.type
            self.target.type = self.type

        if self.type != self.value.type:
            #TODO: cast value
            print(f'cast {self.value.type} to {self.type}')
            pass

    def __repr__(self):
        if self.inMemory:
            return f'{self.target} = {self.value}'
        else:
            return f'{self.target.type} {self.target} = {self.value}'

class Args():
    def __init__(self, args, call=False):
        self.args = args
        print(type(self.args[0]))
        if not call:
            for arg in args:
                arg.namespace = ''
                self.args.append(arg)
    
    def __bool__(self):
        return True if repr(self) else False

    def __repr__(self):
        return ', '.join([repr(arg) for arg in self.args])

class Kwargs():
    def __init__(self, kwargs):
        self.kwargs = []
        for kwarg in kwargs:
            kwarg.target.namespace = ''
            self.kwargs.append(kwarg)
    
    def __bool__(self):
        return True if repr(self) else False

    def __repr__(self):
        return ', '.join([repr(kwarg) for kwarg in self.kwargs])

class Call():
    def __init__(self, name='', args='', kwargs=''):
        self.name = name
        self.args = Args(args, call=True)
        self.kwargs = Kwargs(kwargs)

    def __repr__(self):
        separator = ', ' if self.args and self.kwargs else ''
        return f'{self.name.value}({self.args}{separator}{self.kwargs})'

class Function():
    def __init__(self, name='', args='', kwargs='', code=''):
        self.name = name
        self.args = Args(args)
        self.kwargs = Kwargs(kwargs)
        self.code = Scope(code)

    def __repr__(self):
        separator = ', ' if self.args and self.kwargs else ''
        return f'{self.name.type} {self.name}({self.args}{separator}{self.kwargs}) {self.code}'

class Class():
    def __init__(self, name='', args='', code=''):
        self.name = name
        self.args = Args(args)
        self.code = Scope(code)
        for instruction in self.code:
            if isinstance(instruction, Assign):
                instruction.target.namespace = ''
            elif isinstance(instruction, Function):
                instruction.name.value = f'{self.name.value}_{instruction.name.value}'

    def __repr__(self):
        return f'typedef struct {self.name.value} {self.code} {self.name.value};'

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
