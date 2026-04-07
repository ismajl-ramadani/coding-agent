from textual.containers import VerticalGroup
from textual.widgets import Collapsible, Static


class AgentThought(VerticalGroup, can_focus=False):
    def __init__(self) -> None:
        super().__init__()
        self._text = ""
        self._body = Static("", markup=False)

    def compose(self):
        self._collapsible = Collapsible(self._body, title="Thinking", collapsed=False)
        self._collapsible.can_focus = False
        yield self._collapsible

    def append_text(self, text: str) -> None:
        self._text += text
        self._body.update(self._text)

    def collapse(self) -> None:
        self._collapsible.collapsed = True
