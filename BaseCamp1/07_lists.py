# 07_lists.py
# Lists - storing multiple items in one variable

# Creating lists
fruits = ["apple", "banana", "orange", "grape"]
numbers = [1, 2, 3, 4, 5]
mixed = ["hello", 42, 3.14, True]  # Lists can hold different types

print("Fruits:", fruits)
print("Numbers:", numbers)

# Accessing list items (indexing starts at 0)
print("First fruit:", fruits[0])    # apple
print("Last fruit:", fruits[-1])    # grape (negative indexing)
print("Second number:", numbers[1]) # 2

# List length
print("Number of fruits:", len(fruits))

# Adding items to lists
fruits.append("kiwi")  # Add to end
print("After adding kiwi:", fruits)

fruits.insert(1, "mango")  # Insert at position 1
print("After inserting mango:", fruits)

# Removing items
fruits.remove("banana")  # Remove first occurrence
print("After removing banana:", fruits)

last_fruit = fruits.pop()  # Remove and return last item
print("Removed:", last_fruit)
print("Remaining fruits:", fruits)

# Checking if item is in list
if "apple" in fruits:
    print("Apple is in the list!")

# Looping through lists
print("\nAll fruits:")
for fruit in fruits:
    print(f"I like {fruit}")

print("\nFruits with their positions:")
for i, fruit in enumerate(fruits):
    print(f"{i}: {fruit}")

# List slicing
numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
print("First 3 numbers:", numbers[:3])      # [0, 1, 2]
print("Last 3 numbers:", numbers[-3:])      # [7, 8, 9]
print("Middle numbers:", numbers[3:7])      # [3, 4, 5, 6]
print("Every other number:", numbers[::2])  # [0, 2, 4, 6, 8]