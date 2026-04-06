from textual import on
from textual.binding import Binding
from textual.app import ComposeResult
from textual.message import Message
from textual.widgets import TextArea, Label
from textual import containers


class PromptInput(TextArea):
    BINDINGS = [
        Binding("enter", "submit", "Send", priority=True),
        Binding("ctrl+j,shift+enter", "newline", "Newline"),
    ]

    def __init__(self) -> None:
        super().__init__(language=None)
        self.show_line_numbers = False

    def on_mount(self) -> None:
        self.highlight_cursor_line = False

    def action_submit(self) -> None:
        text = self.text.strip()
        if text:
            self.post_message(Prompt.Submitted(text))
            self.clear()

    def action_newline(self) -> None:
        self.insert("\n")


class Prompt(containers.HorizontalGroup):
    class Submitted(Message):
        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    def compose(self) -> ComposeResult:
        yield Label("❯ ", id="prompt-label")
        yield PromptInput()

    def focus(self, scroll_visible: bool = True):
        self.query_one(PromptInput).focus()
        return self
