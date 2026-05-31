# 05_conditionals.py
# Making decisions with if, elif, and else

# Basic if statement
age = int(input("How old are you? "))

if age >= 18:
    print("You are an adult!")
else:
    print("You are a minor.")

# Multiple conditions with elif
score = int(input("What's your test score? "))

if score >= 90:
    print("Grade: A")
elif score >= 80:
    print("Grade: B")
elif score >= 70:
    print("Grade: C")
elif score >= 60:
    print("Grade: D")
else:
    print("Grade: F")

# Comparison operators
x = 10
y = 5

print("x == y:", x == y)  # Equal to
print("x != y:", x != y)  # Not equal to
print("x > y:", x > y)    # Greater than
print("x < y:", x < y)    # Less than
print("x >= y:", x >= y)  # Greater than or equal
print("x <= y:", x <= y)  # Less than or equal

# Logical operators
temperature = 75
is_sunny = True

if temperature > 70 and is_sunny:
    print("Perfect weather for a picnic!")
elif temperature > 70 or is_sunny:
    print("Pretty good weather!")
else:
    print("Stay inside today.")

# Checking if something is in a range
number = int(input("Enter a number: "))
if 1 <= number <= 10:
    print("Number is between 1 and 10")
else:
    print("Number is outside the range 1-10")