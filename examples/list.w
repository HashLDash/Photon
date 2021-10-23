
# The list starts with index 0
list = [1, 2, 3, 4]
print(list)

# Removing the second element from the list
del list[2]
print(list)

# Line break
print()

# A list of strings
str list_str = []

# Adding elements to the list
# At each call of `+=` a new element will be assigned to a new index
list_str += "P"
list_str += "h"
list_str += "o"
list_str += "t"
list_str += "o"
list_str += "n"

# Iterating a list through variable i
for i in 0..list_str.len:
    print("The key {i} contains the value {list_str[i]}")

# Line break
print()

# The foreach cycles through the list and returns a key-value pair
for key, value in list_str:
    print("The key {key} contains the value {value}")

# Line break
print()

# The foreach is also capable of traversing a string (list of characters)
for index, caracter in "Photon":
    print('The {index + 1}st character of the string is: {caracter}')

