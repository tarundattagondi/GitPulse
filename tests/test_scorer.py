import unittest
from gitpulse.utils import parse_json_response


class TestParseJsonResponse(unittest.TestCase):

    def test_direct_json(self):
        result = parse_json_response('{"score": 85}')
        self.assertEqual(result["score"], 85)

    def test_json_in_code_fence(self):
        text = '```json\n{"score": 85}\n```'
        result = parse_json_response(text)
        self.assertEqual(result["score"], 85)

    def test_json_with_surrounding_text(self):
        text = 'Here is the result:\n{"score": 85}\nDone.'
        result = parse_json_response(text)
        self.assertEqual(result["score"], 85)

    def test_invalid_json_raises(self):
        with self.assertRaises(ValueError):
            parse_json_response("not json at all")


if __name__ == "__main__":
    unittest.main()
