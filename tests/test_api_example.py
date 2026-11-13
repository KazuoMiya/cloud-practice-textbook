"""Run the published handler against a fake table; no AWS calls or credentials."""
import json
from pathlib import Path
import re
import types
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / 'book/17-s6.md'


class ApiExampleTest(unittest.TestCase):
    def setUp(self):
        self.table = Mock()
        self.table.scan.return_value = {'Items': [{'id': 'sample', 'text': '学習'}]}
        boto3 = types.SimpleNamespace(resource=lambda _: types.SimpleNamespace(Table=lambda _: self.table))
        source = re.findall(r'```python\n(.*?)\n```', SOURCE.read_text(encoding='utf-8'), re.S)[0]
        self.scope = {}
        with patch.dict('sys.modules', {'boto3': boto3}), patch.dict('os.environ', {'TABLE_NAME': 'test'}):
            exec(compile(source, str(SOURCE), 'exec'), self.scope)

    def call(self, method, body=None, **fields):
        return self.scope['handler']({'requestContext': {'http': {'method': method}}, 'body': body, **fields}, None)

    def test_valid_post_and_get(self):
        response = self.call('POST', json.dumps({'text': ' 学習 '}))
        self.assertEqual(response['statusCode'], 201)
        self.assertEqual(json.loads(response['body'])['text'], '学習')
        self.table.put_item.assert_called_once()
        self.assertEqual(self.call('GET')['statusCode'], 200)
        self.table.scan.assert_called_once_with(Limit=20)

    def test_invalid_inputs_never_write(self):
        for body in [None, '', '{', 'null', '[]', '42', '{"text":1}', '{"text":[]}', '{"text":" "}',
                     json.dumps({'text': 'a' * 201}), json.dumps({'text': 'あ' * 201}),
                     json.dumps({'text': 'a', 'extra': 'x' * 4096})]:
            with self.subTest(body=str(body)[:30]):
                self.assertEqual(self.call('POST', body)['statusCode'], 400)
        self.assertEqual(self.call('POST', 'e30=', isBase64Encoded=True)['statusCode'], 400)
        self.table.put_item.assert_not_called()

    def test_longest_allowed_memo_fits_in_the_body_limit(self):
        # 200 characters must be accepted however the client encodes them:
        # raw UTF-8, \uXXXX escapes (json.dumps default), or surrogate pairs.
        for label, text, escape in [('utf8', 'あ' * 200, False), ('escaped', 'あ' * 200, True),
                                    ('surrogates', '\U0001F600' * 200, True)]:
            with self.subTest(label):
                body = json.dumps({'text': text}, ensure_ascii=escape)
                self.assertLessEqual(len(body.encode('utf-8')), 4096)
                self.assertEqual(self.call('POST', body)['statusCode'], 201)
        self.assertEqual(self.table.put_item.call_count, 3)

    def test_unsupported_method_never_reads_or_writes(self):
        self.assertEqual(self.call('DELETE')['statusCode'], 405)
        self.table.scan.assert_not_called()
        self.table.put_item.assert_not_called()

    def test_every_python_example_compiles(self):
        for i, source in enumerate(re.findall(r'```python\n(.*?)\n```', SOURCE.read_text(encoding='utf-8'), re.S)):
            compile(source, f'chapter17-example-{i}', 'exec')


if __name__ == '__main__':
    unittest.main()
