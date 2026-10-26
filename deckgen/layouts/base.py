"""양식의 공통 틀. 양식마다 필드 목록과 그리는 방법을 가진다."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from typing import ClassVar

from deckgen.fields import ChoiceField, Field, ObjectListField, TextField, unknown_keys
from deckgen.painter import Para, Run, SlidePainter

NOTES_FIELD = TextField(
    name="notes",
    label="발표자 노트",
    required=False,
    max_chars=1000,
    multiline=True,
    hint="슬라이드 쇼에는 보이지 않는 메모",
)

TONE_FIELD = ChoiceField(
    name="tone",
    label="강조 색",
    required=False,
    choices=("normal", "warn"),
    default="normal",
    hint="warn 이면 번호 원이 주황색",
)


def caption_field(name: str, label: str, max_items: int) -> ObjectListField:
    """보조 문구 목록. tone 이 warn 이면 주황 굵은 글씨."""
    return ObjectListField(
        name=name,
        label=label,
        required=False,
        min_items=0,
        max_items=max_items,
        item_fields=(
            TextField(name="text", label="문구", max_chars=110, example_text="문구를 입력하세요"),
            ChoiceField(name="tone", label="강조", required=False, choices=("normal", "warn"), default="normal"),
        ),
        example_items=({"text": "일반 문구", "tone": "normal"}, {"text": "강조할 문구", "tone": "warn"}),
    )


def plain(text: str, size: float, color: str, bold: bool = False, align: str = "left", space_after: float = 0.0) -> list[Para]:
    """줄바꿈마다 문단 하나. 여러 줄 글을 같은 모양으로 그린다."""
    return [Para((Run(line, size, color, bold=bold),), align=align, space_after=space_after) for line in text.split("\n")]


class Layout(ABC):
    name: ClassVar[str]
    summary: ClassVar[str]
    dark: ClassVar[bool] = False
    fields: ClassVar[tuple[Field, ...]]

    @classmethod
    def all_fields(cls) -> tuple[Field, ...]:
        return (*cls.fields, NOTES_FIELD)

    def validate(self, data: Mapping[str, object], path: str) -> list[str]:
        allowed = {"layout", *(item.name for item in self.all_fields())}
        errors = unknown_keys(data, allowed, path)
        for item in self.all_fields():
            errors.extend(item.validate(data, path))
        return errors

    def describe(self) -> dict[str, object]:
        return {
            "name": self.name,
            "summary": self.summary,
            "dark": self.dark,
            "fields": [item.describe() for item in self.all_fields()],
        }

    def example(self) -> dict[str, object]:
        return {"layout": self.name, **{item.name: item.example() for item in self.fields}}

    @abstractmethod
    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        """검증을 통과한 값으로 슬라이드를 그린다."""
