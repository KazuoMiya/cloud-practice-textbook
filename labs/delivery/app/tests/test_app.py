"""題材のアプリのテスト。make test で実行する。失敗したら、デプロイは行われない。"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app  # noqa: E402


def call(path, version=None):
    if version is None:
        os.environ.pop('APP_VERSION', None)
    else:
        os.environ['APP_VERSION'] = version
    result = {}

    def start_response(status, headers):
        result['status'] = status
        result['headers'] = dict(headers)

    body = b''.join(app.app({'PATH_INFO': path, 'REQUEST_METHOD': 'GET'}, start_response))
    return result['status'], result['headers'], body.decode('utf-8')


class AppTest(unittest.TestCase):
    def test_health(self):
        status, _, body = call('/health')
        self.assertEqual(status, '200 OK')
        self.assertEqual(body, 'ok')

    def test_top_page_shows_message_and_version(self):
        status, headers, body = call('/', version='abc1234')
        self.assertEqual(status, '200 OK')
        self.assertIn('text/html', headers['Content-Type'])
        self.assertIn(app.MESSAGE, body)
        self.assertIn('版：abc1234', body)

    def test_version_is_escaped(self):
        _, _, body = call('/', version='<script>')
        self.assertNotIn('<script>', body)

    def test_unknown_path(self):
        status, _, _ = call('/nothing')
        self.assertEqual(status, '404 Not Found')


if __name__ == '__main__':
    unittest.main()
