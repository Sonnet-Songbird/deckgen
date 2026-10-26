"""명령줄 인터페이스. 사람과 AI 모두 같은 명령을 쓴다."""

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from deckgen.gui import serve
from deckgen.layouts import LAYOUTS
from deckgen.painter import BuildWarning
from deckgen.render import build
from deckgen.spec import SpecError, example_deck, load_deck
from deckgen.theme import Palette, Theme

EXIT_OK = 0
EXIT_INVALID = 1
EXIT_USAGE = 2


def _dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def _read_spec(path: str) -> str:
    """파일 경로, 또는 '-' 이면 표준입력에서 스펙 텍스트를 읽는다."""
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def _warning_dict(warning: BuildWarning) -> dict[str, object]:
    return {"slide": warning.slide, "layout": warning.layout, "message": warning.message}


def _print_warnings(warnings: Sequence[BuildWarning]) -> None:
    for warning in warnings:
        print(f"경고: {warning.slide}번 슬라이드({warning.layout}): {warning.message}", file=sys.stderr)


def _layout_or_error(name: str) -> str:
    if name not in LAYOUTS:
        raise SpecError([f"양식 '{name}' 이 없습니다. 사용 가능: {', '.join(LAYOUTS)}"])
    return name


# ---- 명령 ------------------------------------------------------------------
def cmd_layouts(args: argparse.Namespace) -> int:
    rows = [{"name": layout.name, "summary": layout.summary, "dark": layout.dark} for layout in LAYOUTS.values()]
    print(_dump(rows) if args.json else "\n".join(f"{row['name']:<14} {row['summary']}" for row in rows))
    return EXIT_OK


def cmd_schema(args: argparse.Namespace) -> int:
    names = [_layout_or_error(args.layout)] if args.layout else list(LAYOUTS)
    palette_defaults = {key: getattr(Palette(), key) for key in Palette.__dataclass_fields__}
    theme_defaults = {"font": Theme().font, "code_font": Theme().code_font, "symbol_font": Theme().symbol_font}
    schema = {
        "deck": {
            "theme": {"optional": True, "defaults": {**theme_defaults, "palette": palette_defaults}},
            "slides": "슬라이드 객체의 배열. 각 객체의 layout 에 양식 이름을 쓴다",
        },
        "layouts": {name: LAYOUTS[name].describe() for name in names},
    }
    print(_dump(schema))
    return EXIT_OK


def cmd_example(args: argparse.Namespace) -> int:
    if args.layout:
        print(_dump(LAYOUTS[_layout_or_error(args.layout)].example()))
        return EXIT_OK
    print(_dump(example_deck()))
    return EXIT_OK


def cmd_validate(args: argparse.Namespace) -> int:
    result = build(load_deck(_read_spec(args.spec)))
    print(_dump({"ok": True, "warnings": [_warning_dict(item) for item in result.warnings]}) if args.json else "스펙이 올바릅니다")
    _print_warnings(result.warnings if not args.json else ())
    return EXIT_INVALID if args.strict and result.warnings else EXIT_OK


def cmd_build(args: argparse.Namespace) -> int:
    result = build(load_deck(_read_spec(args.spec)))
    if args.strict and result.warnings:
        _print_warnings(result.warnings)
        print("--strict: 경고가 있어 파일을 만들지 않았습니다", file=sys.stderr)
        return EXIT_INVALID
    output = Path(args.output) if args.output else Path("deck.pptx")
    result.save(output)
    summary = {"output": str(output), "slides": len(result.presentation.slides), "warnings": [_warning_dict(item) for item in result.warnings]}
    print(_dump(summary) if args.json else f"{output} 생성 ({summary['slides']}장)")
    _print_warnings(result.warnings if not args.json else ())
    return EXIT_OK


def cmd_gui(args: argparse.Namespace) -> int:
    serve(args.port, open_browser=not args.no_open)
    return EXIT_OK


# ---- 파서 ------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deckgen", description="양식을 고르고 값만 채워 PPT 를 만듭니다")
    commands = parser.add_subparsers(dest="command", required=True)

    def add(name: str, handler: Callable[[argparse.Namespace], int], help_text: str) -> argparse.ArgumentParser:
        sub = commands.add_parser(name, help=help_text)
        sub.set_defaults(handler=handler)
        return sub

    layouts = add("layouts", cmd_layouts, "사용할 수 있는 양식 목록")
    layouts.add_argument("--json", action="store_true", help="JSON 으로 출력")

    schema = add("schema", cmd_schema, "양식의 필드 스키마(JSON). AI 가 스펙을 쓸 때 먼저 읽는다")
    schema.add_argument("layout", nargs="?", help="양식 이름 (생략하면 전체)")

    example = add("example", cmd_example, "예제 스펙(JSON)")
    example.add_argument("layout", nargs="?", help="양식 이름 (생략하면 모든 양식을 담은 덱)")

    for name, handler, text in (("validate", cmd_validate, "스펙 검증 (그리기 경고 포함)"), ("build", cmd_build, "스펙으로 pptx 생성")):
        sub = add(name, handler, text)
        sub.add_argument("spec", help="스펙 JSON 파일 경로. '-' 는 표준입력")
        sub.add_argument("--strict", action="store_true", help="경고가 있으면 실패 처리")
        sub.add_argument("--json", action="store_true", help="결과를 JSON 으로 출력")
        if name == "build":
            sub.add_argument("-o", "--output", help="저장할 pptx 경로 (기본 deck.pptx)")

    gui = add("gui", cmd_gui, "로컬 웹 화면 실행")
    gui.add_argument("--port", type=int, default=8765)
    gui.add_argument("--no-open", action="store_true", help="브라우저를 자동으로 열지 않음")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        return args.handler(args)
    except SpecError as error:
        print("\n".join(f"오류: {item}" for item in error.errors), file=sys.stderr)
        return EXIT_INVALID
    except OSError as error:
        print(f"오류: {error}", file=sys.stderr)
        return EXIT_USAGE
