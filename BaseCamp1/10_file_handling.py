# 10_file_handling.py
# Reading from and writing to files

# Writing to a file
def write_to_file():
    # Create and write to a file
    with open("sample.txt", "w") as file:
        file.write("Hello, this is my first file!\n")
        file.write("Python makes file handling easy.\n")
        file.write("This is the third line.\n")

    print("File 'sample.txt' has been created!")

# Reading from a file
def read_entire_file():
    try:
        with open("sample.txt", "r") as file:
            content = file.read()
            print("File contents:")
            print(content)
    except FileNotFoundError:
        print("File not found! Make sure to run write_to_file() first.")

# Reading line by line
def read_line_by_line():
    try:
        with open("sample.txt", "r") as file:
            print("Reading line by line:")
            line_number = 1
            for line in file:
                print(f"Line {line_number}: {line.strip()}")
                line_number += 1
    except FileNotFoundError:
        print("File not found!")

# Appending to a file
def append_to_file():
    with open("sample.txt", "a") as file:
        file.write("This line was added later.\n")
        file.write("You can append multiple lines!\n")

    print("Text appended to file!")

# Working with CSV-like data
def write_student_data():
    students = [
        "Alice,85,Math",
        "Bob,92,Science",
        "Charlie,78,English"
    ]

    with open("students.txt", "w") as file:
        file.write("Name,Grade,Subject\n")  # Header
        for student in students:
            file.write(student + "\n")

    print("Student data written to 'students.txt'!")

def read_student_data():
    try:
        with open("students.txt", "r") as file:
            lines = file.readlines()
            print("Student data:")
            for line in lines:
                print(line.strip())
    except FileNotFoundError:
        print("Student file not found!")

# Example of processing file data
def analyze_student_data():
    try:
        with open("students.txt", "r") as file:
            lines = file.readlines()

            # Skip header line
            for line in lines[1:]:
                parts = line.strip().split(",")
                name = parts[0]
                grade = int(parts[1])
                subject = parts[2]

                if grade >= 90:
                    print(f"{name} got an A in {subject}!")
                elif grade >= 80:
                    print(f"{name} got a B in {subject}")
                else:
                    print(f"{name} needs improvement in {subject}")

    except FileNotFoundError:
        print("Student file not found!")
    except (ValueError, IndexError):
        print("Error reading file data!")

# Main function to demonstrate all file operations
def main():
    print("File Handling Demo")
    print("=" * 20)

    # Create a file
    write_to_file()

    # Read the file
    read_entire_file()

    # Read line by line
    read_line_by_line()

    # Append to file
    append_to_file()
    read_entire_file()

    # Work with structured data
    write_student_data()
    read_student_data()
    analyze_student_data()

if __name__ == "__main__":
    main()