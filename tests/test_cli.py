import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from deckgen.cli import main
from deckgen.layouts import LAYOUTS
from deckgen.spec import example_deck


def run(*argv: str, stdin: str = "") -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), mock.patch("sys.stdin", io.StringIO(stdin)):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _spec(self, deck: object) -> Path:
        path = self.dir / "spec.json"
        path.write_text(json.dumps(deck, ensure_ascii=False), encoding="utf-8")
        return path

    def test_layouts_는_모든_양식을_보여_준다(self) -> None:
        code, out, _ = run("layouts")
        self.assertEqual(0, code)
        for name in LAYOUTS:
            self.assertIn(name, out)

    def test_layouts_json_은_배열이다(self) -> None:
        _, out, _ = run("layouts", "--json")
        self.assertEqual(list(LAYOUTS), [item["name"] for item in json.loads(out)])

    def test_schema_는_양식의_필드를_담는다(self) -> None:
        code, out, _ = run("schema", "step")
        schema = json.loads(out)
        self.assertEqual(0, code)
        self.assertEqual(["step"], list(schema["layouts"]))
        self.assertIn("code", [item["name"] for item in schema["layouts"]["step"]["fields"]])

    def test_schema_는_테마_기본값을_담는다(self) -> None:
        _, out, _ = run("schema")
        self.assertEqual("0F4C5C", json.loads(out)["deck"]["theme"]["defaults"]["palette"]["primary"])

    def test_없는_양식은_오류다(self) -> None:
        code, _, err = run("schema", "nope")
        self.assertEqual(1, code)
        self.assertIn("nope", err)

    def test_example_은_검증을_통과하는_스펙이다(self) -> None:
        _, out, _ = run("example")
        self.assertEqual(example_deck(), json.loads(out))
        code, _, _ = run("validate", "-", stdin=out)
        self.assertEqual(0, code)

    def test_example_양식_하나(self) -> None:
        _, out, _ = run("example", "checklist")
        self.assertEqual("checklist", json.loads(out)["layout"])

    def test_validate_는_모든_오류를_보여_주고_1을_돌려준다(self) -> None:
        code, _, err = run("validate", "-", stdin='{"slides":[{"layout":"step","badge":"1"}]}')
        self.assertEqual(1, code)
        self.assertIn("slides[0].title: 필수 항목입니다", err)
        self.assertIn("slides[0].ng: 필수 항목입니다", err)

    def test_JSON_이_깨지면_1을_돌려준다(self) -> None:
        code, _, err = run("validate", "-", stdin="{")
        self.assertEqual(1, code)
        self.assertIn("JSON 해석 실패", err)

    def test_없는_파일은_2를_돌려준다(self) -> None:
        code, _, err = run("build", str(self.dir / "none.json"))
        self.assertEqual(2, code)
        self.assertIn("오류", err)

    def test_build_는_파일을_만든다(self) -> None:
        output = self.dir / "out.pptx"
        code, out, _ = run("build", str(self._spec(example_deck())), "-o", str(output))
        self.assertEqual(0, code)
        self.assertTrue(output.read_bytes().startswith(b"PK"))
        self.assertIn("9장", out)

    def test_build_json_은_요약을_출력한다(self) -> None:
        output = self.dir / "out.pptx"
        _, out, _ = run("build", str(self._spec(example_deck())), "-o", str(output), "--json")
        summary = json.loads(out)
        self.assertEqual({"output": str(output), "slides": 9, "warnings": []}, summary)

    def test_표준입력으로_스펙을_받는다(self) -> None:
        output = self.dir / "stdin.pptx"
        code, _, _ = run("build", "-", "-o", str(output), stdin=json.dumps(example_deck()))
        self.assertEqual(0, code)
        self.assertTrue(output.exists())

    def test_strict_는_경고가_있으면_파일을_만들지_않는다(self) -> None:
        deck = {"slides": [{**LAYOUTS["step"].example(), "ng": "가" * 100}]}
        output = self.dir / "strict.pptx"
        code, _, err = run("build", str(self._spec(deck)), "-o", str(output), "--strict")
        self.assertEqual(1, code)
        self.assertFalse(output.exists())
        self.assertIn("경고", err)

    def test_strict_없이는_경고가_있어도_만든다(self) -> None:
        deck = {"slides": [{**LAYOUTS["step"].example(), "ng": "가" * 100}]}
        output = self.dir / "loose.pptx"
        code, _, err = run("build", str(self._spec(deck)), "-o", str(output))
        self.assertEqual(0, code)
        self.assertTrue(output.exists())
        self.assertIn("경고", err)


if __name__ == "__main__":
    unittest.main()
