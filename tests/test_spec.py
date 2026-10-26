import unittest

from deckgen.layouts import LAYOUTS
from deckgen.spec import SpecError, example_deck, load_deck, parse_deck, validate_deck


def _title_slide() -> dict[str, object]:
    return {"layout": "title", "title": "제목"}


class SpecTest(unittest.TestCase):
    def test_최소_덱은_통과한다(self) -> None:
        self.assertEqual([], validate_deck({"slides": [_title_slide()]}))

    def test_예제_덱은_통과한다(self) -> None:
        self.assertEqual([], validate_deck(example_deck()))
        self.assertEqual(len(LAYOUTS), len(parse_deck(example_deck()).slides))

    def test_객체가_아니면_오류다(self) -> None:
        self.assertEqual(["스펙: 객체여야 합니다"], validate_deck([]))

    def test_slides_가_없으면_오류다(self) -> None:
        self.assertIn("slides: 필수 항목입니다", validate_deck({}))

    def test_알_수_없는_최상위_키는_오류다(self) -> None:
        self.assertIn("스펙.extra: 알 수 없는 항목입니다", validate_deck({"slides": [_title_slide()], "extra": 1}))

    def test_없는_양식은_사용_가능한_양식을_알려준다(self) -> None:
        errors = validate_deck({"slides": [{"layout": "nope"}]})
        self.assertIn("slides[0].layout", errors[0])
        self.assertIn("title", errors[0])

    def test_슬라이드_오류에_번호가_붙고_모두_모아_돌려준다(self) -> None:
        errors = validate_deck({"slides": [{"layout": "title"}, {"layout": "checklist", "title": "t", "items": ["a"]}]})
        self.assertTrue(any(item.startswith("slides[0].title") for item in errors))
        self.assertTrue(any(item.startswith("slides[1].items") for item in errors))

    def test_슬라이드가_없으면_오류다(self) -> None:
        self.assertIn("1~100장", validate_deck({"slides": []})[0])

    def test_테마_색은_6자리_16진수여야_한다(self) -> None:
        errors = validate_deck({"theme": {"palette": {"accent": "red"}}, "slides": [_title_slide()]})
        self.assertIn("theme.palette.accent", errors[0])

    def test_알_수_없는_팔레트_키는_오류다(self) -> None:
        errors = validate_deck({"theme": {"palette": {"nope": "FFFFFF"}}, "slides": [_title_slide()]})
        self.assertIn("theme.palette.nope: 알 수 없는 항목입니다", errors)

    def test_테마_일부만_바꾸면_나머지는_기본값이다(self) -> None:
        deck = parse_deck({"theme": {"palette": {"accent": "112233"}, "font": "Arial"}, "slides": [_title_slide()]})
        self.assertEqual("112233", deck.theme.palette.accent)
        self.assertEqual("Arial", deck.theme.font)
        self.assertEqual("0F4C5C", deck.theme.palette.primary)

    def test_잘못된_스펙은_SpecError_로_모든_오류를_돌려준다(self) -> None:
        with self.assertRaises(SpecError) as caught:
            parse_deck({"slides": [{"layout": "title"}]})
        self.assertEqual(["slides[0].title: 필수 항목입니다"], caught.exception.errors)

    def test_JSON_해석_실패는_위치를_알려준다(self) -> None:
        with self.assertRaises(SpecError) as caught:
            load_deck('{"slides": [')
        self.assertIn("JSON 해석 실패", caught.exception.errors[0])


if __name__ == "__main__":
    unittest.main()
