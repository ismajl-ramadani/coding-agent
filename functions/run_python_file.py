import os
import subprocess
from google.genai import types

def run_python_file(working_directory, file_path, args=None):
    try:
        # 1. Safely resolve and normalize paths
        working_dir_abs = os.path.abspath(working_directory)
        target_file_abs = os.path.normpath(os.path.join(working_dir_abs, file_path))

        # 2. Check if the file is inside the permitted working directory
        valid_file_path = os.path.commonpath([working_dir_abs, target_file_abs]) == working_dir_abs

        if not valid_file_path:
            return f'Error: Cannot execute "{file_path}" as it is outside the permitted working directory'

        # 3. Check if it exists and is a regular file
        if not os.path.isfile(target_file_abs):
            return f'Error: "{file_path}" does not exist or is not a regular file'

        # 4. Enforce Python file extension
        if not target_file_abs.endswith('.py'):
            return f'Error: "{file_path}" is not a Python file'

        # 5. Build the command
        command = ["python", target_file_abs]
        if args:
            command.extend(args)

        # 6. Execute the process safely
        result = subprocess.run(
            command,
            cwd=working_dir_abs,
            capture_output=True,
            text=True,
            timeout=30
        )

        # 7. Format the output
        output_lines = []
        if result.returncode != 0:
            output_lines.append(f"Process exited with code {result.returncode}")

        if not result.stdout and not result.stderr:
            output_lines.append("No output produced")
        else:
            if result.stdout:
                output_lines.append(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                output_lines.append(f"STDERR:\n{result.stderr}")

        return "\n".join(output_lines)

    except Exception as e:
        return f"Error: executing Python file: {e}"
    
schema_run_python_file = types.FunctionDeclaration(
    name="run_python_file",
    description="Executes a Python file and returns its output (stdout and stderr).",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The relative path to the Python file to execute.",
            ),
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(
                    type=types.Type.STRING
                ),
                description="An optional list of command-line arguments to pass to the script.",
            ),
        },
        required=["file_path"],
    ),
)