import sys
import re
from itertools import product
from pprint import pprint

try:
    grammar = sys.argv[1]
except:
    print('Please, provide a grammar')
    exit()

def genRules(val):
    vals = [ i for i in re.split('(\W)', val) if not (i=='' or i==' ' or i=='\n') ]
    terms = []
    current = []
    inGroup = False
    for v in vals:
        if v == ')':
            terms.append(tuple(current))
            current = []
            inGroup = False
        elif v == '(':
            inGroup = True
        elif inGroup:
            current.append(v)
        else:
            terms.append((v,))
    return list(product(*terms))

def createGrammar(grammar):
    with open('generatedGrammar.py', 'w') as g:
        g.write('patterns = {\n')
        for feature, patterns in grammar.items():
            for pattern in patterns:
                g.write(f'  {pattern}: {feature},\n')
        g.write('}')

with open(grammar, 'r') as g:
    generated = {}
    inDefinition = ''
    patterns = []
    for l in g:
        if '=' in l:
            if patterns:
                generated[inDefinition] = list(patterns)
                patterns = []
            definition, val = l.split('=')
            inDefinition = definition.strip()
            patterns += genRules(val)
        elif l.strip().startswith('|'):
            patterns += genRules(l.strip()[1:])
    if patterns:
        generated[inDefinition] = list(patterns)
        patterns = []
    createGrammar(generated)
