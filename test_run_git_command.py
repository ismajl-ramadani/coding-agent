import os
from functions.run_git_command import run_git_command

def main():
    test_dir = "."

    print("--- Testing git status ---")
    result1 = run_git_command(test_dir, ["status"])
    print(result1)
    print("\n")

    print("--- Testing git invalid command ---")
    result2 = run_git_command(test_dir, ["nonexistent-command"])
    print(result2)
    print("\n")

if __name__ == "__main__":
    main()
