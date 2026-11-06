"""원판 로고 — 구성 셋(그대로 · 지붕 가운데 · 지붕 가운데 크게) × 색 둘(크림 원판 · 빨강 원판)."""
import re, os, fitz, numpy as np
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.join(os.environ.get('DEGAJA_AGENT', os.path.join(os.path.expanduser('~'), 'DeGaJa_Agent')), 'users', os.environ.get('DEGAJA_USER', 'user'), 'domains', 'susanna', '시안', '2026-10_부대찌개')
OUT = os.path.join(BASE, 'circle')
s = open(os.path.join(BASE, r'final\Q3_도장격자\고객B_도장격자.svg'), encoding='utf-8').read()
G = dict(re.findall(r'<g id="([^"]+)">(.*?)</g>', s, re.S))
R, L, K = '#A8232A', '#F3E9D2', '#1E1E1E'
W = 5400; C = W / 2
ROOF_C = ((2184.5 + 4289.05) / 2, (308.15 + 1037.07) / 2)
LET_CX = (559.44 + 4008.9) / 2


def recol(gid, col): return re.sub(r'fill="#[0-9A-Fa-f]+"', f'fill="{col}"', G[gid])


def content(red, line, roof_dx=0.0, roof_dy=0.0, roof_k=1.0):
    rx, ry = ROOF_C
    rt = f'translate({rx + roof_dx:.1f},{ry + roof_dy:.1f}) scale({roof_k}) translate({-rx:.1f},{-ry:.1f})'
    return (recol('cauldron', red) + recol('letters', red) +
            f'<g transform="{rt}">' + recol('roof', red) + recol('line', line) + '</g>')


def mec_of(body, scale=0.2):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="4800" height="4800" viewBox="0 -400 4800 4800">'
           f'<rect y="-400" width="4800" height="4800" fill="#fff"/>' + re.sub(r'fill="#[0-9A-Fa-f]+"', 'fill="#000"', body) + '</svg>')
    p = fitz.open(stream=svg.encode(), filetype='svg')[0].get_pixmap(matrix=fitz.Matrix(scale, scale))
    a = np.frombuffer(p.samples, np.uint8).reshape(p.height, p.width, p.n)[..., 0]
    ys, xs = np.nonzero(a < 128); P = np.c_[xs, ys] / scale + [0, -400]
    P = P[::4]; c = P.mean(0)
    for k in range(4000):
        d = np.hypot(*(P - c).T); i = d.argmax(); c = c + (P[i] - c) / (k + 20)
    return c, np.hypot(*(P - c).T).max()


def disc_svg(body_fn, disc, red, line):
    body = body_fn(red, line)
    (cx, cy), r = mec_of(body)
    k = 2300 / r                                   # 그림 바깥원을 원판(2444)의 94% 로
    t = f'translate({C:.1f},{C:.1f}) scale({k:.4f}) translate({-cx:.1f},{-cy:.1f})'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{W}" viewBox="0 0 {W} {W}">'
            f'<circle cx="{C}" cy="{C}" r="2444" fill="{disc}"/><g transform="{t}">{body}</g></svg>')


COMP = [('그대로', lambda red, line: content(red, line)),
        ('지붕 가운데', lambda red, line: content(red, line, LET_CX - ROOF_C[0], -170)),
        ('지붕 가운데 크게', lambda red, line: content(red, line, LET_CX - ROOF_C[0], -300, 1.28))]
COLS = [('크림 원판', dict(disc=L, red=R, line=K)), ('빨강 원판', dict(disc=R, red=L, line=L))]


def raster(svg, px):
    d = fitz.open(stream=svg.encode('utf-8'), filetype='svg'); z = px / W
    p = d[0].get_pixmap(matrix=fitz.Matrix(z, z), alpha=True)
    return Image.frombytes('RGBA', (p.width, p.height), p.samples)


font = ImageFont.truetype(r'C:\Windows\Fonts\malgunbd.ttf', 40)
cell = 700
sheet = Image.new('RGB', (cell * 3 + 80, (cell + 80) * 2 + 20), 'white'); dr = ImageDraw.Draw(sheet)
for j, (cn, ck) in enumerate(COLS):
    for i, (n, fn) in enumerate(COMP):
        svg = disc_svg(fn, **ck)
        tag = f'{i+1}{"AB"[j]}'
        open(os.path.join(OUT, f'원판2_{tag}.svg'), 'w', encoding='utf-8').write(svg)
        im = raster(svg, 1600); im.save(os.path.join(OUT, f'원판2_{tag}.png'))
        x, y = 20 + i * (cell + 20), 20 + j * (cell + 80)
        dr.text((x + 10, y), f'{tag}  {n} · {cn}', fill='black', font=font)
        sm = im.resize((cell - 40, cell - 40)); sheet.paste(sm, (x + 20, y + 60), sm)
sheet.save(os.path.join(OUT, '고객B_원판_구성3x2.png')); print(sheet.size)
