import json
import threading
import unittest
import urllib.error
import urllib.request

from deckgen.gui import make_server
from deckgen.layouts import LAYOUTS
from deckgen.spec import example_deck


class GuiServerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.server = make_server(0)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def _post(self, path: str, payload: object) -> tuple[int, bytes, dict[str, str]]:
        request = urllib.request.Request(self.base + path, data=json.dumps(payload).encode("utf-8"), method="POST")
        try:
            with urllib.request.urlopen(request) as response:
                return response.status, response.read(), dict(response.headers)
        except urllib.error.HTTPError as error:
            return error.code, error.read(), dict(error.headers)

    def test_첫_화면은_HTML_이다(self) -> None:
        with urllib.request.urlopen(self.base + "/") as response:
            body = response.read().decode("utf-8")
        self.assertIn("<title>deckgen</title>", body)

    def test_meta_는_양식_스키마와_예제를_준다(self) -> None:
        with urllib.request.urlopen(self.base + "/api/meta") as response:
            meta = json.loads(response.read())
        self.assertEqual(list(LAYOUTS), [item["name"] for item in meta["layouts"]])
        self.assertEqual(example_deck(), meta["example_deck"])
        self.assertIn("accent", meta["palette_keys"])
        self.assertEqual(set(LAYOUTS), set(meta["examples"]))

    def test_check_는_오류를_모아_돌려준다(self) -> None:
        status, body, _ = self._post("/api/check", {"slides": [{"layout": "title"}]})
        result = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual(["slides[0].title: 필수 항목입니다"], result["errors"])

    def test_check_는_그리기_경고를_돌려준다(self) -> None:
        status, body, _ = self._post("/api/check", {"slides": [{**LAYOUTS["step"].example(), "ng": "가" * 100}]})
        result = json.loads(body)
        self.assertEqual(200, status)
        self.assertEqual([], result["errors"])
        self.assertEqual(1, result["warnings"][0]["slide"])

    def test_build_는_pptx_를_돌려준다(self) -> None:
        status, body, headers = self._post("/api/build", example_deck())
        self.assertEqual(200, status)
        self.assertTrue(body.startswith(b"PK"))
        self.assertIn("presentationml", headers["Content-Type"])
        self.assertIn("deck.pptx", headers["Content-Disposition"])

    def test_잘못된_스펙은_422_와_오류를_돌려준다(self) -> None:
        status, body, _ = self._post("/api/build", {"slides": []})
        self.assertEqual(422, status)
        self.assertIn("1~100장", json.loads(body)["errors"][0])

    def test_JSON_이_아닌_요청은_422_이다(self) -> None:
        request = urllib.request.Request(self.base + "/api/build", data=b"{", method="POST")
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(request)
        self.assertEqual(422, caught.exception.code)

    def test_없는_경로는_404_이다(self) -> None:
        with self.assertRaises(urllib.error.HTTPError) as caught:
            urllib.request.urlopen(self.base + "/nope")
        self.assertEqual(404, caught.exception.code)


if __name__ == "__main__":
    unittest.main()
