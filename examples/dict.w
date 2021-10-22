
# int:int my_dict = { 1:1, 2:4, 3:9, 4:16 }

int:int dict_int = {}
dict_int[1] = 1
dict_int[2] = 4
dict_int[3] = 9
dict_int[4] = 16

for i in 1..5:
    print("The key {i} contains the value {dict_int[i]}")
