import os
import argparse
import sys
import logging
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

log = logging.getLogger(__name__)

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, VerticalGroup
from textual.widgets import Static

import config
from prompts import system_prompt
from call_function import available_functions, call_function
from session_manager import get_new_session_id, get_latest_session_id, load_session, save_session

from console.widgets.throbber import Throbber
from console.widgets.agent_response import AgentResponse
from console.widgets.agent_thought import AgentThought
from console.widgets.tool_call import ToolCall
from console.widgets.user_input import UserInput
from console.widgets.prompt import Prompt

load_dotenv()

WELCOME_TEXT = """\n  [bold]Coding Agent[/bold]\n\n  Your AI-powered coding assistant.\n  Ask me anything about your codebase.\n\n  Type a message below to get started.\n"""


class AgentApp(App):
    CSS_PATH = "app.tcss"

    def __init__(self, client: genai.Client, messages: list, session_id: str, verbose: bool = False, initial_prompt: str | None = None):
        super().__init__()
        self.client = client
        self.messages = messages
        self.session_id = session_id
        self.verbose = verbose
        self.initial_prompt = initial_prompt
        self._agent_response: AgentResponse | None = None
        self._agent_thought: AgentThought | None = None
        self._tool_counter = 0

    def compose(self) -> ComposeResult:
        yield Throbber()
        with VerticalScroll(id="conversation-scroll"):
            yield VerticalGroup(id="conversation-content")
        yield Static(f"session {self.session_id}", id="session-bar")
        yield Prompt()

    def on_mount(self) -> None:
        log.info("App mounted, session=%s", self.session_id)
        if not self.messages:
            content = self.query_one("#conversation-content", VerticalGroup)
            content.mount(Static(WELCOME_TEXT, id="welcome"))
        self.query_one(Prompt).focus()
        if self.initial_prompt:
            log.info("Initial prompt provided: %s", self.initial_prompt[:80])
            self.handle_user_input(self.initial_prompt)

    @on(Prompt.Submitted)
    def on_prompt_submitted(self, event: Prompt.Submitted) -> None:
        self.handle_user_input(event.text)

    def handle_user_input(self, text: str) -> None:
        log.info("User input: %s", text[:100])
        content = self.query_one("#conversation-content", VerticalGroup)
        welcome = self.query("#welcome")
        for w in welcome:
            w.remove()
        content.mount(UserInput(text))
        self._agent_response = None
        self._agent_thought = None
        self.set_busy(True)
        self.run_agent_loop(text)

    def set_busy(self, busy: bool) -> None:
        throbber = self.query_one(Throbber)
        if busy:
            throbber.add_class("-busy")
        else:
            throbber.remove_class("-busy")

    @work(thread=True)
    def run_agent_loop(self, user_input: str) -> None:
        log.info("Agent loop started")
        self.messages.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
        save_session(self.session_id, self.messages)

        for iteration in range(50):
            log.info("--- Iteration %d ---", iteration)
            generate_config = types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt,
            )
            if config.IS_THINKING_MODEL:
                generate_config.thinking_config = types.ThinkingConfig(include_thoughts=True)

            # Stream the response chunk by chunk
            log.info("Calling generate_content_stream (model=%s)", config.MODEL_ID)
            try:
                stream = self.client.models.generate_content_stream(
                    model=config.MODEL_ID,
                    contents=self.messages,
                    config=generate_config,
                )
            except genai_errors.ClientError as e:
                log.error("API client error: %s", e)
                self.call_from_thread(self._show_error, str(e))
                self.call_from_thread(self._finish_turn)
                # Remove the user message we just added since it failed
                self.messages.pop()
                return
            except genai_errors.ServerError as e:
                log.error("API server error: %s", e)
                self.call_from_thread(self._show_error, f"Server error: {e}")
                self.call_from_thread(self._finish_turn)
                self.messages.pop()
                return
            log.info("Stream object received, iterating chunks...")

            all_parts: list = []
            function_calls = []
            chunk_count = 0

            try:
                for chunk in stream:
                    chunk_count += 1
                    if not chunk.candidates:
                        log.debug("Chunk %d: no candidates", chunk_count)
                        continue
                    for candidate in chunk.candidates:
                        if not candidate.content or not candidate.content.parts:
                            log.debug("Chunk %d: candidate with no content/parts", chunk_count)
                            continue
                        for part in candidate.content.parts:
                            all_parts.append(part)

                        if getattr(part, "thought", False) and part.text:
                            log.debug("Chunk %d: thought (%d chars)", chunk_count, len(part.text))
                            event = threading.Event()
                            self.call_from_thread(self._stream_thought_sync, part.text, event)
                            event.wait()
                        elif part.text and not getattr(part, "thought", False):
                            log.debug("Chunk %d: text (%d chars): %s", chunk_count, len(part.text), part.text[:60])
                            if self._agent_thought is not None:
                                self.call_from_thread(self._collapse_thought)
                                self._agent_thought = None
                            event = threading.Event()
                            self.call_from_thread(self._stream_response_sync, part.text, event)
                            event.wait()

                        if part.function_call:
                            log.info("Chunk %d: function_call=%s", chunk_count, part.function_call.name)
                            function_calls.append(part.function_call)
            except (genai_errors.ClientError, genai_errors.ServerError) as e:
                log.error("API error during streaming: %s", e)
                self.call_from_thread(self._show_error, str(e))
                self.call_from_thread(self._finish_turn)
                return

            log.info("Stream finished: %d chunks, %d parts, %d function_calls", chunk_count, len(all_parts), len(function_calls))

            # Save the accumulated response to message history
            if all_parts:
                self.messages.append(types.Content(role="model", parts=all_parts))
                save_session(self.session_id, self.messages)

            if function_calls:
                function_results = []

                for idx, fc in enumerate(function_calls):
                    self._tool_counter += 1
                    tool_id = f"tool-{self._tool_counter}"
                    log.info("Executing tool: %s (id=%s, args=%s)", fc.name, tool_id, dict(fc.args) if fc.args else {})
                    self.call_from_thread(self.post_tool_call, fc.name, "pending", tool_id)

                    function_call_result = call_function(fc, verbose=self.verbose)

                    if not function_call_result.parts:
                        raise ValueError("Function call result has no parts.")

                    func_response = function_call_result.parts[0].function_response
                    if func_response is None:
                        raise ValueError("Function call result has no function_response.")
                    if func_response.response is None:
                        raise ValueError("Function response has no response data.")

                    result_text = str(func_response.response.get("result", ""))
                    log.info("Tool %s completed (%d chars result)", fc.name, len(result_text))
                    if len(result_text) > 300:
                        result_text = result_text[:300] + "…"
                    self.call_from_thread(self.update_tool_status, tool_id, "completed", result_text)

                    function_results.append(function_call_result.parts[0])

                self.messages.append(types.Content(role="user", parts=function_results))
                save_session(self.session_id, self.messages)
                # Reset widgets for next iteration
                self._agent_response = None
                self._agent_thought = None
            else:
                log.info("No function calls, finishing turn")
                self.call_from_thread(self._finish_turn)
                break
        else:
            log.error("Max iterations reached")
            self.call_from_thread(self._stream_response, "Error: Agent reached maximum iterations.")
            self.call_from_thread(self._finish_turn)

    async def _stream_response(self, text: str) -> None:
        log.debug("_stream_response: new_widget=%s, fragment=%d chars", self._agent_response is None, len(text))
        content = self.query_one("#conversation-content", VerticalGroup)
        if self._agent_response is None:
            self._agent_response = AgentResponse()
            await content.mount(self._agent_response)
        await self._agent_response.append_fragment(text)

    def _show_error(self, message: str) -> None:
        import re
        # Extract a user-friendly message from API errors
        if "429" in message or "RESOURCE_EXHAUSTED" in message:
            retry_match = re.search(r"retry in (\S+)", message, re.IGNORECASE)
            retry_info = f" Retry in {retry_match.group(1)}." if retry_match else ""
            friendly = f"Rate limit exceeded.{retry_info}"
        elif "400" in message:
            friendly = "Bad request — the message may be too long or contain unsupported content."
        elif "403" in message:
            friendly = "Access denied — check your API key permissions."
        elif "500" in message or "ServerError" in message:
            friendly = "The API server returned an error. Try again in a moment."
        else:
            friendly = message[:200]
        content = self.query_one("#conversation-content", VerticalGroup)
        content.mount(Static(f"[bold red]Error:[/bold red] {friendly}", classes="error-msg"))
        self.call_after_refresh(self.scroll_to_bottom)

    def _stream_response_sync(self, text: str, event: threading.Event) -> None:
        async def _do() -> None:
            await self._stream_response(text)
            event.set()
        self.call_later(_do)

    async def _stream_thought(self, text: str) -> None:
        log.debug("_stream_thought: new_widget=%s, fragment=%d chars", self._agent_thought is None, len(text))
        content = self.query_one("#conversation-content", VerticalGroup)
        if self._agent_thought is None:
            self._agent_thought = AgentThought()
            await content.mount(self._agent_thought)
            log.debug("_stream_thought: widget mounted")
        self._agent_thought.append_text(text)
        self.call_after_refresh(self.scroll_to_bottom)

    def _stream_thought_sync(self, text: str, event: threading.Event) -> None:
        async def _do() -> None:
            await self._stream_thought(text)
            event.set()
        self.call_later(_do)

    def _finish_turn(self) -> None:
        if self._agent_thought is not None:
            self._agent_thought.collapse()
        self._agent_response = None
        self._agent_thought = None
        self.set_busy(False)
        self.scroll_to_bottom()

    def _collapse_thought(self) -> None:
        if self._agent_thought is not None:
            self._agent_thought.collapse()

    def post_tool_call(self, name: str, status: str, tool_id: str) -> None:
        content = self.query_one("#conversation-content", VerticalGroup)
        tc = ToolCall(name, status)
        tc.id = tool_id
        content.mount(tc)
        self.scroll_to_bottom()

    def update_tool_status(self, tool_id: str, status: str, result: str = "") -> None:
        try:
            tc = self.query_one(f"#{tool_id}", ToolCall)
            tc.update_status(status, result)
        except Exception:
            pass

    def scroll_to_bottom(self) -> None:
        scroll = self.query_one("#conversation-scroll", VerticalScroll)
        scroll.scroll_end(animate=False)


def run():
    load_dotenv()
    api_key = os.environ.get("GEMINI_API_KEY")
    if api_key is None:
        raise RuntimeError("GEMINI_API_KEY not found in environment variables.")

    parser = argparse.ArgumentParser(description="Coding Agent")
    parser.add_argument("user_prompt", type=str, nargs="?", default=None, help="User prompt")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging to console_debug.log")
    parser.add_argument("--resume", action="store_true", help="Resume the latest session")
    parser.add_argument("--session-id", type=str, help="Resume a specific session ID")
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(
            filename="console_debug.log",
            level=logging.DEBUG,
            format="%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
        )

    client = genai.Client(api_key=api_key)

    messages = []
    current_session_id = None

    if args.session_id:
        current_session_id = args.session_id
        try:
            messages = load_session(current_session_id)
        except FileNotFoundError:
            print(f"Error: Session {current_session_id} not found.")
            sys.exit(1)
    elif args.resume:
        current_session_id = get_latest_session_id()
        if current_session_id:
            messages = load_session(current_session_id)
        else:
            current_session_id = get_new_session_id()
    else:
        current_session_id = get_new_session_id()

    app = AgentApp(
        client=client,
        messages=messages,
        session_id=current_session_id,
        verbose=args.verbose,
        initial_prompt=args.user_prompt,
    )
    app.run()


if __name__ == "__main__":
    run()
