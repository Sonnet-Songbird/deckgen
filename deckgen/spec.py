"""덱 스펙(JSON) 검증과 해석."""

import json
from collections.abc import Mapping
from dataclasses import dataclass

from deckgen.fields import json_type, unknown_keys
from deckgen.layouts import LAYOUTS, Layout
from deckgen.theme import Theme, parse_theme, validate_theme

MAX_SLIDES = 100


class SpecError(ValueError):
    """스펙이 올바르지 않을 때. errors 에 모든 문제를 담는다."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors


@dataclass(frozen=True)
class SlideSpec:
    layout: Layout
    data: Mapping[str, object]


@dataclass(frozen=True)
class DeckSpec:
    theme: Theme
    slides: tuple[SlideSpec, ...]


def _validate_slide(raw: object, path: str) -> list[str]:
    if json_type(raw) != "object":
        return [f"{path}: 객체여야 합니다"]
    data: Mapping[str, object] = raw  # type: ignore[assignment]
    name = data.get("layout")
    if json_type(name) != "string" or name not in LAYOUTS:
        return [f"{path}.layout: {', '.join(LAYOUTS)} 중 하나여야 합니다 (현재 {name!r})"]
    return LAYOUTS[str(name)].validate(data, path)


def validate_deck(raw: object) -> list[str]:
    """덱 스펙의 모든 문제를 한 번에 모아 돌려준다."""
    if json_type(raw) != "object":
        return ["스펙: 객체여야 합니다"]
    data: Mapping[str, object] = raw  # type: ignore[assignment]
    errors = unknown_keys(data, {"theme", "slides"}, "스펙")
    errors.extend(validate_theme(data["theme"]) if "theme" in data else [])
    if "slides" not in data:
        return [*errors, "slides: 필수 항목입니다"]
    slides = data["slides"]
    if json_type(slides) != "array":
        return [*errors, "slides: 배열이어야 합니다"]
    items = list(slides)  # type: ignore[call-overload]
    if not 1 <= len(items) <= MAX_SLIDES:
        errors.append(f"slides: 슬라이드는 1~{MAX_SLIDES}장이어야 합니다 (현재 {len(items)}장)")
    for index, slide in enumerate(items):
        errors.extend(_validate_slide(slide, f"slides[{index}]"))
    return errors


def parse_deck(raw: object) -> DeckSpec:
    """검증 후 DeckSpec 으로 바꾼다. 문제가 있으면 SpecError."""
    errors = validate_deck(raw)
    if errors:
        raise SpecError(errors)
    data: Mapping[str, object] = raw  # type: ignore[assignment]
    theme = parse_theme(data.get("theme", {}))  # type: ignore[arg-type]
    slides = tuple(SlideSpec(LAYOUTS[str(slide["layout"])], slide) for slide in data["slides"])  # type: ignore[index, attr-defined]
    return DeckSpec(theme, slides)


def load_deck(text: str) -> DeckSpec:
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise SpecError([f"JSON 해석 실패: {error.msg} ({error.lineno}행 {error.colno}열)"]) from error
    return parse_deck(raw)


def example_deck() -> dict[str, object]:
    """모든 양식의 예제를 한 장씩 담은 덱."""
    return {"slides": [layout.example() for layout in LAYOUTS.values()]}
