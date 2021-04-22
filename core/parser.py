# Photon parser
# This script converts lines of photon code into tokens
# and also generates the struct of the code.
# This struct is used by the Engine to execute the code.

def var():
    pass

def parse():
    pass

def assembly():
    pass

# Load grammar
with open('grammar/generatedGrammar.py') as g:
    exec(g.read())
