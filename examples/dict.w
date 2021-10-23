
# int:int my_dict = { 1:1, 2:4, 3:9, 4:16 }

int:int dict_int = {}
dict_int[1] = 1
dict_int[2] = 4
dict_int[3] = 9
dict_int[4] = 16

for i in 1..dict_int.len+1:
    print("The key {i} contains the value {dict_int[i]}")

int:str dict_str = {}
dict_str[1] = "1"
dict_str[2] = "4"
dict_str[3] = "9"
dict_str[4] = "16"

print(dict_str)
