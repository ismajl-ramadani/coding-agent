from functions.get_file_content import get_file_content

def main():
    print("--- Testing Truncation (lorem.txt) ---")
    lorem_output = get_file_content("calculator", "lorem.txt")
    print(f"Length of returned string: {len(lorem_output)}")
    print(f"Ending text:\n{lorem_output[-100:]}\n")

    print("--- Testing valid file (main.py) ---")
    print(get_file_content("calculator", "main.py"))
    print("\n")

    print("--- Testing valid file in subfolder (pkg/calculator.py) ---")
    print(get_file_content("calculator", "pkg/calculator.py"))
    print("\n")

    print("--- Testing path traversal / outside directory (/bin/cat) ---")
    # This should trigger outside directory error
    print(get_file_content("calculator", "/bin/cat"))
    print("\n")

    print("--- Testing non-existent file (pkg/does_not_exist.py) ---")
    # This should trigger file not found error
    print(get_file_content("calculator", "pkg/does_not_exist.py"))
    print("\n")

if __name__ == "__main__":
    main()