
class Person():

    def new(.name = "Matheus", .age = 23, .gen = "1"):

    def print_name():
        print("My name is {.name}")

    def print_age():
        print("My age is {.age} years old")

    def print_gen():
        if .gen == "1" or .gen == "Man":
            .gen = "Man"
        elif .gen == "0" or .gen == "Woman":
            .gen = "Woman"
        else:
            .gen = "Undefined"
        print("I am a {.gen}")

person = Person()
person.print_name()
person.print_age()
person.print_gen()

print()

person = Person(age=30)
person.name = "William"
person.print_name()
person.print_age()
