import os
from google.genai import types

def patch_file(working_directory, file_path, search_string, replace_string, replace_all=False):
    try:
        # Safely resolve and normalize paths
        working_dir_abs = os.path.abspath(working_directory)
        target_file_abs = os.path.normpath(os.path.join(working_dir_abs, file_path))

        # Check if the file is inside the permitted working directory
        valid_file_path = os.path.commonpath([working_dir_abs, target_file_abs]) == working_dir_abs

        if not valid_file_path:
            return f'Error: Cannot access "{file_path}" as it is outside the permitted working directory'

        if not os.path.isfile(target_file_abs):
            return f'Error: "{file_path}" does not exist or is not a file.'

        with open(target_file_abs, "r", encoding="utf-8") as f:
            content = f.read()

        if search_string not in content:
            return f'Error: The search string was not found in "{file_path}". Make sure it matches exactly, including whitespace.'

        count = content.count(search_string)
        
        if count > 1 and not replace_all:
            return (f'Error: The search string was found {count} times. '
                    f'Set replace_all=True to replace all occurrences, or provide more surrounding context '
                    f'to make the search string unique.')

        if replace_all:
            new_content = content.replace(search_string, replace_string)
        else:
            new_content = content.replace(search_string, replace_string, 1)

        with open(target_file_abs, "w", encoding="utf-8") as f:
            f.write(new_content)

        return f'Successfully patched "{file_path}". Replaced {count if replace_all else 1} occurrence(s).'

    except Exception as e:
        return f"Error: {e}"

schema_patch_file = types.FunctionDeclaration(
    name="patch_file",
    description="Replaces a specific string in a file with a new string. Use this to modify existing files without rewriting them completely.",
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "file_path": types.Schema(
                type=types.Type.STRING,
                description="The relative path to the file to modify.",
            ),
            "search_string": types.Schema(
                type=types.Type.STRING,
                description="The exact text to find and replace. Include surrounding context if necessary to ensure uniqueness.",
            ),
            "replace_string": types.Schema(
                type=types.Type.STRING,
                description="The new text to replace the search string with.",
            ),
            "replace_all": types.Schema(
                type=types.Type.BOOLEAN,
                description="If true, replaces all occurrences. If false, fails if there are multiple matches.",
            ),
        },
        required=["file_path", "search_string", "replace_string"],
    ),
)
