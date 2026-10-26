import unittest

from deckgen.fields import BoolField, ChoiceField, IntField, ObjectListField, TextField, TextListField, json_type


class JsonTypeTest(unittest.TestCase):
    def test_json_값의_타입_이름을_돌려준다(self) -> None:
        names = [json_type(value) for value in ("a", 1, 1.5, True, None, [], {})]
        self.assertEqual(["string", "integer", "number", "boolean", "null", "array", "object"], names)

    def test_bool_은_정수로_취급하지_않는다(self) -> None:
        self.assertEqual("boolean", json_type(True))


class TextFieldTest(unittest.TestCase):
    field = TextField(name="title", label="제목", max_chars=5)

    def test_정상_값은_통과한다(self) -> None:
        self.assertEqual([], self.field.validate({"title": "가나다"}, "s"))

    def test_필수_항목이_없으면_오류다(self) -> None:
        self.assertEqual(["s.title: 필수 항목입니다"], self.field.validate({}, "s"))

    def test_선택_항목은_없어도_된다(self) -> None:
        optional = TextField(name="sub", label="부제", required=False, max_chars=5)
        self.assertEqual([], optional.validate({}, "s"))

    def test_문자열이_아니면_오류다(self) -> None:
        self.assertIn("문자열", self.field.validate({"title": 3}, "s")[0])

    def test_비어_있으면_오류다(self) -> None:
        self.assertIn("비어 있을 수 없습니다", self.field.validate({"title": "  "}, "s")[0])

    def test_길이를_넘으면_오류다(self) -> None:
        self.assertIn("5자를 넘을 수 없습니다", self.field.validate({"title": "가나다라마바"}, "s")[0])

    def test_한_줄_필드에_줄바꿈이_있으면_오류다(self) -> None:
        self.assertIn("줄바꿈", self.field.validate({"title": "가\n나"}, "s")[0])

    def test_여러_줄_필드는_줄바꿈을_허용한다(self) -> None:
        multiline = TextField(name="t", label="t", max_chars=10, multiline=True)
        self.assertEqual([], multiline.validate({"t": "가\n나"}, "s"))


class TextListFieldTest(unittest.TestCase):
    field = TextListField(name="items", label="항목", min_items=1, max_items=2, max_chars=3)

    def test_정상_값은_통과한다(self) -> None:
        self.assertEqual([], self.field.validate({"items": ["a", "b"]}, "s"))

    def test_개수가_범위를_벗어나면_오류다(self) -> None:
        self.assertIn("1~2개", self.field.validate({"items": []}, "s")[0])
        self.assertIn("1~2개", self.field.validate({"items": ["a", "b", "c"]}, "s")[0])

    def test_항목별_오류에_위치가_붙는다(self) -> None:
        errors = self.field.validate({"items": ["abcd", 1]}, "s")
        self.assertEqual("s.items[0]", errors[0].split(":")[0])
        self.assertEqual("s.items[1]", errors[1].split(":")[0])

    def test_배열이_아니면_오류다(self) -> None:
        self.assertIn("배열", self.field.validate({"items": "a"}, "s")[0])


class ObjectListFieldTest(unittest.TestCase):
    field = ObjectListField(
        name="cards",
        label="카드",
        min_items=1,
        max_items=2,
        item_fields=(TextField(name="text", label="내용", max_chars=3), ChoiceField(name="tone", label="강조", required=False, choices=("a", "b"), default="a")),
    )

    def test_정상_값은_통과한다(self) -> None:
        self.assertEqual([], self.field.validate({"cards": [{"text": "x", "tone": "b"}]}, "s"))

    def test_하위_필드_오류에_경로가_붙는다(self) -> None:
        errors = self.field.validate({"cards": [{"text": "abcd"}]}, "s")
        self.assertEqual("s.cards[0].text", errors[0].split(":")[0])

    def test_알_수_없는_키는_오류다(self) -> None:
        errors = self.field.validate({"cards": [{"text": "x", "oops": 1}]}, "s")
        self.assertEqual(["s.cards[0].oops: 알 수 없는 항목입니다"], errors)

    def test_객체가_아닌_항목은_오류다(self) -> None:
        self.assertIn("객체", self.field.validate({"cards": ["x"]}, "s")[0])

    def test_스키마_설명에_하위_필드가_들어_있다(self) -> None:
        described = self.field.describe()
        self.assertEqual("objects", described["type"])
        self.assertEqual(["text", "tone"], [item["name"] for item in described["item_fields"]])  # type: ignore[index]


class SimpleFieldsTest(unittest.TestCase):
    def test_선택지에_없는_값은_오류다(self) -> None:
        field = ChoiceField(name="tone", label="강조", choices=("normal", "warn"), default="normal")
        self.assertEqual([], field.validate({"tone": "warn"}, "s"))
        self.assertIn("normal, warn", field.validate({"tone": "red"}, "s")[0])

    def test_불리언만_허용한다(self) -> None:
        field = BoolField(name="flag", label="표시")
        self.assertEqual([], field.validate({"flag": True}, "s"))
        self.assertIn("true/false", field.validate({"flag": 1}, "s")[0])

    def test_정수_범위를_검사한다(self) -> None:
        field = IntField(name="start", label="시작", minimum=0, maximum=9, default=0)
        self.assertEqual([], field.validate({"start": 3}, "s"))
        self.assertIn("0~9", field.validate({"start": 10}, "s")[0])
        self.assertIn("정수", field.validate({"start": "3"}, "s")[0])
        self.assertIn("정수", field.validate({"start": True}, "s")[0])


if __name__ == "__main__":
    unittest.main()
