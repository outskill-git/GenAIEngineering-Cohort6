# 08_functions.py
# Functions - reusable blocks of code

# Basic function definition
def greet():
    print("Hello there!")
    print("How are you today?")

# Calling the function
greet()
greet()  # Can call it multiple times

# Function with parameters
def greet_person(name):
    print(f"Hello, {name}!")
    print(f"Nice to meet you, {name}!")

greet_person("Alice")
greet_person("Bob")

# Function with multiple parameters
def add_numbers(a, b):
    result = a + b
    print(f"{a} + {b} = {result}")

add_numbers(5, 3)
add_numbers(10, 20)

# Function that returns a value
def multiply(x, y):
    return x * y

result = multiply(4, 7)
print("4 × 7 =", result)

# Function with default parameters
def introduce(name, age=25):
    print(f"Hi, I'm {name} and I'm {age} years old")

introduce("Charlie")      # Uses default age of 25
introduce("Diana", 30)    # Uses provided age of 30

# Function that works with lists
def find_max(numbers):
    if not numbers:  # Check if list is empty
        return None

    maximum = numbers[0]
    for num in numbers:
        if num > maximum:
            maximum = num
    return maximum

my_numbers = [3, 7, 2, 9, 1, 8]
biggest = find_max(my_numbers)
print("Biggest number:", biggest)

# Function with multiple return values
def get_name_parts(full_name):
    parts = full_name.split()
    first_name = parts[0]
    last_name = parts[-1]
    return first_name, last_name

first, last = get_name_parts("John Smith")
print("First name:", first)
print("Last name:", last)

# Using functions to organize code
def main():
    print("Welcome to the calculator!")
    num1 = float(input("Enter first number: "))
    num2 = float(input("Enter second number: "))

    sum_result = add_numbers_return(num1, num2)
    product_result = multiply(num1, num2)

    print(f"Sum: {sum_result}")
    print(f"Product: {product_result}")

def add_numbers_return(a, b):
    return a + b

# Run the main function
if __name__ == "__main__":
    main()