import os
import subprocess
from google.genai import types

def run_git_command(working_directory, args):
    try:
        # Safely resolve the working directory
        working_dir_abs = os.path.abspath(working_directory)

        # Ensure args is a list
        if not isinstance(args, list):
            return "Error: args must be a list of strings."
            
        # Security: ensure we are only running git
        cmd = ["git"] + args

        # Execute the git command
        result = subprocess.run(
            cmd,
            cwd=working_dir_abs,
            capture_output=True,
            text=True,
            check=False
        )

        output = ""
        if result.stdout:
            output += result.stdout + "\n"
        if result.stderr:
            output += "STDERR:\n" + result.stderr + "\n"

        if result.returncode != 0:
            return f"Git command exited with code {result.returncode}.\nOutput:\n{output.strip()}"

        return output.strip() if output else "Command executed successfully with no output."

    except Exception as e:
        return f"Error executing git command: {e}"

schema_run_git_command = types.FunctionDeclaration(
    name="run_git_command",
    description="Executes a git command in the repository. Use this for version control operations like status, diff, add, and commit.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "args": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description="The arguments to pass to git, e.g., ['status'] or ['commit', '-m', 'message']. Do not include 'git' itself.",
            )
        },
        required=["args"],
    ),
)
