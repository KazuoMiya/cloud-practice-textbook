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


class CallApiScriptTest(unittest.TestCase):
    """The signing client must send the body it is given and show error responses instead of crashing."""

    def run_script(self, argv, status=200):
        import io
        import urllib.error
        source = re.findall(r'```python\n(.*?)\n```', SOURCE.read_text(), re.S)[1]
        source = source.replace('https://API_ID.', 'https://abc123.')
        sent = {}

        class Credentials:
            def get_frozen_credentials(self):
                return object()

        class FakeRequest:
            def __init__(self, method, url, data, headers):
                self.headers = dict(headers)

        class FakeSigner:
            def __init__(self, credentials, service, region):
                pass

            def add_auth(self, request):
                request.headers['Authorization'] = 'signed'

        class Response:
            def __init__(self):
                self.status = status

            def read(self):
                return b'{}'

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

        class Opener:
            def open(self, request, timeout):
                sent['method'] = request.get_method()
                sent['body'] = request.data
                sent['auth'] = request.headers.get('Authorization')
                if status >= 400:
                    raise urllib.error.HTTPError(request.full_url, status, 'error', {}, io.BytesIO(b'{"error":"x"}'))
                return Response()

        modules = {
            'boto3': types.SimpleNamespace(Session=lambda: types.SimpleNamespace(get_credentials=Credentials)),
            'botocore': types.SimpleNamespace(),
            'botocore.auth': types.SimpleNamespace(SigV4Auth=FakeSigner),
            'botocore.awsrequest': types.SimpleNamespace(AWSRequest=FakeRequest),
        }
        out = io.StringIO()
        with patch.dict('sys.modules', modules), patch('sys.argv', ['call_api.py', *argv]), \
                patch('urllib.request.build_opener', lambda *handlers: Opener()), patch('sys.stdout', out):
            exec(compile(source, 'call_api.py', 'exec'), {'__name__': '__main__'})
        return sent, out.getvalue()

    def test_posts_the_given_body_and_prints_error_codes(self):
        for body in ['{"text": ', '{"text": "   "}', json.dumps({'text': 'あ' * 201}, ensure_ascii=False)]:
            with self.subTest(body=body[:20]):
                sent, out = self.run_script(['POST', body], status=400)
                self.assertEqual(sent['body'], body.encode('utf-8'))
                self.assertEqual(sent['method'], 'POST')
                self.assertEqual(sent['auth'], 'signed')
                self.assertTrue(out.startswith('400 '))

    def test_default_post_and_get(self):
        sent, out = self.run_script(['POST'], status=201)
        self.assertEqual(json.loads(sent['body'])['text'], '学習用の架空のメモ')
        self.assertTrue(out.startswith('201 '))
        sent, _ = self.run_script([])
        self.assertEqual(sent['method'], 'GET')
        self.assertIsNone(sent['body'])

    def test_rejects_wrong_arguments(self):
        for argv in [['DELETE'], ['GET', 'x'], ['POST', 'a', 'b']]:
            with self.subTest(argv=argv), self.assertRaises(SystemExit):
                self.run_script(argv)

    def test_the_bodies_in_the_chapter_are_rejected_by_the_handler(self):
        handler_test = ApiExampleTest('test_valid_post_and_get')
        handler_test.setUp()
        for body in ['{"text": ', '{"text": "   "}', json.dumps({'text': 'あ' * 201}, ensure_ascii=False)]:
            self.assertEqual(handler_test.call('POST', body)['statusCode'], 400)
        self.assertEqual(handler_test.call('POST', '{"text": "学習用の架空のメモ"}')['statusCode'], 201)
        self.assertIn("printf 'あ%.0s' $(seq 201)", SOURCE.read_text())


if __name__ == '__main__':
    unittest.main()
