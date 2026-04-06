from textual.app import ComposeResult
from textual import containers
from textual.widgets import Markdown, Static


class UserInput(containers.HorizontalGroup):
    def __init__(self, content: str) -> None:
        super().__init__()
        self._content = content

    def compose(self) -> ComposeResult:
        yield Static("❯ ", id="prompt-icon")
        yield Markdown(self._content, id="content")
