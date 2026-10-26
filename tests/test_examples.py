import unittest
from pathlib import Path

from deckgen.render import build
from deckgen.spec import load_deck

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


class ExamplesTest(unittest.TestCase):
    def test_예제_스펙은_모두_경고_없이_그려진다(self) -> None:
        for path in sorted(EXAMPLES.glob("*.json")):
            with self.subTest(example=path.name):
                result = build(load_deck(path.read_text(encoding="utf-8")))
                self.assertEqual((), result.warnings)

    def test_Gitea_조치_가이드는_15장이다(self) -> None:
        result = build(load_deck((EXAMPLES / "gitea-repair.json").read_text(encoding="utf-8")))
        self.assertEqual(15, len(result.presentation.slides))


if __name__ == "__main__":
    unittest.main()
