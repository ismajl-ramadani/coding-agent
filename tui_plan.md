# Textual UI Implementation Plan

## 1. Overview
The goal is to build a highly interactive Terminal User Interface (TUI) for the existing Gemini-powered AI agent using the `textual` framework. This implementation will live in a new file (e.g., `tui.py`) to keep the existing `main.py` intact.

## 2. Dependencies
Since the project uses `uv` (indicated by `uv.lock`), we will add the `textual` framework to the dependencies:
```bash
uv add textual
```

## 3. UI Layout & Design
The interface will consist of the following components:
- **Header**: Displays the application name and current session ID.
- **Message Log (Chat History)**: A vertically scrolling container (`VerticalScroll`) displaying chat messages.
  - User messages will be right-aligned or styled distinctly.
  - Assistant responses will use the `Markdown` widget to natively render rich text (bold, lists, code blocks).
  - Tool execution events (e.g., "Calling function X") will be displayed as minor system messages to show the agent's thought process.
- **Input Area**: A text `Input` widget at the bottom for the user to type their prompts.
- **Footer**: Standard shortcuts (e.g., `Ctrl+C` to quit, `Tab` to switch focus).

## 4. Backend Integration & Concurrency
The current `main.py` interacts with `google.genai` synchronously. To prevent the UI from freezing during network calls or tool executions:
- We will use Textual's `@work(thread=True)` decorator to offload the AI processing loop (which handles generation and function calling) into a separate background thread.
- The background thread will communicate with the main UI thread via custom Textual `Message` objects (e.g., `ChatResponse`, `ToolCall`, `ChatComplete`).
- We will reuse `config.py`, `call_function.py`, `prompts.py`, and `session_manager.py` just like `main.py` does.

## 5. State Management
- **Session ID**: Will be initialized via `get_new_session_id()` or loaded via command-line arguments.
- **Messages**: The Gemini `messages` array will be maintained in the App state and persisted using `save_session()` exactly as done in `main.py`.

## 6. Implementation Steps
1. **Plan Setup**: Save this plan (Done).
2. **Install Textual**: Run `uv add textual`.
3. **Skeleton `tui.py`**: Create the basic TUI layout without backend integration.
4. **Chat Logic Wrapper**: Create an asynchronous or threaded wrapper around the `while` loop logic from `main.py` to yield UI updates.
5. **Connecting UI & Backend**: Trigger the worker when the user submits input, disable the input while generating, and append newly generated markdown messages to the container.
6. **Refinements**: Handle visual styling, scrolling to the bottom on new messages, and graceful exit.