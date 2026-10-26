"""색과 글꼴. 양식은 팔레트의 의미 이름(ink, accent 등)으로만 색을 고른다."""

import re
from collections.abc import Mapping
from dataclasses import dataclass, fields, replace

from pptx.dml.color import RGBColor

from deckgen.fields import json_type, unknown_keys

_HEX_COLOR = re.compile(r"^[0-9A-Fa-f]{6}$")


@dataclass(frozen=True)
class Palette:
    ink: str = "1B2A33"
    paper: str = "FFFFFF"
    primary: str = "0F4C5C"
    surface: str = "EAF2F4"
    accent: str = "0F7B8A"
    warn: str = "D9580B"
    ok: str = "1F8A5B"
    danger: str = "C0392B"
    muted: str = "5C6B73"
    highlight: str = "F2B134"


PALETTE_KEYS: tuple[str, ...] = tuple(item.name for item in fields(Palette))


@dataclass(frozen=True)
class Theme:
    font: str = "Malgun Gothic"
    code_font: str = "Courier New"
    symbol_font: str = "Segoe UI Symbol"
    palette: Palette = Palette()


def validate_theme(raw: object, path: str = "theme") -> list[str]:
    if json_type(raw) != "object":
        return [f"{path}: 객체여야 합니다"]
    data: Mapping[str, object] = raw  # type: ignore[assignment]
    errors = unknown_keys(data, {"font", "code_font", "symbol_font", "palette"}, path)
    for key in ("font", "code_font", "symbol_font"):
        if key in data and (json_type(data[key]) != "string" or not str(data[key]).strip()):
            errors.append(f"{path}.{key}: 글꼴 이름(문자열)이어야 합니다")
    if "palette" not in data:
        return errors
    palette = data["palette"]
    if json_type(palette) != "object":
        return [*errors, f"{path}.palette: 객체여야 합니다"]
    errors.extend(unknown_keys(palette, set(PALETTE_KEYS), f"{path}.palette"))  # type: ignore[arg-type]
    for key, value in palette.items():  # type: ignore[attr-defined]
        if key in PALETTE_KEYS and not _HEX_COLOR.match(str(value)):
            errors.append(f"{path}.palette.{key}: 6자리 16진수 색이어야 합니다 (예: 0F4C5C)")
    return errors


def parse_theme(raw: Mapping[str, object]) -> Theme:
    """검증을 통과한 테마 설정으로 Theme 을 만든다."""
    palette = replace(Palette(), **{key: str(value).upper() for key, value in dict(raw.get("palette", {})).items()})  # type: ignore[call-overload]
    names = {key: str(raw[key]) for key in ("font", "code_font", "symbol_font") if key in raw}
    return replace(Theme(), palette=palette, **names)


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color.upper())


def blend(foreground: str, background: str, ratio: float) -> str:
    """foreground 를 ratio(0~1) 만큼 background 위에 섞은 색. 투명도 대신 쓴다."""
    fg = [int(foreground[index : index + 2], 16) for index in (0, 2, 4)]
    bg = [int(background[index : index + 2], 16) for index in (0, 2, 4)]
    mixed = [round(f * ratio + b * (1 - ratio)) for f, b in zip(fg, bg, strict=True)]
    return "".join(f"{channel:02X}" for channel in mixed)
