
# The `print` function allows displaying in the command line interface (CLI) a certain value
# informed in the argument.
print("Hi.")

# The `input` function allows to obtain a textual value informed in the command line
# interface (CLI), the function's return will always be a string.
name = input("What is your name? ")

# Displaying the string with the value 'Hello, ' along with the name given above.
# In the example below, the string interpolation technique is used to include the name value.
print("Hello, {name}")

# Displays a line break.
print()

# In this case, the input function's return is cast from string to integer
int a = input("Enter an integer: ")
# or float in this case
float b = input("Enter a number with decimal places: ")

# Displaying the sum result.
print("The sum of {a} + {b} = {a + b}")
