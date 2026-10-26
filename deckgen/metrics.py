"""글자 폭 추정. 상자에 글이 들어가는지 렌더링 없이 근사한다."""

import re
from unicodedata import east_asian_width

_WIDE_CLASSES = {"W", "F"}
_TOKEN = re.compile(r"\S+\s*|\s+")
_NARROW_PUNCTUATION = set(" .,:;!'\"|()[]{}/\\-_`")

MONO_EM = 0.6
WIDE_EM = 1.0
SPACE_EM = 0.3
NARROW_EM = 0.38
UPPER_EM = 0.64
LOWER_EM = 0.52
DEFAULT_EM = 0.56
BOLD_FACTOR = 1.06
LINE_HEIGHT = 1.25


def _proportional_em(char: str) -> float:
    """고정폭이 아닌 글꼴에서 글자 하나의 폭(em). 종류별 평균치."""
    if char == " ":
        return SPACE_EM
    if char in _NARROW_PUNCTUATION:
        return NARROW_EM
    if char.isascii() and char.isupper():
        return UPPER_EM
    if char.isascii() and char.islower():
        return LOWER_EM
    return DEFAULT_EM


def char_width_pt(char: str, size_pt: float, mono: bool, bold: bool) -> float:
    """글자 하나의 폭(pt). 한글·한자는 1em, 그 밖은 고정폭 0.6em 또는 종류별 평균."""
    if east_asian_width(char) in _WIDE_CLASSES:
        em = WIDE_EM
    elif mono:
        em = MONO_EM
    else:
        em = _proportional_em(char)
    return em * size_pt * {True: BOLD_FACTOR, False: 1.0}[bold]


def text_width_pt(text: str, size_pt: float, mono: bool, bold: bool) -> float:
    return sum(char_width_pt(char, size_pt, mono, bold) for char in text)


def count_lines(text: str, size_pt: float, width_in: float, mono: bool = False, bold: bool = False) -> int:
    """공백 단위로 줄바꿈할 때 필요한 줄 수. 단어가 한 줄보다 길면 글자 단위로 자른다."""
    limit = width_in * 72.0
    lines = 1
    current = 0.0
    for token in _TOKEN.findall(text):
        for chunk in _split_to_fit(token, size_pt, limit, mono, bold):
            chunk_width = text_width_pt(chunk, size_pt, mono, bold)
            overflow = current > 0 and current + text_width_pt(chunk.rstrip(), size_pt, mono, bold) > limit
            lines += int(overflow)
            current = {True: chunk_width, False: current + chunk_width}[overflow]
    return lines


def _split_to_fit(token: str, size_pt: float, limit: float, mono: bool, bold: bool) -> list[str]:
    if text_width_pt(token.rstrip(), size_pt, mono, bold) <= limit:
        return [token]
    pieces: list[str] = []
    piece = ""
    for char in token:
        too_wide = text_width_pt(piece + char, size_pt, mono, bold) > limit
        pieces.extend([piece] * int(too_wide and bool(piece)))
        piece = {True: char, False: piece + char}[too_wide and bool(piece)]
    return [*pieces, piece]


def lines_height_in(lines: int, size_pt: float) -> float:
    """줄 수와 글자 크기로 필요한 높이(인치)."""
    return lines * size_pt * LINE_HEIGHT / 72.0
