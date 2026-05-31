# 06_loops.py
# Repeating code with for and while loops

# For loops - when you know how many times to repeat
print("Counting to 5:")
for i in range(5):  # 0, 1, 2, 3, 4
    print(i)

print("\nCountdown:")
for i in range(5, 0, -1):  # 5, 4, 3, 2, 1
    print(i)
print("Blast off!")

# Different range() patterns
print("\nNumbers 1 to 10:")
for num in range(1, 11):  # Start at 1, end before 11
    print(num, end=" ")
print()

print("\nEven numbers from 0 to 20:")
for num in range(0, 21, 2):  # Start at 0, end before 21, step by 2
    print(num, end=" ")
print()

# While loops - when you don't know exactly how many times
print("\nGuessing game:")
secret_number = 7
guess = 0

while guess != secret_number:
    guess = int(input("Guess the number (1-10): "))
    if guess < secret_number:
        print("Too low!")
    elif guess > secret_number:
        print("Too high!")
    else:
        print("Correct!")

# Using break and continue
print("\nNumbers 1-10, but skip 5:")
for i in range(1, 11):
    if i == 5:
        continue  # Skip the rest of this iteration
    print(i, end=" ")
print()

print("\nStopping at 7:")
for i in range(1, 11):
    if i == 7:
        break  # Exit the loop completely
    print(i, end=" ")
print()