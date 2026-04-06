from textual.reactive import var
from textual.widgets import Markdown
from textual.widgets.markdown import MarkdownStream


class AgentResponse(Markdown):
    def __init__(self, markdown: str | None = None) -> None:
        super().__init__(markdown)
        self._stream: MarkdownStream | None = None

    @property
    def stream(self) -> MarkdownStream:
        if self._stream is None:
            self._stream = self.get_stream(self)
        return self._stream

    async def append_fragment(self, fragment: str) -> None:
        self.loading = False
        await self.stream.write(fragment)
