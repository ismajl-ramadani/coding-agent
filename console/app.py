import os
import argparse
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
from google import genai
from google.genai import types
from textual import on, work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll, VerticalGroup

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

    def compose(self) -> ComposeResult:
        yield Throbber()
        with VerticalScroll(id="conversation-scroll"):
            yield VerticalGroup(id="conversation-content")
        yield Prompt()

    def on_mount(self) -> None:
        self.query_one(Prompt).focus()
        if self.initial_prompt:
            self.handle_user_input(self.initial_prompt)

    @on(Prompt.Submitted)
    def on_prompt_submitted(self, event: Prompt.Submitted) -> None:
        self.handle_user_input(event.text)

    def handle_user_input(self, text: str) -> None:
        content = self.query_one("#conversation-content", VerticalGroup)
        content.mount(UserInput(text))
        self._agent_response = None
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
        self.messages.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
        save_session(self.session_id, self.messages)

        for iteration in range(50):
            generate_config = types.GenerateContentConfig(
                tools=[available_functions],
                system_instruction=system_prompt,
            )
            if config.IS_THINKING_MODEL:
                generate_config.thinking_config = types.ThinkingConfig(include_thoughts=True)

            response = self.client.models.generate_content(
                model=config.MODEL_ID,
                contents=self.messages,
                config=generate_config,
            )

            if response.candidates:
                for candidate in response.candidates:
                    # Show thinking if present
                    if candidate.content and candidate.content.parts:
                        for part in candidate.content.parts:
                            if hasattr(part, "thought") and part.thought and part.text:
                                self.call_from_thread(self.post_thought, part.text)
                            elif part.text and not getattr(part, "thought", False):
                                self.call_from_thread(self.post_response, part.text)

                    self.messages.append(candidate.content)
                save_session(self.session_id, self.messages)

            if response.function_calls:
                function_results = []

                for fc in response.function_calls:
                    tool_id = f"tool-{fc.name}-{iteration}"
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
                    if len(result_text) > 300:
                        result_text = result_text[:300] + "…"
                    self.call_from_thread(self.update_tool_status, tool_id, "completed", result_text)

                    function_results.append(function_call_result.parts[0])

                self.messages.append(types.Content(role="user", parts=function_results))
                save_session(self.session_id, self.messages)
                # Reset response widget for next iteration
                self._agent_response = None
            else:
                self.call_from_thread(self.set_busy, False)
                self.call_from_thread(self.scroll_to_bottom)
                break
        else:
            self.call_from_thread(self.post_response, "Error: Agent reached maximum iterations.")
            self.call_from_thread(self.set_busy, False)

    def post_response(self, text: str) -> None:
        content = self.query_one("#conversation-content", VerticalGroup)
        if self._agent_response is None:
            self._agent_response = AgentResponse(text)
            content.mount(self._agent_response)
        else:
            self.app.call_later(self._agent_response.append_fragment, text)
        self.scroll_to_bottom()

    def post_thought(self, text: str) -> None:
        content = self.query_one("#conversation-content", VerticalGroup)
        thought = AgentThought(text)
        content.mount(thought)
        self.scroll_to_bottom()

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
    parser.add_argument("--resume", action="store_true", help="Resume the latest session")
    parser.add_argument("--session-id", type=str, help="Resume a specific session ID")
    args = parser.parse_args()

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
