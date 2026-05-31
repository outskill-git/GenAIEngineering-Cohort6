# 03_input_output.py
# Getting input from the user and displaying output

# Getting user input (input() always returns a string)
name = input("What's your name? ")
print("Nice to meet you, " + name + "!")

# Getting numbers from user input
age_text = input("How old are you? ")
age = int(age_text)  # Convert string to integer
print("You are", age, "years old")

# Shorter way to get and convert numbers
favorite_number = int(input("What's your favorite number? "))
doubled = favorite_number * 2
print("Your favorite number doubled is:", doubled)

# Different ways to format output
print("Hello", name, "you are", age, "years old")
print(f"Hello {name}, you are {age} years old")  # f-string (modern way)

# Getting decimal numbers
temperature = float(input("What's the temperature today? "))
print(f"It's {temperature} degrees today")