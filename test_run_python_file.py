from functions.run_python_file import run_python_file

def main():
    print("--- Testing calculator usage (main.py without args) ---")
    print(run_python_file("calculator", "main.py"))
    print("\n")

    print("--- Testing calculator execution (main.py with args) ---")
    print(run_python_file("calculator", "main.py", ["3 + 5"]))
    print("\n")

    print("--- Testing calculator tests (tests.py) ---")
    print(run_python_file("calculator", "tests.py"))
    print("\n")

    print("--- Testing path traversal / outside directory ---")
    print(run_python_file("calculator", "../main.py"))
    print("\n")

    print("--- Testing non-existent file ---")
    print(run_python_file("calculator", "nonexistent.py"))
    print("\n")

    print("--- Testing non-Python file ---")
    print(run_python_file("calculator", "lorem.txt"))
    print("\n")

if __name__ == "__main__":
    main()