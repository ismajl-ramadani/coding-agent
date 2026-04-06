import os
from google.genai import types

def write_file(working_directory, file_path, content):
    try:
        # 1. Safely resolve and normalize paths
        working_dir_abs = os.path.abspath(working_directory)
        target_file_abs = os.path.normpath(os.path.join(working_dir_abs, file_path))

        # 2. Check if the file is inside the permitted working directory
        valid_file_path = os.path.commonpath([working_dir_abs, target_file_abs]) == working_dir_abs

        if not valid_file_path:
            return f'Error: Cannot write to "{file_path}" as it is outside the permitted working directory'

        # 3. Check if the target path is already an existing directory
        if os.path.isdir(target_file_abs):
            return f'Error: Cannot write to "{file_path}" as it is a directory'

        # 4. Create necessary parent directories
        # os.path.dirname gets the folder path, os.makedirs creates it (and any missing parents)
        os.makedirs(os.path.dirname(target_file_abs), exist_ok=True)

        # 5. Write the content to the file
        with open(target_file_abs, "w", encoding="utf-8") as f:
            f.write(content)

        # 6. Return success message
        return f'Successfully wrote to "{file_path}" ({len(content)} characters written)'

    except Exception as e:
        return f"Error: {e}"
    
schema_write_file = types.FunctionDeclaration(
    name="write_file",
    description="Writes or overwrites a file with the specified content.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The relative path where the file should be written.",
            ),
            "content": types.Schema(
                type=types.Type.STRING,
                description="The text content to write to the file.",
            ),
        },
        required=["file_path", "content"],
    ),
)