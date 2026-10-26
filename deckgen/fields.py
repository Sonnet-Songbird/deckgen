"""양식 필드 정의. 필드마다 검증 규칙, 스키마 설명, 예제 값을 한곳에서 갖는다."""

from abc import ABC, abstractmethod
from collections.abc import Mapping
from dataclasses import dataclass
from typing import ClassVar

_JSON_TYPE_NAMES: dict[type, str] = {
    str: "string",
    bool: "boolean",
    int: "integer",
    float: "number",
    list: "array",
    dict: "object",
    type(None): "null",
}


def json_type(value: object) -> str:
    """JSON 값의 타입 이름. 타입 객체로 직접 조회한다."""
    return _JSON_TYPE_NAMES.get(type(value), type(value).__name__)


def unknown_keys(data: Mapping[str, object], allowed: set[str], path: str) -> list[str]:
    """허용 목록에 없는 키를 오류로 돌려준다."""
    return [f"{path}.{key}: 알 수 없는 항목입니다" for key in data if key not in allowed]


@dataclass(frozen=True, kw_only=True)
class Field(ABC):
    name: str
    label: str
    required: bool = True
    hint: str = ""

    kind: ClassVar[str]

    @abstractmethod
    def validate_value(self, value: object, path: str) -> list[str]:
        """값 하나를 검증한다."""

    @abstractmethod
    def constraints(self) -> dict[str, object]:
        """스키마에 싣는 제약."""

    @abstractmethod
    def example(self) -> object:
        """예제 값."""

    def describe(self) -> dict[str, object]:
        return {
            "name": self.name,
            "label": self.label,
            "type": self.kind,
            "required": self.required,
            "hint": self.hint,
            **self.constraints(),
        }

    def validate(self, data: Mapping[str, object], path: str) -> list[str]:
        if self.name not in data:
            return [f"{path}.{self.name}: 필수 항목입니다"] if self.required else []
        return self.validate_value(data[self.name], f"{path}.{self.name}")


def _type_error(value: object, expected: str, path: str) -> list[str]:
    return [f"{path}: {expected} 이어야 합니다 (현재 {json_type(value)})"]


@dataclass(frozen=True, kw_only=True)
class TextField(Field):
    max_chars: int
    multiline: bool = False
    example_text: str = ""

    kind: ClassVar[str] = "text"

    def validate_value(self, value: object, path: str) -> list[str]:
        if json_type(value) != "string":
            return _type_error(value, "문자열", path)
        text = str(value)
        errors: list[str] = []
        if self.required and not text.strip():
            errors.append(f"{path}: 비어 있을 수 없습니다")
        if len(text) > self.max_chars:
            errors.append(f"{path}: {self.max_chars}자를 넘을 수 없습니다 (현재 {len(text)}자)")
        if not self.multiline and "\n" in text:
            errors.append(f"{path}: 줄바꿈을 쓸 수 없습니다")
        return errors

    def constraints(self) -> dict[str, object]:
        return {"max_chars": self.max_chars, "multiline": self.multiline}

    def example(self) -> object:
        return self.example_text


@dataclass(frozen=True, kw_only=True)
class TextListField(Field):
    """문자열 목록. 화면에서는 한 줄에 항목 하나로 입력한다."""

    min_items: int = 1
    max_items: int
    max_chars: int
    example_items: tuple[str, ...] = ()

    kind: ClassVar[str] = "list"

    def validate_value(self, value: object, path: str) -> list[str]:
        if json_type(value) != "array":
            return _type_error(value, "배열", path)
        items = list(value)  # type: ignore[call-overload]
        errors: list[str] = []
        if not self.min_items <= len(items) <= self.max_items:
            errors.append(f"{path}: 항목은 {self.min_items}~{self.max_items}개여야 합니다 (현재 {len(items)}개)")
        for index, item in enumerate(items):
            item_path = f"{path}[{index}]"
            if json_type(item) != "string":
                errors.extend(_type_error(item, "문자열", item_path))
                continue
            if len(item) > self.max_chars:
                errors.append(f"{item_path}: {self.max_chars}자를 넘을 수 없습니다 (현재 {len(item)}자)")
        return errors

    def constraints(self) -> dict[str, object]:
        return {"min_items": self.min_items, "max_items": self.max_items, "max_chars": self.max_chars}

    def example(self) -> object:
        return list(self.example_items)


@dataclass(frozen=True, kw_only=True)
class ObjectListField(Field):
    """하위 필드를 가진 항목의 목록."""

    item_fields: tuple[Field, ...]
    min_items: int = 1
    max_items: int
    example_items: tuple[Mapping[str, object], ...] = ()

    kind: ClassVar[str] = "objects"

    def validate_value(self, value: object, path: str) -> list[str]:
        if json_type(value) != "array":
            return _type_error(value, "배열", path)
        items = list(value)  # type: ignore[call-overload]
        errors: list[str] = []
        if not self.min_items <= len(items) <= self.max_items:
            errors.append(f"{path}: 항목은 {self.min_items}~{self.max_items}개여야 합니다 (현재 {len(items)}개)")
        allowed = {item_field.name for item_field in self.item_fields}
        for index, item in enumerate(items):
            item_path = f"{path}[{index}]"
            if json_type(item) != "object":
                errors.extend(_type_error(item, "객체", item_path))
                continue
            errors.extend(unknown_keys(item, allowed, item_path))
            for item_field in self.item_fields:
                errors.extend(item_field.validate(item, item_path))
        return errors

    def constraints(self) -> dict[str, object]:
        return {
            "min_items": self.min_items,
            "max_items": self.max_items,
            "item_fields": [item_field.describe() for item_field in self.item_fields],
        }

    def example(self) -> object:
        return [dict(item) for item in self.example_items]


@dataclass(frozen=True, kw_only=True)
class ChoiceField(Field):
    choices: tuple[str, ...]
    default: str

    kind: ClassVar[str] = "choice"

    def validate_value(self, value: object, path: str) -> list[str]:
        if value in self.choices:
            return []
        return [f"{path}: {', '.join(self.choices)} 중 하나여야 합니다 (현재 {value!r})"]

    def constraints(self) -> dict[str, object]:
        return {"choices": list(self.choices), "default": self.default}

    def example(self) -> object:
        return self.default


@dataclass(frozen=True, kw_only=True)
class BoolField(Field):
    default: bool = False

    kind: ClassVar[str] = "bool"

    def validate_value(self, value: object, path: str) -> list[str]:
        return [] if json_type(value) == "boolean" else _type_error(value, "true/false", path)

    def constraints(self) -> dict[str, object]:
        return {"default": self.default}

    def example(self) -> object:
        return self.default


@dataclass(frozen=True, kw_only=True)
class IntField(Field):
    minimum: int
    maximum: int
    default: int

    kind: ClassVar[str] = "int"

    def validate_value(self, value: object, path: str) -> list[str]:
        if json_type(value) != "integer":
            return _type_error(value, "정수", path)
        if not self.minimum <= int(value) <= self.maximum:  # type: ignore[call-overload]
            return [f"{path}: {self.minimum}~{self.maximum} 범위여야 합니다 (현재 {value})"]
        return []

    def constraints(self) -> dict[str, object]:
        return {"minimum": self.minimum, "maximum": self.maximum, "default": self.default}

    def example(self) -> object:
        return self.default
