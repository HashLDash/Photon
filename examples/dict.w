
# A dictionary can be described a double list
# Where a first list is responsible for storing the keys and
# the second list for storing the value associated with each key in the first list

# To create a dictionary it is necessary to inform the data type
# of the list of keys and the data type of the list of values
# The type of the list of keys:The type of the list of values
# Examples:
#   int:int `dictionary name`
#   int:float `dictionary name`
#   int:str `dictionary name`

# Example of creating and assigning keys and values ​​to the dictionary
#int:int my_dict = { 1:1, 2:4, 3:9, 4:16 }

int:int dict_int = {}
dict_int[1] = 1
dict_int[2] = 4
dict_int[3] = 9
dict_int[4] = 16

# Deletes an element from the dictionary using the entered key
#del dict_int[2]

# This structure only works if the list key is a sequence of integers
for i in 1..dict_int.len+1:
    print("The key {i} contains the value {dict_int[i]}")

# This structure does not work in the list-only dictionary
#for key, value in dict_int:
#   print("The key {key} contains the value {value}")

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
