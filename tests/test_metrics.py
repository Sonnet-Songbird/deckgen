import unittest

from deckgen.metrics import count_lines, lines_height_in, text_width_pt


class MetricsTest(unittest.TestCase):
    def test_짧은_글은_한_줄이다(self) -> None:
        self.assertEqual(1, count_lines("확인", 20, 5.0))

    def test_한글은_글자당_1em_이다(self) -> None:
        self.assertEqual(200.0, text_width_pt("가" * 10, 20, mono=False, bold=False))

    def test_고정폭은_글자당_0점6em_이다(self) -> None:
        self.assertAlmostEqual(60.0, text_width_pt("a" * 10, 10, mono=True, bold=False))

    def test_너비를_넘는_한글_문장은_여러_줄이_된다(self) -> None:
        text = " ".join(["가나다라마"] * 8)
        self.assertEqual(3, count_lines(text, 20, 5.0))

    def test_공백_없는_긴_단어는_글자_단위로_자른다(self) -> None:
        self.assertGreater(count_lines("a" * 200, 10, 2.0), 1)

    def test_줄_수로_높이를_구한다(self) -> None:
        self.assertAlmostEqual(2 * 18 * 1.25 / 72.0, lines_height_in(2, 18))


if __name__ == "__main__":
    unittest.main()
