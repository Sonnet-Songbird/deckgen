"""로컬 웹 화면 서버. 127.0.0.1 에만 열고 외부 의존성 없이 표준 라이브러리로 동작한다."""

import json
import webbrowser
from collections.abc import Callable
from dataclasses import fields
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import quote

from deckgen.layouts import LAYOUTS
from deckgen.painter import BuildWarning
from deckgen.render import build
from deckgen.spec import SpecError, example_deck, parse_deck
from deckgen.theme import PALETTE_KEYS, Palette, Theme

HOST = "127.0.0.1"
MAX_BODY_BYTES = 2_000_000
PPTX_MIME = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
_INDEX = Path(__file__).parent / "web" / "index.html"


def _warning_dict(warning: BuildWarning) -> dict[str, object]:
    return {"slide": warning.slide, "layout": warning.layout, "message": warning.message}


def _meta() -> dict[str, object]:
    theme = Theme()
    return {
        "layouts": [layout.describe() for layout in LAYOUTS.values()],
        "palette_keys": list(PALETTE_KEYS),
        "default_theme": {
            "font": theme.font,
            "code_font": theme.code_font,
            "symbol_font": theme.symbol_font,
            "palette": {item.name: getattr(Palette(), item.name) for item in fields(Palette)},
        },
        "example_deck": example_deck(),
        "examples": {name: layout.example() for name, layout in LAYOUTS.items()},
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "deckgen"

    # ---- 응답 도우미 -----------------------------------------------------
    def _send(self, status: HTTPStatus, content_type: str, body: bytes, headers: dict[str, str] | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: object, status: HTTPStatus = HTTPStatus.OK) -> None:
        self._send(status, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def _read_json(self) -> object:
        length = int(self.headers.get("Content-Length", "0"))
        if length > MAX_BODY_BYTES:
            raise SpecError([f"요청이 너무 큽니다 ({MAX_BODY_BYTES} 바이트 이하)"])
        try:
            return json.loads(self.rfile.read(length) or b"null")
        except json.JSONDecodeError as error:
            raise SpecError([f"JSON 해석 실패: {error.msg}"]) from error

    # ---- 경로별 처리 -----------------------------------------------------
    def _get_index(self) -> None:
        self._send(HTTPStatus.OK, "text/html; charset=utf-8", _INDEX.read_bytes())

    def _get_meta(self) -> None:
        self._send_json(_meta())

    def _post_check(self) -> None:
        try:
            result = build(parse_deck(self._read_json()))
        except SpecError as error:
            self._send_json({"errors": error.errors, "warnings": []})
            return
        self._send_json({"errors": [], "warnings": [_warning_dict(item) for item in result.warnings]})

    def _post_build(self) -> None:
        try:
            result = build(parse_deck(self._read_json()))
        except SpecError as error:
            self._send_json({"errors": error.errors}, HTTPStatus.UNPROCESSABLE_ENTITY)
            return
        disposition = f"attachment; filename*=UTF-8''{quote('deck.pptx')}"
        self._send(HTTPStatus.OK, PPTX_MIME, result.to_bytes(), {"Content-Disposition": disposition, "X-Deckgen-Warnings": str(len(result.warnings))})

    GET_ROUTES: dict[str, Callable[["Handler"], None]] = {"/": _get_index, "/api/meta": _get_meta}
    POST_ROUTES: dict[str, Callable[["Handler"], None]] = {"/api/check": _post_check, "/api/build": _post_build}

    def _dispatch(self, routes: dict[str, Callable[["Handler"], None]]) -> None:
        handler = routes.get(self.path.split("?")[0])
        if handler is None:
            self._send_json({"errors": ["없는 경로입니다"]}, HTTPStatus.NOT_FOUND)
            return
        handler(self)

    def do_GET(self) -> None:  # noqa: N802 (표준 라이브러리 규약)
        self._dispatch(self.GET_ROUTES)

    def do_POST(self) -> None:  # noqa: N802
        self._dispatch(self.POST_ROUTES)

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """요청 로그는 남기지 않는다."""


def make_server(port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((HOST, port), Handler)


def serve(port: int, open_browser: bool) -> None:
    server = make_server(port)
    url = f"http://{HOST}:{server.server_address[1]}/"
    print(f"deckgen 화면: {url}  (종료: Ctrl+C)")
    if open_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("종료합니다")
    finally:
        server.server_close()
