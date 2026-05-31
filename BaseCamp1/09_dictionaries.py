# 09_dictionaries.py
# Dictionaries - storing key-value pairs

# Creating dictionaries
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York",
    "job": "Engineer"
}

# Accessing values by key
print("Name:", person["name"])
print("Age:", person["age"])

# Safer way to access (won't crash if key doesn't exist)
print("Name:", person.get("name"))
print("Country:", person.get("country", "Unknown"))  # Default value

# Adding new key-value pairs
person["email"] = "alice@email.com"
person["hobby"] = "reading"

print("Updated person:", person)

# Modifying existing values
person["age"] = 31
print("New age:", person["age"])

# Checking if key exists
if "name" in person:
    print("Person has a name!")

# Getting all keys, values, or items
print("\nAll keys:", list(person.keys()))
print("All values:", list(person.values()))
print("All items:", list(person.items()))

# Looping through dictionaries
print("\nPerson details:")
for key, value in person.items():
    print(f"{key}: {value}")

# Dictionary of lists
grades = {
    "math": [85, 90, 88],
    "english": [92, 87, 95],
    "science": [78, 82, 85]
}

print("\nGrades:")
for subject, scores in grades.items():
    average = sum(scores) / len(scores)
    print(f"{subject}: {scores} (Average: {average:.1f})")

# List of dictionaries
students = [
    {"name": "Alice", "grade": 85},
    {"name": "Bob", "grade": 92},
    {"name": "Charlie", "grade": 78}
]

print("\nStudent grades:")
for student in students:
    print(f"{student['name']}: {student['grade']}")

# Nested dictionaries
school = {
    "name": "Central High",
    "classes": {
        "math": {"teacher": "Mr. Smith", "students": 25},
        "english": {"teacher": "Ms. Johnson", "students": 22}
    }
}

print("\nMath teacher:", school["classes"]["math"]["teacher"])