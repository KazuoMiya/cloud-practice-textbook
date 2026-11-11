"""Tiny SVG figure DSL for the cloud textbook. Output is theme-aware via page CSS classes."""
import html

def esc(s):
    return html.escape(str(s), quote=True)

class Fig:
    def __init__(self, name, w, h, label):
        self.name, self.w, self.h, self.label = name, w, h, label
        self.el = []
        self.uses_arrow = False

    # ---- primitives -------------------------------------------------
    def rect(self, x, y, w, h, cls='fg-box', rx=8):
        self.el.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" class="{cls}"/>')
        return self

    def text(self, x, y, s, cls='fg-t', anchor='start', bold=False, size=None):
        c = cls + (' fg-b' if bold else '')
        st = f' font-size="{size}"' if size else ''
        self.el.append(f'<text x="{x}" y="{y}" text-anchor="{anchor}" class="{c}"{st}>{esc(s)}</text>')
        return self

    def box(self, x, y, w, h, label=None, sub=None, kind='box', bold=False, align='center', lines=None):
        """A labelled box. lines: extra body lines (list) drawn left-aligned under a bold name."""
        cls = {'box': 'fg-box', 'acc': 'fg-acc', 'zone': 'fg-zone', 'dash': 'fg-dash', 'soft': 'fg-soft',
               'lv1': 'fg-lv fg-lv1', 'lv2': 'fg-lv fg-lv2', 'lv3': 'fg-lv fg-lv3', 'lv4': 'fg-lv fg-lv4',
               'lv5': 'fg-lv fg-lv5', 'me': 'fg-me', 'them': 'fg-them'}[kind]
        self.rect(x, y, w, h, cls)
        if lines is not None:
            self.text(x + 14, y + 22, label, bold=True)
            for i, ln in enumerate(lines):
                self.text(x + 14, y + 42 + i * 17, ln, cls='fg-s')
            return self
        if label is None:
            return self
        cx = x + w / 2 if align == 'center' else x + 14
        anchor = 'middle' if align == 'center' else 'start'
        if sub:
            self.text(cx, y + h / 2 - 3, label, anchor=anchor, bold=bold)
            self.text(cx, y + h / 2 + 14, sub, cls='fg-m', anchor=anchor)
        else:
            self.text(cx, y + h / 2 + 4.5, label, anchor=anchor, bold=bold)
        return self

    def arrow(self, pts, dashed=False, label=None, lpos=None, anchor='start', head=True, both=False):
        self.uses_arrow = True
        d = 'M' + ' L'.join(f'{x} {y}' for x, y in pts)
        cls = 'fg-ar' + (' fg-ard' if dashed else '')
        m = f' marker-end="url(#ah-{self.name})"' if head else ''
        if both:
            m += f' marker-start="url(#ah-{self.name})"'
        self.el.append(f'<path d="{d}" class="{cls}"{m}/>')
        if label:
            lx, ly = lpos if lpos else (pts[0][0] + 8, (pts[0][1] + pts[1][1]) / 2 + 4)
            self.text(lx, ly, label, cls='fg-m', anchor=anchor)
        return self

    def line(self, x1, y1, x2, y2, cls='fg-rule'):
        self.el.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" class="{cls}"/>')
        return self

    def badge(self, cx, cy, n):
        self.el.append(f'<circle cx="{cx}" cy="{cy}" r="10" class="fg-badge"/>')
        self.text(cx, cy + 4, n, cls='fg-bt', anchor='middle', bold=True)
        return self

    def raw(self, s):
        self.el.append(s)
        return self

    # ---- output -----------------------------------------------------
    def svg(self):
        defs = ''
        if self.uses_arrow:
            defs = (f'<defs><marker id="ah-{self.name}" viewBox="0 0 10 10" refX="9" refY="5" '
                    f'markerWidth="6.5" markerHeight="6.5" orient="auto-start-reverse">'
                    f'<path d="M0 0L10 5L0 10z" class="fg-ah"/></marker></defs>')
        return (f'<svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{esc(self.label)}" '
                f'class="fig-svg">{defs}{"".join(self.el)}</svg>')
