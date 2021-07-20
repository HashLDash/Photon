
# Variables in the photon can be dynamically typed or have a specific fixed type.
#-----------------------------------------------------------------------------------------
# Every variable contains three elements. Type, Name and Value, by default in Photon
# the dynamically typed variables do not require the type to be informed.
# Because the type will be implicitly defined based on the informed (assigned) value.

#-----------------------------------------------------------------------------------------
# Dynamically typed variables
my_var = 1
my_var = 3.1415
my_var = "The name of this programming language is called Photon"

#-----------------------------------------------------------------------------------------
# Explicitly typed variables

# Number integer
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

# Array of integers
float array_float = []
# Append elements on array of floats
array_float += 1.1
array_float += 2.1
array_float += 3.1

# Array of strings
str array_str = []
# The addition of elements is still under development!
#array_str += "My name"
#array_str += "is Johann"
