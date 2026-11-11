#!/usr/bin/env python3
"""クラウド実践テキストのビルド。book/*.md + theme/ + 図（tools/figs.py）から、HTMLと同じサイト内のCSS・JavaScriptを作る。

    python tools/build.py             dist/index.html + dist/assets/（dist全体を公開）
    python tools/build.py --artifact  dist/artifact.html も出力（同じassets/を必要とする断片）
    python tools/build.py --strict    警告が1つでもあれば失敗にする（CI用）

Markdownの拡張:  :::kind タイトル ... :::   {{ch:key}}  {{ch:key|t}}  {{fig:name|caption}}  - [ ] チェックリスト
"""
import hashlib, html, pathlib, re, sys
import markdown

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
from manifest import BOOK, PARTS, chapters, secno  # noqa: E402
from figs import all_figs  # noqa: E402

CH = chapters()
BYKEY = {c['key']: c for c in CH}
FIGS = all_figs()
LABELS = {'goal': 'この章のゴール', 'note': '要点', 'warn': '注意', 'tip': '現場のコツ', 'pit': '落とし穴',
          'lab': 'わざと壊してみる', 'ref': '公式資料で確かめる', 'sum': 'この章のまとめ', 'req': '要件',
          'think': '考えどころ', 'dir': '構成の方向性', 'ex': '例'}
OPEN = re.compile(r'^:::(\w+)\s*(.*)$')
warnings = []


def chref(m):
    key, opt = m.group(1), m.group(2)
    c = BYKEY.get(key)
    if not c:
        warnings.append(f'unknown chapter ref: {key}')
        return '??'
    txt = c['label'] + (f'「{c["title"]}」' if opt == 't' else '')
    return f'<a class="xr" href="#{key}">{txt}</a>'


class Ctx:
    def __init__(self, c):
        self.c, self.no = c, secno(c['label'])
        self.fig = self.q = self.chk = 0
        self.stash = {}

    def md(self, text):
        text = re.sub(r'\{\{ch:(\w+)(?:\|(\w))?\}\}', chref, text)

        def fig(m):
            name, cap = m.group(1), m.group(2).strip()
            self.fig += 1
            tok = f'FIGTOKEN{len(self.stash)}X'
            svg = FIGS.get(name)
            if svg is None:
                warnings.append(f'{self.c["key"]}: unknown figure {name}')
                svg = ''
            self.stash[tok] = (f'<figure class="fig"><div class="fig-frame">{svg}</div>'
                               f'<figcaption><b>図 {self.no}-{self.fig}</b>{html.escape(cap)}</figcaption></figure>')
            return f'\n\n{tok}\n\n'
        text = re.sub(r'^\{\{fig:([\w-]+)\|(.*?)\}\}\s*$', fig, text, flags=re.M)
        out = markdown.Markdown(extensions=['tables', 'fenced_code', 'sane_lists', 'attr_list']).convert(text)
        for tok, h in self.stash.items():
            out = out.replace(f'<p>{tok}</p>', h)
        return out


def parse(lines, i=0, inside=None):
    nodes, buf, fence = [], [], False

    def flush():
        if any(s.strip() for s in buf):
            nodes.append(('md', buf[:]))
        buf.clear()
    while i < len(lines):
        ln = lines[i]
        if ln.startswith('```'):
            fence = not fence
        if not fence and ln.startswith(':::'):
            if ln.strip() == ':::':
                flush()
                return nodes, i + 1
            m = OPEN.match(ln)
            kind, title = m.group(1), m.group(2).strip()
            flush()
            if inside == 'q' and kind in ('a', 'hint'):
                nodes.append(('sw', kind))
                i += 1
                continue
            kids, i = parse(lines, i + 1, kind)
            nodes.append(('blk', kind, title, kids))
            continue
        buf.append(ln)
        i += 1
    flush()
    if inside:
        warnings.append(f'unclosed block :::{inside}')
    return nodes, i


def render(nodes, ctx):
    out = []
    for n in nodes:
        if n[0] == 'md':
            out.append(ctx.md('\n'.join(n[1])))
        elif n[0] == 'blk':
            _, kind, title, kids = n
            if kind == 'q':
                out.append(render_q(title, kids, ctx))
            elif kind in LABELS:
                t = LABELS[kind] + (f'：{html.escape(title)}' if title else '')
                out.append(f'<div class="box {kind}"><p class="bt">{t}</p>{render(kids, ctx)}</div>')
            else:
                warnings.append(f'{ctx.c["key"]}: unknown block {kind}')
    return '\n'.join(out)


def render_q(title, kids, ctx):
    ctx.q += 1
    kind, _, head = title.partition('|')
    if not _:
        kind, head = '', title
    parts, cur = {'body': [], 'hint': [], 'a': []}, 'body'
    for k in kids:
        if k[0] == 'sw':
            cur = k[1]
        else:
            parts[cur].append(k)
    h = [f'<section class="q"><header><span class="q-n">問 {ctx.no}-{ctx.q}</span>']
    if kind.strip():
        h.append(f'<span class="q-k">{html.escape(kind.strip())}</span>')
    if head.strip():
        h.append(f'<span class="q-h">{html.escape(head.strip())}</span>')
    h.append('</header>' + render(parts['body'], ctx))
    if parts['hint']:
        h.append(f'<details class="hint"><summary>ヒント</summary><div>{render(parts["hint"], ctx)}</div></details>')
    if parts['a']:
        h.append(f'<details class="ans"><summary>解答と解説</summary><div>{render(parts["a"], ctx)}</div></details>')
    else:
        warnings.append(f'{ctx.c["key"]}: question {ctx.q} has no answer')
    h.append('</section>')
    return ''.join(h)


def post(body, ctx):
    key, secs = ctx.c['key'], []

    def h2(m):
        secs.append(re.sub(r'<[^>]+>', '', m.group(1)))
        n = len(secs)
        return f'<h2 id="{key}-{n}"><span class="hn">{ctx.no}.{n}</span>{m.group(1)}</h2>'
    body = re.sub(r'<h2>(.*?)</h2>', h2, body)
    body = body.replace('<table>', '<div class="tbl"><table>').replace('</table>', '</table></div>')

    def chk(m):
        ctx.chk += 1
        return (f'<li class="ck"><label><input type="checkbox" data-ck="{key}-c{ctx.chk}">'
                f'<span>{m.group(1)}</span></label></li>')
    body = re.sub(r'<li>\[ \] (.*?)</li>', chk, body, flags=re.S)
    body = re.sub(r'<ul>(\s*<li class="ck">)', r'<ul class="chklist">\1', body)
    body = re.sub(r'<a href="(https?://[^"]+)"', r'<a href="\1" target="_blank" rel="noopener noreferrer"', body)
    return body, secs


def load_source(key):
    hits = sorted((ROOT / 'book').glob(f'*-{key}.md'))
    if not hits:
        return None
    return hits[0].read_text(encoding='utf-8')


def chapter_html(i, c):
    text = load_source(c['key'])
    if text is None:
        return None, 0
    ctx = Ctx(c)
    nodes, _ = parse(text.split('\n'))
    body, secs = post(render(nodes, ctx), ctx)
    key = c['key']
    route = [f'<b>レベル</b><i>→</i>{c["lvname"] or "共通"}']
    if c['mins']:
        route.append(f'<b>目安</b><i>→</i>{c["mins"]}分')
    if c['pre']:
        route.append('<b>前提</b><i>→</i>' + '・'.join(f'<a href="#{p}">{BYKEY[p]["label"]}</a>' for p in c['pre']))
    mini = ''
    if len(secs) >= 3:
        items = ''.join(f'<li><a href="#{key}-{n}"><span class="hn">{ctx.no}.{n}</span>{html.escape(s)}</a></li>'
                        for n, s in enumerate(secs, 1))
        mini = f'<details class="mini" open><summary>この章の節</summary><ol>{items}</ol></details>'
    head = (f'<header class="ch-head"><p class="eyebrow"><span class="chip">{c["part"]}</span>'
            f'<span>{c["pdesc"]}</span></p>'
            f'<h1><span class="cn">{c["label"]}</span>{html.escape(c["title"])}</h1>'
            f'<p class="route">{"　｜　".join(route)}</p>{mini}</header>')
    if key == 'guide':
        head = (f'<header class="ch-head cover"><p class="kicker">CLOUD PRACTICE TEXTBOOK ／ {BOOK["asof"]}版</p>'
                f'<h1>{BOOK["title"]}</h1><p class="sub">{BOOK["sub"]}</p>'
                '<p class="resume" id="resume" hidden></p></header>')
    hidden = '' if key == 'guide' else ' hidden'
    return (f'<article class="ch {c["lv"]}" id="{key}" data-label="{c["label"]}" data-title="{html.escape(c["title"])}"{hidden}>'
            f'{head}<div class="body">{body}</div>__FOOT_{key}__</article>'), len(re.sub(r'<[^>]+>', '', body))


def main():
    arts, done, total = [], [], 0
    for i, c in enumerate(CH):
        h, n = chapter_html(i, c)
        if h:
            arts.append((c, h))
            done.append(c['key'])
            total += n
    out = []
    for j, (c, h) in enumerate(arts):
        pn = ''
        if j > 0:
            p = arts[j - 1][0]
            pn += f'<a class="prev" href="#{p["key"]}"><small>← 前へ　{p["label"]}</small>{html.escape(p["title"])}</a>'
        else:
            pn += '<span></span>'
        if j < len(arts) - 1:
            n = arts[j + 1][0]
            pn += f'<a class="next" href="#{n["key"]}"><small>{n["label"]}　次へ →</small>{html.escape(n["title"])}</a>'
        foot = (f'<footer class="ch-foot"><button class="done" type="button" data-done="{c["key"]}" aria-pressed="false">'
                f'この章を読了にする</button><nav class="pn" aria-label="前後の章">{pn}</nav></footer>')
        out.append(h.replace(f'__FOOT_{c["key"]}__', foot))
    toc = []
    for pname, pdesc, lv, lvname, chs in PARTS:
        items = ''.join(
            f'<li><a href="#{k}" data-toc="{k}"><span class="n">{lab.replace("第", "").replace("章", "").replace("付録", "") or ""}</span>'
            f'<span>{html.escape(t)}</span><span class="ck" aria-hidden="true">✓</span></a></li>'
            for k, lab, t, _, _ in chs if k in done)
        if items:
            toc.append(f'<div class="toc-part {lv}"><p><i></i>{pname}</p><ol>{items}</ol></div>')
    assets = ROOT / 'dist' / 'assets'
    assets.mkdir(parents=True, exist_ok=True)

    def asset(name, text):
        stem, suffix = name.rsplit('.', 1)
        filename = f'{stem}.{hashlib.sha256(text.encode()).hexdigest()[:12]}.{suffix}'
        (assets / filename).write_text(text, encoding='utf-8')
        return 'assets/' + filename

    css = (':root{color-scheme:light;padding-top:env(safe-area-inset-top,0px);'
           'padding-bottom:env(safe-area-inset-bottom,0px)}\n'
           'body{margin:0}img{max-width:100%}[hidden]{display:none!important}\n'
           + (ROOT / 'theme' / 'style.css').read_text(encoding='utf-8'))
    css_asset = asset('style.css', css)
    state_asset = asset('state.js', (ROOT / 'theme' / 'state.js').read_text(encoding='utf-8'))
    init_asset = asset('init.js', (ROOT / 'theme' / 'init.js').read_text(encoding='utf-8'))
    app_asset = asset('app.js', (ROOT / 'theme' / 'app.js').read_text(encoding='utf-8'))
    noscript_asset = asset('noscript.css', 'article.ch[hidden]{display:block!important}\n'
                          '.search,.prog,.done,.themebtn,.bar{display:none!important}\n')

    def body(standalone):
        theme = ('<button class="themebtn" type="button" id="theme" aria-label="表示の切り替え">表示：端末に合わせる</button>'
                 if standalone else '')
        return f"""<div class="bar"><button type="button" id="menu" aria-controls="side" aria-expanded="false">目次</button><span id="bartitle">{BOOK["title"]}</span></div>
<div class="app">
<nav class="side" id="side" aria-label="目次">
<a class="brand" href="#guide">{BOOK["title"]}<small>{BOOK["sub"]}</small></a>
<div class="prog"><span id="progtxt">読了 0 / {len(arts)} 章</span><div class="prog-track"><progress class="prog-fill" id="progfill" max="{len(arts)}" value="0" aria-labelledby="progtxt"></progress></div></div>
<input class="search" id="search" type="search" placeholder="本文を検索（2文字以上）" aria-label="本文を検索" autocomplete="off">
<ul class="hits" id="hits" hidden></ul>
<div class="toc" id="toc">{"".join(toc)}</div>
{theme}
</nav>
<main class="main" id="main"><div class="col">
{"".join(out)}
</div></main>
</div>
<script src="{app_asset}" defer></script>
"""

    icon = ("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E"
            "%3Crect width='32' height='32' rx='7' fill='%232a63d4'/%3E"
            "%3Cpath d='M8 9h7a3 3 0 0 1 3 3v12a3 3 0 0 0-3-3H8zM24 9h-3a3 3 0 0 0-3 3v12a3 3 0 0 1 3-3h3z' fill='%23fff'/%3E%3C/svg%3E")
    site = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'none'; object-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="referrer" content="no-referrer">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{BOOK["title"]}</title>
<meta name="description" content="{BOOK["desc"]}">
<meta property="og:type" content="book">
<meta property="og:title" content="{BOOK["title"]}">
<meta property="og:description" content="{BOOK["desc"]}">
<meta name="theme-color" content="#f5f6f8" media="(prefers-color-scheme: light)">
<meta name="theme-color" content="#10141a" media="(prefers-color-scheme: dark)">
<link rel="icon" href="{icon}">
<script src="{state_asset}"></script>
<script src="{init_asset}"></script>
<link rel="stylesheet" href="{css_asset}">
<noscript><link rel="stylesheet" href="{noscript_asset}"></noscript>
</head>
<body>
{body(True)}</body>
</html>
"""
    (ROOT / 'dist').mkdir(exist_ok=True)
    (ROOT / 'dist' / 'index.html').write_text(site, encoding='utf-8')
    (ROOT / 'dist' / '.nojekyll').write_text('', encoding='utf-8')
    if '--artifact' in sys.argv:
        frag = (f'<title>{BOOK["title"]}</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n'
                f'<link rel="stylesheet" href="{css_asset}">\n<script src="{state_asset}"></script>\n{body(False)}')
        (ROOT / 'dist' / 'artifact.html').write_text(frag, encoding='utf-8')
    print(f'chapters {len(arts)}/{len(CH)}  text chars {total}  html bytes {len(site.encode("utf-8"))}')
    missing = [c['key'] for c in CH if c['key'] not in done]
    if missing:
        print('missing:', ' '.join(missing))
    for w in sorted(set(warnings)):
        print('WARN', w)
    if '--strict' in sys.argv and (missing or warnings):
        sys.exit(1)


if __name__ == '__main__':
    main()
