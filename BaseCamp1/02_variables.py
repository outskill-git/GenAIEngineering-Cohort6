# 02_variables.py
# Variables are like boxes that store information

# Creating variables (no need to declare types!)
name = "Alice"          # String (text)
age = 25               # Integer (whole number)
height = 5.6           # Float (decimal number)
is_student = True      # Boolean (True or False)

# Using variables
print("Name:", name)
print("Age:", age)
print("Height:", height, "feet")
print("Is student:", is_student)

# Variables can change
age = 26
print("New age:", age)

# You can use variables in calculations
birth_year = 2025 - age
print("Birth year:", birth_year)

# Combining strings (concatenation)
greeting = "Hello, " + name + "!"
print(greeting)