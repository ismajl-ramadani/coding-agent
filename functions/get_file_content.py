import os
from config import GET_FILE_CONTENT_MAX_CHARS as MAX_CHARS
from google.genai import types

def get_file_content(working_directory, file_path):
    try:
        # 1. Safely resolve and normalize paths
        working_dir_abs = os.path.abspath(working_directory)
        target_file_abs = os.path.normpath(os.path.join(working_dir_abs, file_path))

        # 2. Check if the file is inside the permitted working directory
        valid_file_path = os.path.commonpath([working_dir_abs, target_file_abs]) == working_dir_abs

        if not valid_file_path:
            return f'Error: Cannot read "{file_path}" as it is outside the permitted working directory'

        # 3. Check if it actually exists and is a file
        if not os.path.isfile(target_file_abs):
            return f'Error: File not found or is not a regular file: "{file_path}"'

        # 4. Read the file with truncation logic
        with open(target_file_abs, "r", encoding="utf-8") as f:
            content = f.read(MAX_CHARS)
            
            # If we can read 1 more character, the file is longer than MAX_CHARS
            if f.read(1):
                content += f'[...File "{file_path}" truncated at {MAX_CHARS} characters]'

        return content

    except Exception as e:
        return f"Error: {e}"
    
schema_get_file_content = types.FunctionDeclaration(
    name="get_file_content",
    description="Reads the contents of a file up to a maximum character limit.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The relative path to the file to read.",
            ),
        },
        required=["file_path"],
    ),
)