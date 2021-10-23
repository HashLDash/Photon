
# list = [1,2,3,4]

str list_str = []
list_str += "P"
list_str += "h"
list_str += "o"
list_str += "t"
list_str += "o"
list_str += "n"

for i in 0..(list_str.len):
    print("The key {i} contains the value {list_str[i]}")

for n, letra in list_str:
    print('{n} {letra}')

for n, letra in "Photon":
    print('{n} {letra}')
