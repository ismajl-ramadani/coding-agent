from functools import lru_cache
from time import monotonic
from typing import Callable

from rich.segment import Segment
from rich.style import Style as RichStyle

from textual.color import Color, Gradient
from textual.css.styles import RulesMap
from textual.strip import Strip
from textual.style import Style
from textual.visual import RenderOptions, Visual
from textual.widget import Widget


COLORS = [
    "#881177",
    "#aa3355",
    "#cc6666",
    "#ee9944",
    "#eedd00",
    "#99dd55",
    "#44dd88",
    "#22ccbb",
    "#00bbcc",
    "#0099cc",
    "#3366bb",
    "#663399",
    "#881177",
]


class ThrobberVisual(Visual):
    gradient = Gradient.from_colors(*[Color.parse(c) for c in COLORS])

    def __init__(self, character: str = "━", get_time: Callable[[], float] = monotonic):
        self.character = character
        self.get_time = get_time

    @lru_cache(maxsize=8)
    def make_segments(self, style: Style, width: int) -> list[Segment]:
        gradient = self.gradient
        background = style.rich_style.bgcolor
        character = self.character
        return [
            Segment(
                character,
                RichStyle.from_color(
                    gradient.get_rich_color((offset / width) % 1),
                    background,
                ),
            )
            for offset in range(width * 2)
        ]

    def render_strips(
        self, width: int, height: int | None, style: Style, options: RenderOptions
    ) -> list[Strip]:
        time = self.get_time()
        segments = self.make_segments(style, width)
        offset = width - int((time % 1.0) * width)
        segments = segments[offset : offset + width]
        return [Strip(segments, cell_length=width)]

    def get_optimal_width(self, rules: RulesMap, container_width: int) -> int:
        return container_width

    def get_height(self, rules: RulesMap, width: int) -> int:
        return 1


class Throbber(Widget):
    def on_mount(self) -> None:
        self.auto_refresh = 1 / 15

    def render(self) -> ThrobberVisual:
        return ThrobberVisual()
