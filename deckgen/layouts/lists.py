"""목록 양식. 카드를 두 열로 나눠 놓는다."""

import math
from collections.abc import Mapping, Sequence
from typing import ClassVar

from deckgen.fields import Field, TextField, TextListField
from deckgen.layouts.base import TONE_FIELD, Layout, plain
from deckgen.painter import CONTENT_W, MARGIN_X, Para, Run, SlidePainter
from deckgen.theme import blend

_COLUMN_GAP = 0.4


def _column_width() -> float:
    return (CONTENT_W - _COLUMN_GAP) / 2


def _split_columns(items: Sequence[str]) -> list[tuple[int, int, str]]:
    """(열 번호, 열 안 줄 번호, 항목) 목록. 앞 열을 먼저 채운다."""
    per_column = math.ceil(len(items) / 2)
    return [(index // per_column, index % per_column, item) for index, item in enumerate(items)]


class ChecklistLayout(Layout):
    name: ClassVar[str] = "checklist"
    summary: ClassVar[str] = "확인 항목 카드 (체크 표시, 두 열) 와 하단 주의 문구"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="title", label="제목", max_chars=40, example_text="고쳐졌는지 확인하는 항목"),
        TextListField(name="items", label="항목", min_items=2, max_items=6, max_chars=40, example_items=("첫 번째 확인", "두 번째 확인", "세 번째 확인")),
        TextField(name="note", label="하단 주의", required=False, max_chars=110, example_text="반드시 새 환경에서 확인하세요."),
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        painter.title(str(data["title"]), MARGIN_X, 0.45, CONTENT_W, 0.9, 34, palette.primary)
        items: Sequence[str] = data["items"]  # type: ignore[assignment]
        width = _column_width()
        rows = math.ceil(len(items) / 2)
        for index, item in enumerate(items):
            x = MARGIN_X + (index % 2) * (width + _COLUMN_GAP)
            y = 1.75 + (index // 2) * 1.35
            painter.card(x, y, width, 1.2, palette.surface, f"확인 카드 {index + 1}")
            painter.symbol_circle(x + 0.3, y + 0.3, 0.6, "✓", palette.ok, 22, f"확인 표시 {index + 1}")
            painter.text(plain(item, 18, palette.ink), x + 1.15, y, width - 1.4, 1.2, f"확인 문구 {index + 1}", anchor="middle")
        note = str(data.get("note", ""))
        if note:
            painter.text([Para((Run(note, 16, palette.warn, bold=True),))], MARGIN_X, 1.75 + rows * 1.35 + 0.1, CONTENT_W, 0.6, "주의", anchor="middle")


class NumberedListLayout(Layout):
    name: ClassVar[str] = "numbered_list"
    summary: ClassVar[str] = "번호 카드 목록 (두 열). 번호 원과 경고 문구는 선택"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="badge", label="번호 원", required=False, max_chars=3, example_text="5"),
        TextField(name="title", label="제목", max_chars=40, example_text="STEP 5  다시 만들기"),
        TextField(name="warning", label="경고 문구", required=False, max_chars=110, example_text="되돌릴 수 없습니다. 먼저 알리고 진행하세요."),
        TextListField(
            name="items",
            label="항목",
            min_items=2,
            max_items=8,
            max_chars=60,
            example_items=("설정 저장", "사본 확인", "새로 만들기", "복원", "검증"),
        ),
        TONE_FIELD,
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        badge = str(data.get("badge", ""))
        title_x = {True: 1.7, False: MARGIN_X}[bool(badge)]
        if badge:
            painter.badge(badge, str(data.get("tone", "normal")))
        painter.title(str(data["title"]), title_x, 0.45, CONTENT_W + MARGIN_X - title_x, 0.9, 34, palette.primary)
        warning = str(data.get("warning", ""))
        if warning:
            painter.text([Para((Run(warning, 18, palette.warn, bold=True),))], MARGIN_X, 1.55, CONTENT_W, 0.5, "경고", anchor="middle")
        top = {True: 2.3, False: 1.8}[bool(warning)]
        width = _column_width()
        for number, (column, row, item) in enumerate(_split_columns(data["items"]), start=1):  # type: ignore[arg-type]
            x = MARGIN_X + column * (width + _COLUMN_GAP)
            y = top + row * 1.0
            painter.card(x, y, width, 0.85, palette.surface, f"항목 {number}")
            painter.numbered_circle(x + 0.2, y + 0.18, 0.5, str(number), palette.accent, palette.paper, 16, f"항목 번호 {number}")
            painter.text(plain(item, 15, palette.ink), x + 0.9, y, width - 1.1, 0.85, f"항목 문구 {number}", anchor="middle")


class ProhibitionsLayout(Layout):
    name: ClassVar[str] = "prohibitions"
    summary: ClassVar[str] = "하지 말 것 카드 (붉은 표시, 두 열)"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="title", label="제목", max_chars=40, example_text="하지 말 것"),
        TextListField(
            name="items",
            label="항목",
            min_items=2,
            max_items=8,
            max_chars=60,
            example_items=("백업 전에 지우지 않는다", "오류가 나면 멈춘다"),
        ),
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        painter.title(str(data["title"]), MARGIN_X, 0.45, CONTENT_W, 0.9, 34, palette.primary)
        width = _column_width()
        tint = blend(palette.danger, palette.paper, 0.10)
        for number, (column, row, item) in enumerate(_split_columns(data["items"]), start=1):  # type: ignore[arg-type]
            x = MARGIN_X + column * (width + _COLUMN_GAP)
            y = 1.7 + row * 1.2
            painter.card(x, y, width, 1.0, tint, f"금지 {number}")
            painter.symbol_circle(x + 0.2, y + 0.25, 0.5, "✕", palette.danger, 18, f"금지 표시 {number}")
            painter.text(plain(item, 15, palette.ink), x + 0.9, y, width - 1.1, 1.0, f"금지 문구 {number}", anchor="middle")
