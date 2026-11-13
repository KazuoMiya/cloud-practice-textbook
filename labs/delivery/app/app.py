"""第19章の題材のアプリ。画面を1つと、ヘルスチェック用のパスを返すだけの、小さなWebアプリ。

外部のライブラリを使わず、Pythonの標準の仕組み（WSGI）だけで書いている。
本番では、gunicorn がこの app を呼び出す。
"""
import html
import os

# 合格基準4では、この文言を変えて push し、画面に反映されることを確かめる
MESSAGE = 'クラウド実践テキスト 第19章の題材のアプリです'


def app(environ, start_response):
    path = environ.get('PATH_INFO', '/')
    if path == '/health':
        return respond(start_response, '200 OK', 'text/plain; charset=utf-8', 'ok')
    if path == '/':
        version = os.environ.get('APP_VERSION', 'local')
        page = (
            '<!doctype html><html lang="ja"><meta charset="utf-8"><title>cloudbook app</title>'
            f'<h1>{html.escape(MESSAGE)}</h1><p>版：{html.escape(version)}</p></html>'
        )
        return respond(start_response, '200 OK', 'text/html; charset=utf-8', page)
    return respond(start_response, '404 Not Found', 'text/plain; charset=utf-8', 'not found')


def respond(start_response, status, content_type, text):
    body = text.encode('utf-8')
    start_response(status, [('Content-Type', content_type), ('Content-Length', str(len(body)))])
    return [body]
