def inference(value):
    ''' Return the token and infer its properties '''

    try:
        float(value)
        return {'token':'num', 'value': value, 'type':'int'}
    except:
        try:
            print(float(value[0]))
            print('it is something??')
            return {'token':'value','type':'unknown','value':value}
        except:
            if value == 'True' or value == 'False':
                return {'token':'expr','type':'bool','args': [{'type':'bool','value':value.lower()}], 'ops':[] }
            elif value == 'null':
                return {'token':'expr','type':'null','args': [{'type':'null','value':'null'}], 'ops':[] }
            else:
                return {'token':'var', 'type':'unknown', 'name':value}

def comment(i, t):
    print('comment')
    return []

def string(i, t):
    ''' Return a string value token according to tokenList '''
    
    # Maybe there is a doubleQuote before, verify
    for n,token in enumerate(t):
        if token['token'] in {'singleQuote','doubleQuote'}:
            i = n
            break
    if t[i]['token'] == 'singleQuote':
        quote = "'"
        stringQuote = 'singleQuote'
    else:
        quote = '"'
        stringQuote = 'doubleQuote'
    s = ''
    n = 1
    for token in t[i+1:]:
        if token['token'] == stringQuote:
            break
        elif 'singleQuote' in token:
            s += '"\'"'
        elif 'doubleQuote' in token:
            s += "'\"'"
        elif token['token'] == 'var':
            s += token['name']
        elif 'num' in token:
            s += str(token['value'])
        elif 'operator' in token:
            s += token['operator']
        elif 'symbol' in token:
            s += token['symbol']
        elif 'type' in token:
            s += token['type']
        else:
            tok = token['token']
            if 'Statement' in tok:
                s += tok.replace('Statement', '')
            else:
                s += tok
        n += 1

    t[i] = {
        'token':'expr',
        'args':[{'token':'str', 'type':'str','value':f'{quote}{s}{quote}'}],
        'ops':[]
    }
    for _ in range(n):
        del t[i+1]
    return t

def var(i, t):
    return t

def arrayType(i, t):
    ''' 
    Return a type token according to signature.
    (var type) beginBlock num -> array
    '''
    if t[i]['token'] == 'var':
        elementType = t[i]['name']
    elif t[i]['token'] == 'type':
        elementType = t[i]['type']
    else:
        raise SyntaxError('Array type ok {t[i]["token"} not implemented.')

    arrayLen = t[i+2]['value']

    t[i] = {'token':'type', 'type':'array', 'elementType':elementType, 'len':arrayLen}

    del t[i+1] #beginBlock
    del t[i+1] #num
    return t

def typeDeclaration(i, t):
    varType = []
    last = ''
    name = ''
    elementType = ''
    arrayLen = ''
    keyType = ''
    valType = ''
    if t[i]['token'] in {'type', 'var'}:
        for n, tok in enumerate(t[i:]):
            if tok['token'] == 'type':
                if tok['type'] == 'array':
                    elementType = tok['elementType']
                    arrayLen = tok['len']
                elif tok['type'] == 'map':
                    keyType = tok['keyType']
                    valType = tok['valType']
                else:
                    varType.append(tok['type'])
            elif tok['token'] == 'var' and not last == 'var':
                name = tok['name']
                last = 'var'
            elif tok['token'] == 'var' and last == 'var':
                varType.append(name)
                name = tok['name']
                break
    if not name:
        raise SyntaxError('Type declaration error')
    t[i] = {'token':'var', 'name':name, 'type':' '.join(varType)} 
    if arrayLen:
        # It's an array, include len and elementType
        t[i]['type'] = 'array'
        t[i]['len'] = arrayLen
        t[i]['elementType'] = elementType
    elif valType:
        # It's a map, include keyType and valType
        t[i]['type'] = 'map'
        t[i]['keyType'] = keyType
        t[i]['valType'] = valType
    for _ in range(n):
        del t[i+1] # type and var types
    return t

def floatNumber(i, t):
    ''' Return a float number from the given tokenList '''

    try:
        t[i] = {
            'token':'floatNumber',
            'type':'float',
            'value': f"{t[i]['value']}.{t[i+2]['value']}"}
        del t[i+1] #dot
    except:
        t[i] = {
            'token':'floatNumber',
            'type':'float',
            'value': f"{t[i]['value']}."}

    del t[i+1] #dot or decimal
    return t

def convertToExpr(token):
    if token['token'] in {'num', 'floatNumber'}:
        if token['token'] == 'num':
            varType = 'int'
        else:
            varType = 'float'
        return {'token':'expr', 'type':varType, 'args':[token], 'ops':[]}
    elif token['token'] in {'var'}:
        return {'token':'expr', 'type':token['type'], 'args':[token], 'ops':[]}
    else:
        raise SyntaxError('Cant convert token to expr')

def expr(i, t):
    if t[i]['token'] in {'num', 'floatNumber', 'var'}:
        t[i] = convertToExpr(t[i])
    else:
        raise SyntaxError('Expression of token {t[i]["token"]} not implemented.')
    return t
        
def printFunc(i, t):
    ''' Return a printFunction token '''

    if t[i+2]['token'] == 'expr':
        t[i] = {'token':'printFunc', 'expr':t[i+2]}
    else:
        t[i] = {'token':'printFunc', 'expr':convertToExpr(t[i+2])}
    del t[i+1] # lparen
    del t[i+1] # expr
    del t[i+1] # rparen
    return t