# Coding Agent

A lightweight Python-based AI coding assistant powered by Google's Gemini API, featuring local function calling (reading/writing files, executing scripts).

## Setup

1. **Install `uv`** (Python package manager):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. **Install dependencies**:
   ```bash
   uv sync
   ```

3. **Configure environment**:
   Update or create a `.env` file in the root directory with your Gemini API key:
   ```env
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

**Interactive Mode:**
Start the chat session and type your prompts.
```bash
uv run main.py
```

**Direct Prompt:**
Pass the prompt directly via the command line.
```bash
uv run main.py "list the files in this directory"
```

**Verbose Mode:**
See token usage, tool executions, and underlying system traces by adding the `--verbose` flag.
```bash
uv run main.py --verbose "write a simple hello world script"
```

**Sessions:**
The agent automatically saves conversation sessions in the `.sessions/` directory.

Resume the most recent session:
```bash
uv run main.py --resume
```

Resume a specific session by ID:
```bash
uv run main.py --session-id session_YYYYMMDD_HHMMSS
```