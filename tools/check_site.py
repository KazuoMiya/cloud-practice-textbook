"""Independent checks of generated HTML, assets and workflow pinning."""
from html.parser import HTMLParser
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


class SiteCheck(HTMLParser):
    def __init__(self):
        super().__init__()
        self.errors, self.ids, self.fragments, self.chapters = [], set(), [], []
        self.policy = ''
        self.resources = []
        self.route_keys = []

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            if attrs['id'] in self.ids:
                self.errors.append('duplicate id: ' + attrs['id'])
            self.ids.add(attrs['id'])
        if tag == 'meta' and attrs.get('http-equiv', '').lower() == 'content-security-policy':
            self.policy = attrs.get('content', '')
        if tag == 'style' or (tag == 'script' and not attrs.get('src')):
            self.errors.append('inline executable/style element: ' + tag)
        for name, value in attributes:
            if name.startswith('on') or name == 'style':
                self.errors.append('inline attribute: ' + name)
            if name in ('href', 'src') and value and re.match(r'\s*(?:javascript|vbscript):', value, re.I):
                self.errors.append('unsafe URL scheme')
        if tag == 'a':
            href = attrs.get('href', '')
            if href.startswith('#'):
                self.fragments.append(href[1:])
            if href.startswith(('http://', 'https://')) and 'noopener' not in attrs.get('rel', '').split():
                self.errors.append('external link lacks noopener')
        if tag in ('script', 'img', 'iframe', 'link'):
            url = attrs.get('src', attrs.get('href', ''))
            if url and not url.startswith('data:'):
                self.resources.append(url)
                if '://' in url or url.startswith('//'):
                    self.errors.append('third-party resource: ' + url)
                elif not (ROOT / 'dist' / url).is_file():
                    self.errors.append('missing resource: ' + url)
        if tag == 'html':
            self.route_keys = attrs.get('data-chapters', '').split()
        if tag == 'article' and 'ch' in attrs.get('class', '').split():
            self.chapters.append(attrs)


def check():
    site = (ROOT / 'dist/index.html').read_text(encoding='utf-8')
    parser = SiteCheck()
    parser.feed(site)
    errors = parser.errors
    for required in ["default-src 'none'", "script-src 'self'", "style-src 'self'", "base-uri 'none'", "object-src 'none'", "connect-src 'none'"]:
        if required not in parser.policy:
            errors.append('missing CSP directive: ' + required)
    if 'unsafe-' in parser.policy or '*' in parser.policy:
        errors.append('overly broad CSP')
    for fragment in parser.fragments:
        if fragment not in parser.ids:
            errors.append('broken internal link: ' + fragment)
    if len(parser.chapters) != 46:
        errors.append('expected 46 chapters')
    visible = [a['id'] for a in parser.chapters if 'hidden' not in a]
    if visible != ['guide']:
        errors.append('initial rendering must contain only the guide')
    ids = [a['id'] for a in parser.chapters]
    if parser.route_keys != ids:
        errors.append('data-chapters must list every chapter id in order')
    styles = ''.join((ROOT / 'dist' / url).read_text(encoding='utf-8') for url in parser.resources
                     if re.fullmatch(r'assets/style\.[0-9a-f]+\.css', url))
    for key in ids[1:]:
        if f'html[data-route="{key}"] article[id="{key}"][hidden]{{display:block!important}}' not in styles:
            errors.append('no pre-paint route rule for chapter: ' + key)
    if any(not re.fullmatch(r'[a-z0-9]+', key) for key in ids):
        errors.append('chapter ids must stay [a-z0-9]+ (they are written into selectors)')
    if 'fonts.googleapis.com' in site or 'fonts.gstatic.com' in site:
        errors.append('Google Fonts resource remains')
    if '「クラウド入門 キャッチアップ資料」と「AWS実践ガイド」の内容を見直してひとつにまとめ' in site:
        errors.append('removed introduction text remains')
    for path in [*ROOT.glob('.github/workflows/*.yml'), ROOT / 'book/19-s8.md']:
        source = path.read_text(encoding='utf-8')
        for action in re.findall(r'uses:\s*([^\s#]+)', source):
            if not re.fullmatch(r'[\w.-]+/[\w./-]+@[0-9a-f]{40}', action):
                errors.append(f'action is not SHA-pinned: {path.name}: {action}')
    workflow = (ROOT / '.github/workflows/deploy.yml').read_text(encoding='utf-8')
    if 'contents: write' in workflow or 'git push' in workflow:
        errors.append('publication has repository write access')
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(parser.chapters)} chapters; {len(parser.fragments)} internal links; '
          f'{len(parser.resources)} local assets; CSP, no inline code, pinned actions')


if __name__ == '__main__':
    check()
