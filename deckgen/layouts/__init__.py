"""양식 등록부. 이름으로 양식 객체를 찾는다."""

from deckgen.layouts.base import Layout
from deckgen.layouts.frames import ClosingLayout, FlowLayout, IntroCardsLayout, TitleLayout
from deckgen.layouts.lists import ChecklistLayout, NumberedListLayout, ProhibitionsLayout
from deckgen.layouts.steps import ProcedureLayout, StepLayout

_ALL: tuple[Layout, ...] = (
    TitleLayout(),
    IntroCardsLayout(),
    FlowLayout(),
    StepLayout(),
    ProcedureLayout(),
    ChecklistLayout(),
    NumberedListLayout(),
    ProhibitionsLayout(),
    ClosingLayout(),
)

LAYOUTS: dict[str, Layout] = {layout.name: layout for layout in _ALL}

__all__ = ["LAYOUTS", "Layout"]
