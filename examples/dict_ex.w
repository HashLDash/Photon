
# The dictionary structure is a way of relating a key to a value.
# Where the pair (key:value) must have their respective types.

# Type examples for (key:value dictionary_name):
#   int:int `dictionary_name`
#   int:float `dictionary_name`
#   int:str `dictionary_name`

# Example of creating and assigning keys and values to the dictionary
#int:int my_dict = { 1:1, 2:4, 3:9, 4:16 }

int:int dict_int = {}
dict_int[1] = 1
dict_int[2] = 4
dict_int[3] = 9
dict_int[4] = 16

print("# Iterating by index")
# This structure only works if the key is a sequence of integers.
for i in 1..dict_int.len + 1:
    print("The key {i} contains the value {dict_int[i]}")

# Deletes an element from the dictionary using the entered key
del dict_int[2]

# Line break
print()

print("# Gets the key and value in each dictionary iteration")
for key, value in dict_int:
    print("The key {key} contains the value {value}")

# Line break
print()

int:str dict_str = {}
dict_str[1] = "P"
dict_str[2] = "H"
dict_str[3] = "O"
dict_str[4] = "T"
dict_str[5] = "O"
dict_str[6] = "N"

print(dict_str)
