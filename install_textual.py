import subprocess
import sys

def main():
    try:
        result = subprocess.run(["uv", "add", "textual"], capture_output=True, text=True, check=True)
        print("Success:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print("Error:")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()