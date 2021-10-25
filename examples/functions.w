
# Functions are made up of parameters and a return value type.
# Data types that can be used to define parameters/return: int, float, str...
# Every function has def `return type` `function name` (`parameter type and name, next parameter`)

def int add(int x, int y):
    return x + y

def float sub(float x, float y):
    return x - y

def example(int a = 0, int b = 0):
    print("A = {a} | B = {b}")

def add_list(int list = []):
    int sum = 0
    for num in list:
        sum += num
    return sum

print("Add 3 + 1 = {add(3, 1)}")

# Line break
print()

print("Sub 5 - 2.1 = {sub(5, 2.1)}")

# Line break
print()

# Line break
example()
# You must specify the name of each argument that has a default value,
# otherwise the entered value will be ignored and the default value applied.
example(1, 2) # Don't do like that
example(a = 1, b = 2) # Do like this
example(b = 1, a = 2) # Do like this

# Line break
print()

int list = [1, 2, 3]

print("Add [1, 2, 3] = {add_list(list=list)}")

# Line break
#print()

#def test(cb callback):
#   print(callback(1, 2))

#test(add)
