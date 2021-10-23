
list = [1,2,3,4]
print(list)

print()

str list_str = []
list_str += "P"
list_str += "h"
list_str += "o"
list_str += "t"
list_str += "o"
list_str += "n"

for i in 0..list_str.len:
    print("The key {i} contains the value {list_str[i]}")

print()

for key, value in list_str:
    print("The key {key} contains the value {value}")

print()

for index, caracter in "Photon":
    print('The {index + 1}st character of the string is: {caracter}')
