# -*- coding: utf-8 -*-
"""포스터 첫 판 자동 생성 — 구도 유형(A~I)의 규격(types.json 중앙값)대로 우리 문구·사진을 깐다.
python -m ad pgrid layout D --title SIGN --sub "간판 구조 전시" --date 2026.11.12~11.30 --place "대전 수산나디자인" --photo a.jpg --out <폴더>
나오는 것: layout_<유형>.png(미리보기) · layout_<유형>.svg(일러스트레이터에서 글자 고치기 — «안내선» 묶음은 내보낼 때 끈다) · layout_<유형>_guide.png
🔴 첫 판이다. 글자 크기·자리는 레퍼런스 중앙값이라 그대로 두면 «평균»이 된다 — 사람이 다듬는 출발점으로 쓴다.
"""
import base64
import io
import json
import os
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', 'refs', '_모음', '포스터_그리드')
FD = os.path.join(HERE, '..', 'jobs', '2026-10_수산나포스터', 'fonts')
WF = r'C:\Windows\Fonts'
FONTS = {  # 종류: (파일, SVG 글꼴 이름, 굵기)
    'grot': (os.path.join(FD, 'Pretendard-Bold.otf'), 'Pretendard', 700),
    'grotm': (os.path.join(FD, 'Pretendard-SemiBold.otf'), 'Pretendard', 600),
    'grotr': (os.path.join(FD, 'Pretendard-Regular.otf'), 'Pretendard', 400),
    'cond': (os.path.join(WF, 'bahnschrift.ttf'), 'Bahnschrift Condensed', 700),
    'serif': (os.path.join(WF, 'georgiab.ttf'), 'Georgia', 700),
    'mono': (os.path.join(WF, 'consola.ttf'), 'Consolas', 400),
}
W, H = 1200, 1697
HANGUL = re.compile('[\uac00-\ud7a3]')


def _kind(kind, s):
    return 'grot' if HANGUL.search(s) and kind in ('cond', 'serif', 'mono') else kind


def _font(kind, size):
    f = ImageFont.truetype(FONTS[kind][0], max(6, int(size)))
    if kind == 'cond':
        try:
            f.set_variation_by_name('Bold Condensed')
        except Exception:
            pass
    return f


def _cap(kind, s):
    f = _font(kind, 200)
    smp = 'H' if not HANGUL.search(s) else '한'
    b = f.getbbox(smp)
    return (b[3] - b[1]) / 200


class Page:
    def __init__(self, bg=(250, 250, 248)):
        self.bg = bg
        self.im = Image.new('RGB', (W, H), bg)
        self.d = ImageDraw.Draw(self.im)
        self.svg = [f'<rect width="{W}" height="{H}" fill="{_hex(bg)}"/>']
        self.guides = []

    def X(self, p): return p * W / 100
    def Y(self, p): return p * H / 100

    def photo(self, box, path=None, tone=0):
        x0, y0, x1, y1 = [int(round(v)) for v in (self.X(box[0]), self.Y(box[1]), self.X(box[2]), self.Y(box[3]))]
        w, h = x1 - x0, y1 - y0
        if path and os.path.isfile(path):
            im = Image.open(path).convert('RGB')
            s = max(w / im.width, h / im.height)                          # 덮게 자르기(cover)
            im = im.resize((max(w, int(im.width * s + 1)), max(h, int(im.height * s + 1))), Image.LANCZOS)
            l, t = (im.width - w) // 2, (im.height - h) // 2
            im = im.crop((l, t, l + w, t + h))
        else:
            g = np.linspace(0, 1, h)[:, None] * np.ones((1, w))
            arr = (150 + tone + 55 * g).clip(0, 255).astype(np.uint8)
            im = Image.fromarray(np.stack([arr] * 3, -1))
            d = ImageDraw.Draw(im)
            d.line([(0, 0), (w, h)], fill=(235, 235, 235), width=2); d.line([(0, h), (w, 0)], fill=(235, 235, 235), width=2)
        self.im.paste(im, (x0, y0))
        buf = io.BytesIO(); im.save(buf, 'JPEG', quality=88)
        self.svg.append(f'<image x="{x0}" y="{y0}" width="{w}" height="{h}" href="data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"/>')

    def rect(self, box, fill, outline=None, width=2):
        x0, y0, x1, y1 = self.X(box[0]), self.Y(box[1]), self.X(box[2]), self.Y(box[3])
        self.d.rectangle([x0, y0, x1, y1], fill=fill, outline=outline, width=width)
        self.svg.append(f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="{_hex(fill) if fill else "none"}"'
                        + (f' stroke="{_hex(outline)}" stroke-width="{width}"' if outline else '') + '/>')

    def ellipse(self, box, outline, width):
        x0, y0, x1, y1 = self.X(box[0]), self.Y(box[1]), self.X(box[2]), self.Y(box[3])
        self.d.ellipse([x0, y0, x1, y1], outline=outline, width=width)
        self.svg.append(f'<ellipse cx="{(x0 + x1) / 2:.1f}" cy="{(y0 + y1) / 2:.1f}" rx="{(x1 - x0) / 2 - width / 2:.1f}" ry="{(y1 - y0) / 2 - width / 2:.1f}" fill="none" stroke="{_hex(outline)}" stroke-width="{width}"/>')

    def text(self, x, y, s, kind, cap_pct, fill=(20, 20, 20), align='l', rot=0, maxw=None, name=''):
        """x,y = 판 대비 % — 가로 글은 (왼쪽|가운데|오른쪽, 대문자 윗끝), 세로 글(rot=90)은 (왼쪽, 글줄 아랫끝)"""
        if not s:
            return None
        kind = _kind(kind, s)
        cr = _cap(kind, s)
        size = (cap_pct * H / 100) / cr
        f = _font(kind, size)
        tw = self.d.textlength(s, font=f)
        lim = (maxw * (H if rot else W) / 100) if maxw else None
        if lim and tw > lim:
            size *= lim / tw
            f = _font(kind, size)
            tw = self.d.textlength(s, font=f)
        capH = cr * size
        top_off = f.getbbox('H' if not HANGUL.search(s) else '한')[1]
        layer = Image.new('RGBA', (int(tw + 8), int(size * 1.5)), (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((4, -top_off), s, font=f, fill=fill)
        layer = layer.crop((0, 0, layer.width, int(capH * 1.35) + 2))
        px, py = self.X(x), self.Y(y)
        fam, wt = FONTS[kind][1], FONTS[kind][2]
        if rot:
            layer = layer.rotate(90, expand=True)
            self.im.paste(layer, (int(px), int(py - layer.height)), layer)
            bx, by = px + capH, py
            self.svg.append(f'<text x="{bx:.1f}" y="{by:.1f}" transform="rotate(-90 {bx:.1f} {by:.1f})" font-family="{fam}" font-weight="{wt}" font-size="{size:.1f}" fill="{_hex(fill)}">{_esc(s)}</text>')
            return {'w': layer.width, 'h': layer.height, 'cap': 100 * capH / H}
        if align == 'r':
            px -= tw
        elif align == 'c':
            px -= tw / 2
        self.im.paste(layer, (int(px - 4), int(py)), layer)
        anchor = {'l': 'start', 'r': 'end', 'c': 'middle'}[align]
        ax = self.X(x)
        self.svg.append(f'<text x="{ax:.1f}" y="{py + capH:.1f}" text-anchor="{anchor}" font-family="{fam}" font-weight="{wt}" font-size="{size:.1f}" fill="{_hex(fill)}">{_esc(s)}</text>')
        return {'w': tw, 'h': capH, 'cap': 100 * capH / H, 'x0': px}

    def save(self, out, key, margins):
        os.makedirs(out, exist_ok=True)
        base = os.path.join(out, f'layout_{key}')
        self.im.save(base + '.png')
        mL, mT, mR, mB = margins
        x0, y0, x1, y1 = self.X(mL), self.Y(mT), self.X(100 - mR), self.Y(100 - mB)
        g = ['<g id="안내선" opacity="0.6" style="display:inline">',
             f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{x1 - x0:.1f}" height="{y1 - y0:.1f}" fill="none" stroke="#3C9BD0" stroke-width="2"/>']
        gi = self.im.copy(); gd = ImageDraw.Draw(gi, 'RGBA')
        gd.rectangle([x0, y0, x1, y1], outline=(60, 155, 208, 230), width=2)
        cw = (x1 - x0) / 12
        for i in range(1, 12):
            gx = x0 + i * cw
            g.append(f'<line x1="{gx:.1f}" y1="0" x2="{gx:.1f}" y2="{H}" stroke="#3C9BD0" stroke-width="1"/>')
            gd.line([(gx, 0), (gx, H)], fill=(60, 155, 208, 90), width=1)
        for k in (1, 2):
            g.append(f'<line x1="0" y1="{H * k / 3:.1f}" x2="{W}" y2="{H * k / 3:.1f}" stroke="#999999" stroke-dasharray="8 8"/>')
            gd.line([(0, H * k / 3), (W, H * k / 3)], fill=(150, 150, 150, 140), width=1)
        g.append('</g>')
        gi.save(base + '_guide.png')
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n<g id="포스터">\n'
               + '\n'.join(self.svg) + '\n</g>\n' + '\n'.join(g) + '\n</svg>\n')
        open(base + '.svg', 'w', encoding='utf-8').write(svg)
        return base + '.png'


def _hex(c):
    return '#%02X%02X%02X' % tuple(c[:3]) if isinstance(c, tuple) else c


def _esc(s):
    return s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def _rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def _stat(T, key, k, default):
    try:
        return T[key]['stats'][k]['med']
    except KeyError:
        return default


def layout(key, c, out, root=ROOT):
    """c = {title, sub, date, place, info:[…], brand, photo, photo2, accent}"""
    T = json.load(open(os.path.join(root, 'types.json'), encoding='utf-8'))
    head = _stat(T, key, 'head', 8.0)
    acc = _rgb(c.get('accent') or '#141414')
    ttl, sub, date, place, brand = c.get('title', ''), c.get('sub', ''), c.get('date', ''), c.get('place', ''), c.get('brand', '')
    info = c.get('info') or []
    ph, ph2 = c.get('photo'), c.get('photo2')
    W_ = (245, 245, 243)
    if key == 'A':
        p = Page(); p.photo([0, 0, 100, 100], ph, -40)
        if ph2:
            p.photo([58, 30, 88, 60], ph2, 30)
        p.text(3.3, 66, ttl, 'grot', head, W_, rot=90, maxw=62)
        p.text(96.7, 92.4, sub or date, 'grotm', 1.6, W_, align='r')
        p.text(96.7, 95.2, (date + '  ' + place) if sub else place, 'grotr', 1.1, (225, 225, 225), align='r')
        p.text(3.3, 2.2, brand, 'grotm', 1.1, W_)
        m = (3.3, 3.5, 3.3, 3.5)
    elif key == 'B':
        p = Page(); p.photo([0, 0, 100, 100], ph, -25)
        r = p.text(3, 3, ttl, 'cond', head, W_, maxw=94)
        p.text(3, 3 + (r['cap'] if r else head) + 2.5, sub, 'grotm', 2.8, W_)
        p.text(3, 92, date, 'grot', 2.5, W_)
        p.text(97, 92, brand or place, 'grot', 2.5, W_, align='r')
        m = (3, 2.5, 3, 3)
    elif key == 'C':
        p = Page()
        r = p.text(2.1, 2.5, ttl, 'serif', head, (20, 20, 20), maxw=66)
        yy = 2.5 + (r['cap'] if r else head) + 2.2
        cols = [(date, ''), (place, info[0] if info else ''), (sub, brand)]
        for i, (a1, b1) in enumerate(cols):
            p.text(2.1 + i * 33, yy, a1, 'grot', 1.4)
            p.text(2.1 + i * 33, yy + 2.2, b1, 'grotr', 1.4)
        p.photo([0, yy + 6, 100, 100], ph, -10)
        m = (2.1, 1.7, 2.1, 1.7)
    elif key == 'D':
        p = Page(bg=(24, 24, 24)); p.photo([1.6, 2.1, 98.4, 62], ph, -20)
        r = p.text(1.6, 70, ttl, 'grot', head, (240, 240, 238), maxw=96.8)
        y2 = 70 + (r['cap'] if r else head) + 3
        p.text(1.6, y2, '  '.join(x for x in (sub, date, place) if x), 'grotm', 1.3, (220, 220, 220), maxw=96.8)
        p.text(1.6, y2 + 2.4, '  '.join(info), 'grotr', 1.3, (200, 200, 200), maxw=96.8)
        p.text(98.4, y2, brand, 'grotm', 1.3, acc if c.get('accent') else (220, 220, 220), align='r')
        m = (1.6, 2.1, 1.6, 2.1)
    elif key == 'E':
        p = Page()
        p.text(2, 5.5, ttl, 'cond', head, (150, 150, 150), maxw=96)
        p.photo([30, 24, 96, 90], ph, -30)
        p.text(4, 40, sub, 'grotm', 4.0, acc if c.get('accent') else (20, 20, 20), maxw=40)
        p.text(96, 92, date, 'grotr', 4.0, align='r')
        p.text(96, 96.2, place or brand, 'grot', 1.8, align='r')
        m = (2, 5.5, 2, 2)
    elif key == 'F':
        p = Page()
        r1 = p.text(2.2, 1.6, ttl, 'grot', head, maxw=95.6)
        c1 = r1['cap'] if r1 else head
        r2 = p.text(2.2, 1.6 + c1 + 1.6, sub, 'grot', c1 / max(_stat(T, 'F', 'step', 1.3), 1.0), (120, 120, 120), maxw=95.6)
        top = 1.6 + c1 + (r2['cap'] if r2 else 0) + 4
        p.photo([2.2, top, 97.8, top + 56], ph)
        y3 = top + 59
        p.text(2.2, y3, info[0] if info else place, 'grot', 2.5, maxw=95.6)
        for i, s in enumerate((date, place, brand)):
            p.rect([2.2 + i * 32.2, y3 + 5.5, 33.2 + i * 32.2, 98], None, (30, 30, 30), 2)
            p.text(3.6 + i * 32.2, y3 + 7, s, 'grotm', 1.3, maxw=29)
        m = (2.2, 1.6, 2.2, 2)
    elif key == 'G':
        p = Page(bg=(232, 232, 230))
        for i in range(14):
            if i % 3 != 1:
                p.rect([i * 7.6, 14 + (i % 4) * 6, i * 7.6 + 4.2, 60 + (i % 3) * 8], acc if c.get('accent') else (40, 40, 40))
        for cx, cy, rr in [(22, 70, 13), (70, 34, 9), (78, 80, 15)]:
            p.ellipse([cx - rr, cy - rr * 0.707, cx + rr, cy + rr * 0.707], (40, 40, 40), 34)
        p.rect([0, 0, 100, 10.5], (232, 232, 230)); p.rect([0, 89.5, 100, 100], (232, 232, 230))
        p.text(1.3, 3.1, ttl, 'grotr', head, maxw=97.4)
        p.text(1.3, 92, date, 'grotr', head, maxw=97.4)
        p.text(30, 47, sub or place, 'grotm', 3.2)
        m = (1.3, 3.1, 1.3, 3.1)
    elif key == 'H':
        p = Page(bg=(238, 235, 226))
        words = ttl.split() or [ttl]
        p.text(3.8, 1.5, words[0], 'grot', head, maxw=45)
        for i, w in enumerate(words[1:3]):
            p.text(96.2, 1.5 + i * (head + 2), w, 'grot', head, align='r', maxw=45)
        for i, s in enumerate([sub, date, place] + info[:3]):
            p.text(50, 66 + i * 3, s, 'mono', 1.4, align='c')
        p.text(3.8, 97, brand, 'grotr', 0.8)
        m = (3.8, 0.7, 3.8, 1.6)
    elif key == 'I':
        p = Page()
        panels = [[0, 0, 62, 32], [62, 0, 87, 32], [87, 0, 100, 32], [0, 32, 10, 65], [10, 32, 36, 65], [36, 32, 100, 65], [0, 65, 23, 100], [23, 65, 48, 100], [48, 65, 100, 100]]
        tones = [acc if c.get('accent') else (110, 110, 110), (238, 238, 238), (70, 70, 70), (160, 160, 160), (245, 245, 245), (205, 205, 205), (180, 180, 180), (245, 245, 245), (190, 190, 190)]
        for b_, t_ in zip(panels, tones):
            p.rect(b_, t_)
        if ph:
            p.photo([10, 32, 36, 65], ph)
        p.text(3, 3, ttl, 'grotr', 3.8, maxw=56)
        p.text(40, 36, sub, 'grotr', 3.8, maxw=56)
        p.text(54, 50, (date.split('.')[-1] if date else ''), 'grot', _stat(T, 'I', 'head', 11.6))
        p.text(55, 99, date, 'grotr', 3.8, rot=90, maxw=33)
        p.text(1.5, 68, place, 'grotr', 3.8, maxw=20)
        p.text(64, 30, brand, 'grotm', 1.5, rot=90, maxw=29)
        m = (0.8, 1.3, 1.8, 3.1)
    else:
        raise ValueError(f'유형 {key} 없음 (A~I)')
    return p.save(out, key, m)
