import os
from functions.patch_file import patch_file

def main():
    # Setup test file
    test_dir = "."
    test_file = "test_patch_dummy.txt"
    with open(test_file, "w", encoding="utf-8") as f:
        f.write("line 1\nline 2\nline 3\nline 2\nline 5")

    print("--- Testing exact match replace ---")
    result1 = patch_file(test_dir, test_file, "line 1\n", "line 1 modified\n")
    print(result1)

    print("\n--- Testing multiple matches without replace_all ---")
    result2 = patch_file(test_dir, test_file, "line 2", "line 2 changed")
    print(result2)

    print("\n--- Testing multiple matches with replace_all ---")
    result3 = patch_file(test_dir, test_file, "line 2", "line 2 changed", replace_all=True)
    print(result3)

    print("\n--- Testing not found ---")
    result4 = patch_file(test_dir, test_file, "line 100", "new line")
    print(result4)

    # Cleanup
    os.remove(test_file)

if __name__ == "__main__":
    main()
