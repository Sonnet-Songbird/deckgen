"""표지, 소개 카드, 흐름도, 마무리처럼 단계 상자 없이 쓰는 양식."""

from collections.abc import Mapping, Sequence
from typing import ClassVar

from deckgen.fields import BoolField, Field, IntField, ObjectListField, TextField, TextListField
from deckgen.layouts.base import Layout, caption_field, plain
from deckgen.metrics import count_lines, lines_height_in
from deckgen.painter import CONTENT_W, MARGIN_X, Para, Run, SlidePainter, slot_runs
from deckgen.theme import blend

_TONE_NORMAL = "normal"


def _caption_paragraph(painter: SlidePainter, item: Mapping[str, object], normal_size: float, warn_size: float) -> Para:
    palette = painter.theme.palette
    warn = str(item.get("tone", _TONE_NORMAL)) == "warn"
    color = {True: palette.warn, False: palette.ink}[warn]
    size = {True: warn_size, False: normal_size}[warn]
    return Para(slot_runs(str(item["text"]), size, color, palette.danger, bold=warn))


class TitleLayout(Layout):
    name: ClassVar[str] = "title"
    summary: ClassVar[str] = "표지 (어두운 배경, 큰 제목과 부제)"
    dark: ClassVar[bool] = True
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="title", label="제목", max_chars=34, example_text="발표 제목"),
        TextField(name="subtitle", label="부제", required=False, max_chars=120, multiline=True, example_text="부제 또는 한 줄 설명"),
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        painter.title(str(data["title"]), MARGIN_X, 1.9, CONTENT_W, 1.8, 48, palette.paper, anchor="bottom")
        subtitle = str(data.get("subtitle", ""))
        if subtitle:
            painter.text(plain(subtitle, 22, palette.surface), MARGIN_X, 3.9, CONTENT_W, 1.2, "부제")


class IntroCardsLayout(Layout):
    name: ClassVar[str] = "intro_cards"
    summary: ClassVar[str] = "번호 카드 2~4장과 아래 보조 문구 (시작 전 안내, 핵심 요약)"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="title", label="제목", max_chars=40, example_text="시작하기 전에 3가지"),
        ObjectListField(
            name="cards",
            label="카드",
            min_items=2,
            max_items=4,
            item_fields=(TextField(name="text", label="내용", max_chars=60, multiline=True, example_text="내용을 입력하세요"),),
            example_items=({"text": "첫 번째 안내"}, {"text": "두 번째 안내"}, {"text": "세 번째 안내"}),
        ),
        caption_field("footnotes", "보조 문구", 3),
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        painter.title(str(data["title"]), MARGIN_X, 0.45, CONTENT_W, 0.9, 34, palette.primary)
        cards: Sequence[Mapping[str, object]] = data["cards"]  # type: ignore[assignment]
        gap = 0.35
        width = (CONTENT_W - (len(cards) - 1) * gap) / len(cards)
        for index, card in enumerate(cards):
            x = MARGIN_X + index * (width + gap)
            painter.card(x, 1.7, width, 3.0, palette.surface, f"카드 {index + 1}", radius=0.1)
            painter.numbered_circle(x + 0.35, 1.95, 0.8, str(index + 1), palette.accent, palette.paper, 26, f"카드 번호 {index + 1}")
            painter.text(plain(str(card["text"]), 20, palette.ink), x + 0.35, 2.95, width - 0.7, 1.6, f"카드 내용 {index + 1}")
        notes: Sequence[Mapping[str, object]] = data.get("footnotes", [])  # type: ignore[assignment]
        y = 4.95
        for index, note in enumerate(notes):
            paragraph = _caption_paragraph(painter, note, 16, 16)
            height = max(0.5, lines_height_in(count_lines(paragraph.text, 16, CONTENT_W, bold=paragraph.runs[0].bold), 16) + 0.1)
            painter.text([paragraph], MARGIN_X, y, CONTENT_W, height, f"보조 문구 {index + 1}", anchor="middle")
            y += height + 0.1
        painter.warn_if_below(y, 7.0, "보조 문구가 슬라이드 아래쪽을 넘칩니다. 문구를 줄이세요")


class FlowLayout(Layout):
    name: ClassVar[str] = "flow"
    summary: ClassVar[str] = "단계 상자를 화살표로 잇는 전체 순서도 (마지막 상자 강조 가능)"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="title", label="제목", max_chars=40, example_text="전체 순서"),
        ObjectListField(
            name="steps",
            label="단계",
            min_items=2,
            max_items=7,
            item_fields=(TextField(name="label", label="이름", max_chars=8, example_text="확인"),),
            example_items=({"label": "확인"}, {"label": "조치"}, {"label": "검증"}),
        ),
        TextField(name="tag", label="번호 앞말", required=False, max_chars=8, example_text="STEP"),
        IntField(name="start", label="시작 번호", required=False, minimum=0, maximum=99, default=0),
        BoolField(name="highlight_last", label="마지막 단계 강조", required=False, default=False),
        caption_field("captions", "아래 문구", 3),
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        painter.title(str(data["title"]), MARGIN_X, 0.45, CONTENT_W, 0.9, 34, palette.primary)
        steps: Sequence[Mapping[str, object]] = data["steps"]  # type: ignore[assignment]
        tag = str(data.get("tag", "STEP"))
        start = int(data.get("start", 0))  # type: ignore[call-overload]
        highlight_last = bool(data.get("highlight_last", False))
        gap = 0.35
        width = (CONTENT_W - (len(steps) - 1) * gap) / len(steps)
        for index, step in enumerate(steps):
            x = MARGIN_X + index * (width + gap)
            last = index == len(steps) - 1
            fill = {True: palette.warn, False: palette.accent}[last and highlight_last]
            painter.card(x, 2.3, width, 2.2, fill, f"{tag} {start + index}", radius=0.1)
            paper = palette.paper
            painter.text(
                [
                    Para((Run(tag, 14, paper),), align="center"),
                    Para((Run(str(start + index), 40, paper, bold=True),), align="center"),
                    Para((Run(str(step["label"]), 18, paper, bold=True),), align="center"),
                ],
                x, 2.3, width, 2.2, f"{tag} {start + index} 문구", anchor="middle",
            )
            if not last:
                arrow = [Para((Run(">", 28, palette.muted, bold=True),), align="center")]
                painter.text(arrow, x + width, 2.9, gap, 1.0, f"화살표 {index + 1}", anchor="middle")
        captions: Sequence[Mapping[str, object]] = data.get("captions", [])  # type: ignore[assignment]
        for index, caption in enumerate(captions):
            painter.text([_caption_paragraph(painter, caption, 20, 18)], MARGIN_X, 5.0 + index * 0.6, CONTENT_W, 0.5, f"아래 문구 {index + 1}", anchor="middle")


class ClosingLayout(Layout):
    name: ClassVar[str] = "closing"
    summary: ClassVar[str] = "마무리 (어두운 배경, 번호 항목과 하단 명령 상자)"
    dark: ClassVar[bool] = True
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="title", label="제목", max_chars=40, example_text="막히면 여기서 멈추세요"),
        TextListField(name="items", label="항목", min_items=1, max_items=5, max_chars=38, example_items=("첫 번째 항목", "두 번째 항목")),
        TextListField(name="code", label="하단 명령", required=False, min_items=0, max_items=3, max_chars=100, example_items=("Get-Date",)),
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        painter.title(str(data["title"]), MARGIN_X, 0.5, CONTENT_W, 0.9, 36, palette.paper)
        items: Sequence[str] = data["items"]  # type: ignore[assignment]
        for index, item in enumerate(items):
            y = 1.8 + index * 0.75
            painter.numbered_circle(MARGIN_X, y, 0.55, str(index + 1), palette.highlight, palette.ink, 18, f"항목 번호 {index + 1}")
            painter.text(plain(item, 20, palette.paper), MARGIN_X + 0.85, y, CONTENT_W - 0.85, 0.55, f"항목 {index + 1}", anchor="middle")
        code: Sequence[str] = data.get("code", [])  # type: ignore[assignment]
        if not code:
            return
        height = len(code) * 0.34 + 0.45
        painter.card(MARGIN_X, 5.75, CONTENT_W, height, blend(palette.paper, palette.primary, 0.12), "명령 배경")
        paragraphs = [Para(slot_runs(line, 13, palette.paper, palette.highlight, mono=True)) for line in code]
        painter.text(paragraphs, MARGIN_X + 0.3, 5.75, CONTENT_W - 0.6, height, "명령", anchor="middle")
