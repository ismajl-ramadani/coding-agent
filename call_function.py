from google.genai import types
from functions.get_files_info import schema_get_files_info, get_files_info
from functions.get_file_content import schema_get_file_content, get_file_content
from functions.write_file import schema_write_file, write_file
from functions.patch_file import schema_patch_file, patch_file
from functions.run_git_command import schema_run_git_command, run_git_command
from functions.run_command import schema_run_command, run_command

available_functions = types.Tool(
    function_declarations=[
        schema_get_files_info,
        schema_get_file_content,
        schema_write_file,
        schema_patch_file,
        schema_run_git_command,
        schema_run_command
    ],
)

def call_function(function_call, verbose=False):
    if verbose:
        print(f"Calling function: {function_call.name}({function_call.args})")
    else:
        print(f" - Calling function: {function_call.name}")

    function_map = {
        "get_files_info": get_files_info,
        "get_file_content": get_file_content,
        "write_file": write_file,
        "patch_file": patch_file,
        "run_git_command": run_git_command,
        "run_command": run_command
    }
    function_name = function_call.name or ""

    if function_name not in function_map:
        return  types.Content(
            role="tool",
            parts=[
                types.Part.from_function_response(
                    name=function_name,
                    response={"error": f"Unknown function: {function_name}"},
                )
            ],
        )

    # Make a copy of the args and force our security constraint
    args = dict(function_call.args) if function_call.args else {}
    args["working_directory"] = "."

    function_result = function_map[function_name](**args)

    # Wrap the string result in the format the Google SDK expects to see later
    return types.Content(
        role="tool",
        parts=[
            types.Part.from_function_response(
                name=function_name,
                response={"result": function_result},
            )
        ],
    )
