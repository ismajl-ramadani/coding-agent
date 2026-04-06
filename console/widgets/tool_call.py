from textual import on, events
from textual.app import ComposeResult
from textual.content import Content
from textual.reactive import var
from textual import containers
from textual.widgets import Static


class ToolCallHeader(Static):
    pass


class ToolCall(containers.VerticalGroup):
    expanded: var[bool] = var(False, toggle_class="-expanded")

    def __init__(self, name: str, status: str = "pending", result: str = "") -> None:
        super().__init__()
        self.tool_name = name
        self.tool_status = status
        self.tool_result = result

    def compose(self) -> ComposeResult:
        yield ToolCallHeader(self._header_content, markup=False)
        if self.tool_result:
            yield Static(self.tool_result, id="tool-content", markup=False)

    @property
    def _header_content(self) -> Content:
        if self.expanded:
            icon = Content.styled("▼ ", "dim")
        else:
            icon = Content.styled("▶ ", "dim")

        header = Content.assemble(icon, Content.styled("Tool ", "bold"), self.tool_name)

        if self.tool_status == "pending":
            header += Content.assemble(" ⌛")
        elif self.tool_status == "completed":
            header += Content.styled(" ✔", "green")
        elif self.tool_status == "failed":
            header += Content.styled(" ✘ failed", "red")

        return header

    def update_status(self, status: str, result: str = "") -> None:
        self.tool_status = status
        self.tool_result = result
        self.query_one(ToolCallHeader).update(self._header_content)
        if result and not self.expanded:
            self.expanded = True

    @on(events.Click, "ToolCallHeader")
    def on_click_header(self, event: events.Click) -> None:
        event.stop()
        if self.tool_result:
            self.expanded = not self.expanded
            self.query_one(ToolCallHeader).update(self._header_content)
