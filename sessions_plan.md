# Session Management Implementation Plan

This document outlines the step-by-step plan to introduce session tracking and resumption to the AI coding agent. 

## 1. Directory Structure & Version Control
- **Hidden Folder**: Sessions will be stored in a `.sessions/` directory in the root of the project.
- **Git Ignore**: Add `.sessions/` to the `.gitignore` file to ensure personal conversation history isn't accidentally committed to version control.

## 2. Session ID Generation
- A session ID will be generated upon starting a new session. A timestamp-based approach is recommended for easy sorting, e.g., `session_YYYYMMDD_HHMMSS.json`.
- The current session ID will be held in a variable (e.g., `current_session_id`) to be used throughout the app's runtime.

## 3. Serialization and Deserialization
Since the `google.genai.types.Content` objects are essentially Pydantic models under the hood:
- **Saving (Serialization)**: Convert the `messages` list into a JSON-serializable list of dictionaries using `model_dump`:
  ```python
  import json
  serializable_messages = [msg.model_dump(exclude_none=True) for msg in messages]
  ```
- **Loading (Deserialization)**: Read the JSON file and reconstruct the `types.Content` objects using `**kwargs`:
  ```python
  import json
  from google.genai import types
  # load data from JSON...
  messages = [types.Content(**msg_data) for msg_data in data]
  ```

## 4. CLI Arguments Update
Add new arguments to the `argparse.ArgumentParser` in `main.py`:
- `--resume`: A boolean flag (`action="store_true"`). If passed, the app will scan the `.sessions/` directory, find the most recently created (or modified) `.json` file, and resume it.
- `--session-id`: A string parameter (e.g., `--session-id session_20231024_153022`). If passed, the app will look for exactly that file and resume it.

## 5. Main Application Logic
- **Initialization**: 
  - Ensure `.sessions/` exists: `os.makedirs(".sessions", exist_ok=True)`.
  - Check for `--resume` or `--session-id`. If specified, load the corresponding file, populate `messages`, and set `current_session_id`. Handle edge cases (e.g., no sessions exist or file not found).
  - If no resume flags are provided, generate a new timestamp-based `current_session_id` and initialize `messages = []`.
- **Saving State**:
  - Create a helper function `save_session(session_id, messages)`.
  - Call this function inside the `while True:` loop every time the `messages` array is updated:
    1. After appending the user's input.
    2. After appending the model's generated response candidate(s).
    3. After appending the function/tool execution results.

## 6. Implementation Checklist
- [x] Update `.gitignore`.
- [x] Create `session_manager.py` (optional, or just add the functions directly to `main.py`) with `save_session` and `load_session` helpers.
- [x] Update `main.py` CLI parser.
- [x] Implement the initialization logic in `main.py` to load previous sessions.
- [x] Add `save_session` hooks throughout the conversation loop in `main.py`.
- [x] Test new session creation, saving, and resumption.
- [x] Add the instructions for sessions to the readme