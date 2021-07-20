
# Variables in the photon language can be inferred or explicitly typed.
#-----------------------------------------------------------------------------------------
# Every variable contains three elements. Type, Name and Value. By default, Photon
# tries to infer the type of the variable based on the assigned value.

#-----------------------------------------------------------------------------------------
# Type inference in action
my_int = 1
my_float = 3.1415
my_string = "The name of this programming language is called Photon"
my_int_array = [1,2,3]
my_float_array = [1,2,2.4,3.0]

#-----------------------------------------------------------------------------------------
# Explicitly typed variables

# Integer number
int number_int = 1

# Floating point number
float number_real = 3.1415

# String of characters
str text = "The name of this programming language is called Photon"

# Array of integers
int array_int = []
# Append elements on array of integers
array_int += 1
array_int += 2
array_int += 3

# Array of floats
float array_float = []
# Append elements on array of floats
array_float += 1.1
array_float += 2.1
array_float += 3.1

# Array of strings
str array_str = []
# The addition of string elements is still under development!
#array_str += "My name"
#array_str += "is Johann"
