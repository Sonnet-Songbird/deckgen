"""단계 안내 양식. 번호 원, 안내 문장, 본문, 성공/실패 상자로 이루어진다."""

from collections.abc import Mapping, Sequence
from typing import ClassVar

from deckgen.fields import Field, TextField, TextListField
from deckgen.layouts.base import TONE_FIELD, Layout, plain
from deckgen.painter import CONTENT_W, MARGIN_X, RESULT_ROW_Y, Para, SlidePainter, slot_runs

_TITLE_X = 1.7
_TITLE_W = 13.333 - 1.7 - MARGIN_X
_BODY_GAP = 0.15
_AFTER_CODE_GAP = 0.25
_EXTRA_LINE_H = 0.32


def _header(painter: SlidePainter, data: Mapping[str, object]) -> float:
    """번호 원, 제목, 안내 문장을 그리고 본문이 시작할 y 를 돌려준다."""
    palette = painter.theme.palette
    painter.badge(str(data["badge"]), str(data.get("tone", "normal")))
    painter.title(str(data["title"]), _TITLE_X, 0.45, _TITLE_W, 0.9, 34, palette.primary)
    lead_height = painter.lead(str(data["lead"]))
    return 1.6 + lead_height + _BODY_GAP


class StepLayout(Layout):
    name: ClassVar[str] = "step"
    summary: ClassVar[str] = "단계 하나: 번호 원, 안내, 명령 상자, 추가 안내, 성공/실패 상자"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="badge", label="번호", max_chars=3, example_text="1"),
        TextField(name="title", label="제목", max_chars=40, example_text="STEP 1  서비스 재시작"),
        TextField(name="lead", label="안내 문장", max_chars=110, example_text="서비스를 다시 시작합니다."),
        TextListField(
            name="code",
            label="명령 (한 줄에 하나, <바꿀 곳>은 붉은 글씨)",
            min_items=1,
            max_items=8,
            max_chars=95,
            example_items=("Get-Service *app*", "Restart-Service <서비스이름>"),
        ),
        TextField(name="extra", label="명령 아래 추가 안내", required=False, max_chars=120, example_text="오류가 나오면 무시해도 됩니다."),
        TextField(name="ok", label="성공일 때", max_chars=100, example_text="화면이 정상으로 열리면 끝."),
        TextField(name="ng", label="실패일 때", max_chars=100, example_text="같은 오류가 나오면 다음 단계로."),
        TONE_FIELD,
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        y = _header(painter, data)
        code: Sequence[str] = data["code"]  # type: ignore[assignment]
        bottom = painter.code_block(code, y) + _AFTER_CODE_GAP
        extra = str(data.get("extra", ""))
        if extra:
            height = _EXTRA_LINE_H * 2
            painter.text(plain(extra, 16, palette.ink), MARGIN_X, bottom, CONTENT_W, height, "추가 안내")
            bottom += height
        painter.warn_if_below(bottom, RESULT_ROW_Y, "본문이 성공/실패 상자와 겹칩니다. 명령 줄 수나 안내를 줄이세요")
        painter.result_row(str(data["ok"]), str(data["ng"]))


class ProcedureLayout(Layout):
    name: ClassVar[str] = "procedure"
    summary: ClassVar[str] = "화면에서 누르는 절차: 번호 원, 안내, 번호 목록 상자, 성공/실패 상자"
    fields: ClassVar[tuple[Field, ...]] = (
        TextField(name="badge", label="번호", max_chars=3, example_text="2"),
        TextField(name="title", label="제목", max_chars=40, example_text="STEP 2  설정 화면에서 저장"),
        TextField(name="lead", label="안내 문장", max_chars=110, example_text="웹 화면에서 한 번만 누릅니다."),
        TextListField(
            name="steps",
            label="절차 (한 줄에 하나, 번호는 자동)",
            min_items=1,
            max_items=5,
            max_chars=90,
            example_items=("관리자로 로그인합니다", "설정 메뉴를 엽니다", "저장 버튼을 누릅니다"),
        ),
        TextField(name="ok", label="성공일 때", max_chars=100, example_text="저장 완료 문구가 보이면 끝."),
        TextField(name="ng", label="실패일 때", max_chars=100, example_text="오류가 나오면 관리자에게 알립니다."),
        TONE_FIELD,
    )

    def render(self, painter: SlidePainter, data: Mapping[str, object]) -> None:
        palette = painter.theme.palette
        y = _header(painter, data)
        steps: Sequence[str] = data["steps"]  # type: ignore[assignment]
        height = max(1.4, len(steps) * 0.55 + 0.6)
        painter.card(MARGIN_X, y, CONTENT_W, height, palette.surface, "절차 배경")
        paragraphs = [Para(slot_runs(f"{index + 1}.  {step}", 18, palette.ink, palette.danger), space_after=10) for index, step in enumerate(steps)]
        painter.text(paragraphs, MARGIN_X + 0.4, y, CONTENT_W - 0.8, height, "절차", anchor="middle")
        painter.warn_if_below(y + height, RESULT_ROW_Y - _AFTER_CODE_GAP, "절차 상자가 성공/실패 상자와 겹칩니다. 항목을 줄이세요")
        painter.result_row(str(data["ok"]), str(data["ng"]))
