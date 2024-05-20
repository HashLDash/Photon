class BaseType():
    nativeTypes = {
        'int':'int',
        'str':'str',
        'float':'float',
        'bool':'bool',
        'unknown':'unknown',
        '':'unknown',
        'obj':'obj',
        'file':'file',
    }

    def __init__(self, type, elementType=None, keyType=None, valType=None, returnType=None, funcName=None, argsTypes=None, name=None, namespace='', native=False, **kwargs):
        if isinstance(type, self.__class__):
            self.native = type.native
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
            self.native = native
            self.namespace = namespace
            self.type = type if type is not None else 'unknown'
            self.elementType = self.__class__(elementType) if self.isKnown(self.type) else 'unknown'
            self.keyType = self.__class__(keyType) if self.isKnown(self.type) else 'unknown'
            self.valType = self.__class__(valType) if self.isKnown(self.type) else 'unknown'
            self.returnType = self.__class__(returnType) if self.isKnown(self.type) else 'unknown'
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
        elif self.known and not self.native and not self.type in self.nativeTypes and self.type not in ['array', 'map', 'module'] and not 'func' in self.type.split(' '):
            return True
        else:
            return False

    def isKnown(self, type):
        if isinstance(type, self.__class__):
            return type.known
        if type not in ['unknown', '']:
            return True
        return False
    
    def __str__(self):
        return repr(self)

    def __repr__(self):
        raise NotImplemented

    def __hash__(self):
        return hash((self.type, self.elementType, self.keyType, self.valType))

    def __eq__(self, obj):
        return hash(obj) == self.__hash__()
