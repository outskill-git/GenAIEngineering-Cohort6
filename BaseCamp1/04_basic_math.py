# 04_basic_math.py
# Basic mathematical operations in Python

# Basic arithmetic operators
a = 10
b = 3

print("Addition:", a + b)       # 13
print("Subtraction:", a - b)    # 7
print("Multiplication:", a * b) # 30
print("Division:", a / b)       # 3.333...
print("Integer division:", a // b) # 3 (rounds down)
print("Remainder:", a % b)      # 1 (modulo)
print("Power:", a ** b)         # 1000 (10 to the power of 3)

# Order of operations (PEMDAS)
result = 2 + 3 * 4
print("2 + 3 * 4 =", result)  # 14 (not 20!)

# Use parentheses to change order
result = (2 + 3) * 4
print("(2 + 3) * 4 =", result)  # 20

# Useful built-in functions
print("Absolute value of -5:", abs(-5))
print("Round 3.7:", round(3.7))
print("Maximum of 5, 8, 3:", max(5, 8, 3))
print("Minimum of 5, 8, 3:", min(5, 8, 3))

# Compound assignment operators
x = 5
x += 3  # Same as x = x + 3
print("x after += 3:", x)

x *= 2  # Same as x = x * 2
print("x after *= 2:", x)