import os
import subprocess
from config import GET_FILE_CONTENT_MAX_CHARS as MAX_CHARS
from google.genai import types


def run_command(working_directory, command):
    try:
        working_dir_abs = os.path.abspath(working_directory)

        if not os.path.isdir(working_dir_abs):
            return f'Error: Working directory "{working_directory}" does not exist'

        result = subprocess.run(
            command,
            shell=True,
            cwd=working_dir_abs,
            capture_output=True,
            text=True,
            timeout=120,
        )

        output = ""
        if result.stdout:
            output += result.stdout
        if result.stderr:
            if output:
                output += "\n"
            output += "STDERR:\n" + result.stderr

        if not output:
            output = "Command executed successfully with no output."

        if len(output) > MAX_CHARS:
            output = output[:MAX_CHARS] + f"\n[...output truncated at {MAX_CHARS} characters]"

        if result.returncode != 0:
            output = f"Exit code: {result.returncode}\n{output}"

        return output.strip()

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 120 seconds."
    except Exception as e:
        return f"Error executing command: {e}"


schema_run_command = types.FunctionDeclaration(
    name="run_command",
    description="Executes a shell command and returns its output. Use this to run any command like grep, find, python, pip, cat, ls, etc. Supports pipes, redirects, and shell features.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "command": types.Schema(
                type=types.Type.STRING,
                description="The shell command to execute, e.g., 'grep -r \"def main\" .' or 'python test.py' or 'find . -name \"*.py\"'.",
            ),
        },
        required=["command"],
    ),
)
